"""
Load generator for the LLM Noisy Neighbour demo.

Drives baseline (short, fast) and noisy (long, heavy) requests against a
vLLM OpenAI-compatible endpoint so Grafana can visualise the interference.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import httpx
from fastapi import FastAPI
from rich.console import Console

console = Console()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
MODEL = "meta-llama/Llama-3.2-3B-Instruct"

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

BASELINE_SYSTEM_PROMPT = (
    "You are a concise SRE triage assistant. When given an alert summary, "
    "reply with exactly three sections: Impact (one sentence), Root Cause "
    "hypothesis (one sentence), and Recommended Action (one sentence). Do not "
    "include pleasantries. Use bullet points. Keep your response under 60 words "
    "total. Focus on actionable information that an on-call engineer can use "
    "immediately during an incident."
)

BASELINE_USER_PROMPT = (
    "Alert: pod CrashLoopBackOff on checkout-service in us-west-2 prod cluster. "
    "OOMKilled 4 times in the last 10 minutes. Memory limit is 512Mi."
)

NOISY_SYSTEM_PROMPT = (
    "You are a senior infrastructure architect preparing a detailed technical "
    "report for the VP of Engineering. Your reports are thorough, data-driven, "
    "and include specific metrics, percentiles, and capacity projections. You "
    "always structure your analysis with numbered sections, sub-sections, and "
    "concrete recommendations with estimated effort and impact scores. Include "
    "references to industry benchmarks where applicable. When discussing costs, "
    "provide exact dollar estimates with assumptions stated. Format tables using "
    "markdown. Every recommendation must include a priority rating (P0-P3), an "
    "estimated implementation timeline, required team resources, risk assessment, "
    "and a rollback plan. Begin with an executive summary of no more than 200 "
    "words, then proceed to the detailed analysis. End with a quarterly roadmap "
    "table showing milestones, owners, and success metrics. Include a RACI "
    "matrix for cross-team dependencies."
)

NOISY_USER_PROMPT = (
    "Produce a comprehensive capacity planning report for our Kubernetes "
    "platform. We currently run 14 EKS clusters across 3 AWS regions serving "
    "280 microservices. Cluster CPU utilisation averages 62% with p99 at 89%. "
    "Memory utilisation averages 71% with p99 at 94%. We expect 40% traffic "
    "growth over the next two quarters. Our monthly compute spend is $847,000. "
    "Analyse bin-packing efficiency, right-sizing opportunities, spot instance "
    "adoption, Karpenter consolidation gains, and reserved instance coverage. "
    "Provide a migration plan from Cluster Autoscaler to Karpenter for all "
    "clusters including risk assessment and rollback procedures."
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    baseline_completed: int = 0
    noisy_completed: int = 0
    baseline_latency_sum: float = 0.0
    noisy_latency_sum: float = 0.0
    baseline_ttft_sum: float = 0.0
    noisy_ttft_sum: float = 0.0

stats = Stats()
baseline_tasks: list[asyncio.Task] = []
noisy_tasks: list[asyncio.Task] = []
_shutdown_event = asyncio.Event()


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

async def send_streaming_request(
    client: httpx.AsyncClient,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    label: str,
) -> tuple[float, float]:
    """Send a streaming chat completion and return (ttft, total_latency)."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "stream": True,
        "temperature": 0.7,
    }

    ttft = 0.0
    start = time.monotonic()
    first_token_seen = False
    token_count = 0

    async with client.stream(
        "POST",
        f"{VLLM_BASE_URL}/v1/chat/completions",
        json=payload,
        timeout=300.0,
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            chunk = line[len("data: "):]
            if chunk.strip() == "[DONE]":
                break
            if not first_token_seen:
                ttft = time.monotonic() - start
                first_token_seen = True
            token_count += 1

    total_latency = time.monotonic() - start
    console.print(
        f"  [{label}] tokens={token_count}  ttft={ttft:.3f}s  "
        f"total={total_latency:.3f}s",
        style="dim",
    )
    return ttft, total_latency


async def baseline_worker(worker_id: int) -> None:
    """Continuously sends short requests until cancelled."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                ttft, latency = await send_streaming_request(
                    client,
                    BASELINE_SYSTEM_PROMPT,
                    BASELINE_USER_PROMPT,
                    max_tokens=50,
                    label=f"baseline-{worker_id}",
                )
                stats.baseline_completed += 1
                stats.baseline_latency_sum += latency
                stats.baseline_ttft_sum += ttft
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                console.print(
                    f"  [baseline-{worker_id}] error: {exc}", style="bold red"
                )
            await asyncio.sleep(1.0)


async def noisy_worker(worker_id: int) -> None:
    """Continuously sends long, heavy requests until cancelled."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                ttft, latency = await send_streaming_request(
                    client,
                    NOISY_SYSTEM_PROMPT,
                    NOISY_USER_PROMPT,
                    max_tokens=3000,
                    label=f"noisy-{worker_id}",
                )
                stats.noisy_completed += 1
                stats.noisy_latency_sum += latency
                stats.noisy_ttft_sum += ttft
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                console.print(
                    f"  [noisy-{worker_id}] error: {exc}", style="bold red"
                )
            await asyncio.sleep(1.0)


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    console.print("[bold green]Load generator ready[/bold green]")
    console.print(f"  vLLM endpoint: {VLLM_BASE_URL}")
    console.print(f"  Model: {MODEL}")
    yield
    # Cleanup on shutdown
    await _cancel_tasks(baseline_tasks)
    await _cancel_tasks(noisy_tasks)
    console.print("[bold red]Load generator shut down[/bold red]")


app = FastAPI(
    title="Noisy Neighbour Load Generator",
    lifespan=lifespan,
)


async def _cancel_tasks(task_list: list[asyncio.Task]) -> None:
    for task in task_list:
        task.cancel()
    await asyncio.gather(*task_list, return_exceptions=True)
    task_list.clear()


@app.post("/baseline")
async def start_baseline():
    """Start 5 baseline workers sending short, fast requests."""
    if baseline_tasks:
        return {"status": "baseline_already_running", "workers": len(baseline_tasks)}
    for i in range(5):
        task = asyncio.create_task(baseline_worker(i))
        baseline_tasks.append(task)
    console.print("[bold blue]>>> Baseline started: 5 workers[/bold blue]")
    return {"status": "baseline_started", "workers": 5}


@app.post("/noisy")
async def start_noisy():
    """Start 3 noisy-neighbour workers sending long, heavy requests."""
    if noisy_tasks:
        return {"status": "noisy_already_running", "workers": len(noisy_tasks)}
    for i in range(3):
        task = asyncio.create_task(noisy_worker(i))
        noisy_tasks.append(task)
    console.print("[bold magenta]>>> Noisy neighbours started: 3 workers[/bold magenta]")
    return {"status": "noisy_started", "workers": 3}


@app.post("/stop")
async def stop_all():
    """Gracefully stop all workers."""
    await _cancel_tasks(baseline_tasks)
    await _cancel_tasks(noisy_tasks)
    console.print("[bold red]>>> All workers stopped[/bold red]")
    return {"status": "stopped"}


@app.get("/status")
async def get_status():
    """Return current state of the load generator."""
    baseline_avg_latency = (
        stats.baseline_latency_sum / stats.baseline_completed
        if stats.baseline_completed > 0
        else 0.0
    )
    noisy_avg_latency = (
        stats.noisy_latency_sum / stats.noisy_completed
        if stats.noisy_completed > 0
        else 0.0
    )
    baseline_avg_ttft = (
        stats.baseline_ttft_sum / stats.baseline_completed
        if stats.baseline_completed > 0
        else 0.0
    )
    noisy_avg_ttft = (
        stats.noisy_ttft_sum / stats.noisy_completed
        if stats.noisy_completed > 0
        else 0.0
    )
    return {
        "baseline_workers_running": len(baseline_tasks),
        "noisy_workers_running": len(noisy_tasks),
        "baseline_requests_completed": stats.baseline_completed,
        "noisy_requests_completed": stats.noisy_completed,
        "baseline_avg_latency_s": round(baseline_avg_latency, 3),
        "noisy_avg_latency_s": round(noisy_avg_latency, 3),
        "baseline_avg_ttft_s": round(baseline_avg_ttft, 3),
        "noisy_avg_ttft_s": round(noisy_avg_ttft, 3),
    }
