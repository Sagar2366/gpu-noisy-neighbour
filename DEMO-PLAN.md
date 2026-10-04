# Demo Plan — vLLM Noisy Neighbour Observatory

## Overview

Three pre-recorded demo phases (~8 minutes of talk time, slides 7–10) using **vLLM** serving Llama 3.2 3B on a single GPU, instrumented with **DCGM Exporter**, **Prometheus**, and **Grafana**. All pre-recorded before the conference.

**Story:** "Here's a healthy LLM inference stack. I inject three long-output requests alongside short ones. Watch the metrics shift — then I'll show you how to pin the cause."

**Demo Style:** Pre-recorded asciinema terminal + Grafana dashboard screenshots, embedded in slides.

---

## Pre-Recording Infrastructure

Two options — use whichever fits your setup:

| Option | Path | When to use |
|--------|------|-------------|
| **Kubernetes (recommended)** | `demo/kubernetes/` | You have a GPU K8s cluster with Prometheus + DCGM already running |
| **Docker Compose** | `demo/docker-compose.yml` | Standalone GPU machine, no K8s needed |

The Kubernetes path is more realistic for the audience and reuses your existing monitoring stack (Prometheus, Grafana, DCGM Exporter DaemonSet). See `demo/kubernetes/README.md` for setup.

---

## Pre-Flight Checklist (Recording Day)

### If using Kubernetes:
- [ ] `kubectl` configured for the GPU cluster
- [ ] DCGM Exporter DaemonSet running on GPU nodes
- [ ] Prometheus (kube-prometheus-stack) scraping ServiceMonitors
- [ ] Grafana accessible via port-forward or ingress
- [ ] HuggingFace token exported as `HF_TOKEN`
- [ ] `demo/kubernetes/` manifests applied and vllm pod is Ready
- [ ] Load generator built and deployed (`docker build` + `kubectl apply`)
- [ ] Grafana dashboard imported (auto via sidecar or manual import)

### If using Docker Compose:
- [ ] GPU machine accessible (SSH or local)
- [ ] Docker & Docker Compose v2 installed
- [ ] nvidia-container-toolkit installed and working (`docker run --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi`)
- [ ] HuggingFace token set in `.env` (for gated Llama model)

### Both:
- [ ] `asciinema` installed for terminal recording
- [ ] OBS Studio or QuickTime for screen recording Grafana
- [ ] Full demo flow tested end-to-end (all 3 phases)
- [ ] Grafana dark theme enabled (Settings → Preferences → Theme: Dark)
- [ ] `asciinema` installed for terminal recording
- [ ] OBS Studio or QuickTime for screen recording Grafana
- [ ] Full demo flow tested end-to-end (all 3 phases)
- [ ] Grafana dark theme enabled (Settings → Preferences → Theme: Dark)
- [ ] Grafana dashboard auto-loaded and visible at `http://localhost:3000`
- [ ] Browser zoom set so all 6 panels are visible without scrolling
- [ ] Terminal font size large enough for conference projector (18pt+)

---

## Demo Setup

### Option A: Kubernetes (recommended)

```bash
cd observability-summit-2026/demo/kubernetes

# Create namespace + secret
export HF_TOKEN="hf_your_token_here"
envsubst < 00-namespace.yaml | kubectl apply -f -

# Deploy vLLM
kubectl apply -f 01-vllm.yaml

# Wait for model load (~3-5 min)
kubectl -n llm-demo wait --for=condition=ready pod -l app=vllm --timeout=600s

# Build and deploy load generator
docker build -t load-generator:latest ../load-generator/
# Push to your registry or kind load docker-image load-generator:latest
kubectl apply -f 02-load-generator.yaml

# Import Grafana dashboard
kubectl apply -f 03-grafana-dashboard-cm.yaml

# Port-forward
kubectl -n llm-demo port-forward svc/load-generator 8080:8080 &
kubectl -n llm-demo port-forward svc/vllm 8000:8000 &
```

### Option B: Docker Compose

```bash
cd observability-summit-2026/demo

# Set HuggingFace token
cp .env.example .env
# Edit .env → set HF_TOKEN

# Start the stack
docker compose up -d

# Wait for vLLM to load the model (~2-3 minutes)
docker compose logs -f vllm | grep "Uvicorn running"

# Verify all services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10

# Verify metrics are flowing
curl -s http://localhost:8000/metrics | grep vllm | head -5
curl -s http://localhost:9400/metrics | grep DCGM | head -5

# Open Grafana
open http://localhost:3000
# Login: admin / demo
# Dashboard: "LLM Inference: Noisy Neighbour Observatory"
```

---

## Recording Session

### Recording 1: Terminal (asciinema)

```bash
# Start recording
asciinema rec noisy-neighbour-demo.cast --title "Noisy Neighbour Demo"
```

Run the three phases inside the recording (see below). Stop recording with `exit` or Ctrl+D.

### Recording 2: Grafana (screen capture)

Start OBS Studio or QuickTime screen recording focused on the Grafana browser tab. Run the three phases while recording. You'll edit the video later to extract the key moments.

### Alternative: Screenshots

If video feels risky, take a Grafana screenshot at each phase instead:
1. Baseline steady-state (after 60s of load)
2. Peak noisy-neighbour impact (30-60s after injection)
3. Recovery (60s after stopping noisy requests)

---

## Phase 1: Healthy Baseline (Slide 8, ~2 min talk time)

### The Story
> "Five short requests, healthy metrics. This is what good looks like."

### Commands

```bash
# Start baseline load: 5 short requests
curl -s -X POST http://localhost:8080/baseline | jq .
```

### Expected terminal output
```json
{
  "status": "baseline_started",
  "workers": 5,
  "config": {
    "prompt_tokens": "~100",
    "max_output_tokens": 50
  }
}
```

### Wait and observe
```bash
# Wait 60 seconds for metrics to stabilize
sleep 60

# Check status
curl -s http://localhost:8080/status | jq .
```

### Expected Grafana state
| Panel | Value | Visual |
|-------|-------|--------|
| TTFT p99 | ~80ms | Flat line, low |
| ITL p99 | ~14ms | Flat line, low |
| KV Cache | ~18% | Flat, green zone |
| Batch Size | ~5 | Flat |
| Tensor Core | ~38% | Moderate |
| Queue Depth | 0 | Zero line |

### 📸 Screenshot: "Healthy Baseline"

### Talking points
> "TTFT 82ms, ITL 14ms, KV cache 18%, batch size 5, tensor cores 38%, queue zero. Everything flat, everything healthy. Remember these numbers."

---

## Phase 2: Inject Noisy Neighbours (Slide 9, ~2.5 min talk time)

### The Story
> "Three long requests join the batch. Watch every metric shift."

### Commands

```bash
# Inject 3 noisy neighbours (keep baseline running)
curl -s -X POST http://localhost:8080/noisy | jq .
```

### Expected terminal output
```json
{
  "status": "noisy_started",
  "workers": 3,
  "config": {
    "prompt_tokens": "~500",
    "max_output_tokens": 3000
  }
}
```

### Wait and observe
```bash
# Wait 60-90 seconds for full impact
sleep 90

# Check status — note the latency increase for short requests
curl -s http://localhost:8080/status | jq .
```

### Expected Grafana state
| Panel | Before | After | Change |
|-------|--------|-------|--------|
| TTFT p99 | ~80ms | ~420ms | 5× ▲ |
| ITL p99 | ~14ms | ~43ms | 3× ▲ |
| KV Cache | ~18% | ~87% | 4.8× ▲ |
| Batch Size | ~5 | ~8 | +3 |
| Tensor Core | ~38% | ~74% | 2× ▲ |
| Queue Depth | 0 | 0 | No change! |

### 📸 Screenshot: "Noisy Neighbour Impact"

### Talking points
> "TTFT 5× spike. ITL 3× spike. KV cache rockets to 87%. Batch size goes to 8. Tensor cores at 74% — GPU is busy. And queue depth? Still zero. The problem isn't queueing. It's what happens inside the batch."

---

## Phase 3: Pin the Cause (Slide 10, ~2.5 min talk time)

### The Story
> "The correlation chain: more batch-mates → more KV pressure → preemptions → ITL spikes. It's not the queue. It's the batch."

### Commands (no new commands — same Grafana view, different narrative)

```bash
# Show the status with detailed per-request metrics
curl -s http://localhost:8080/status | jq '.request_stats'
```

### Key correlations to highlight in Grafana
1. **KV Cache ↔ ITL**: Overlay the two panels. KV cache spike at T+10s → ITL spike at T+12s. The lag is the preemption.
2. **Batch Size ↔ ITL**: Batch goes from 5 to 8 → each iteration takes longer.
3. **Tensor Core ↔ Queue**: Tensor cores HIGH + Queue ZERO = the GPU is busy serving someone else, not waiting for work.

### 📸 Screenshot: "Correlation View" (zoom into the transition moment)

### Talking points
> "The correlation: batch size 5→8, KV cache 18→87%, ITL 14→43ms. GPU utilization 74%. Queue zero. Your dashboard says 'add more GPUs.' The real answer: 'cap batch size and route by output length.' You don't need more GPUs. You need fewer neighbours."

### Recovery (optional, for recording completeness)

```bash
# Stop all load
curl -s -X POST http://localhost:8080/stop | jq .

# Wait 30s, show metrics returning to baseline
sleep 30
```

### 📸 Screenshot: "Recovery" (metrics dropping back)

---

## Fallback Plan

| Priority | If... | Do... |
|----------|-------|-------|
| 1 | Video doesn't play | Show Grafana screenshots embedded in backup slides |
| 2 | Screenshots unclear | Walk through PromQL on a terminal-style slide |
| 3 | Everything fails | Use the ASCII diagrams in slides 8-10 + tell the story verbally |

---

## Demo Script Aliases

```bash
#!/bin/bash
# Source this before recording: source demo-aliases.sh

alias demo-baseline='curl -s -X POST http://localhost:8080/baseline | jq .'
alias demo-noisy='curl -s -X POST http://localhost:8080/noisy | jq .'
alias demo-stop='curl -s -X POST http://localhost:8080/stop | jq .'
alias demo-status='curl -s http://localhost:8080/status | jq .'
alias demo-metrics-vllm='curl -s http://localhost:8000/metrics | grep -E "vllm:(time_to_first|inter_token|kv_cache|num_requests)" | head -20'
alias demo-metrics-dcgm='curl -s http://localhost:9400/metrics | grep DCGM_FI_PROF_PIPE_TENSOR | head -5'

# Full sequence
alias demo-full='echo "Phase 1: Baseline" && demo-baseline && sleep 60 && echo "Phase 2: Noisy" && demo-noisy && sleep 90 && echo "Phase 3: Recovery" && demo-stop'
```

---

## Timing Checkpoints (During Talk)

| Checkpoint | Target | If Behind |
|-----------|--------|-----------|
| Stack intro done (slide 7) | 9:00 | Skip architecture details, jump to demo |
| Phase 1 shown (slide 8) | 11:00 | Show screenshot only, skip terminal |
| Phase 2 shown (slide 9) | 13:30 | Skip per-metric narration, show before/after table |
| Phase 3 + cause pinned (slide 10) | 16:00 | If >17:00, cut slide 13 (mitigations) to 3 bullets |
| PromQL slide done (slide 11) | 18:00 | Read 3 of 6 queries, say "the other 3 are in the slides" |
| Closing slide | 23:00 | If >23:30, skip Monday checklist, go straight to closing line |

---

## Post-Recording Checklist

- [ ] Terminal recording plays correctly: `asciinema play noisy-neighbour-demo.cast`
- [ ] Terminal recording uploaded: `asciinema upload noisy-neighbour-demo.cast`
- [ ] Grafana screenshots are high-res (2× or Retina)
- [ ] Screenshots cropped to show only the dashboard (no browser chrome)
- [ ] All 3 phases have both terminal and Grafana captures
- [ ] Video edited to remove dead time (waiting for model load, etc.)
- [ ] Backup slides created with screenshots embedded
- [ ] All materials tested on the presentation laptop
