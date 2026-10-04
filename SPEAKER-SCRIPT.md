# Speaker Script — The Noisy Neighbour Inside Your GPU

> **Duration:** 23 min content + 2 min Q&A = 25 min
> **Style:** Conversational, first-person, data-driven. "Your dashboard says X, the truth is Y."
> **Recurring device:** Mystery → reveal. Show the misleading signal, then show what's really happening.

---

## [0:00] SLIDE 1 — Title

Hey everyone. I'm Sagar Utekar — Senior SRE at CrowdStrike, CNCF Ambassador, and Kubestronaut.

"Noisy neighbour" — it's an SRE term most of you know. A container stealing CPU from the pod next door. A VM thrashing the disk on a shared host. We've been dealing with it for years, and we've gotten pretty good at it. Cgroups, resource limits, node affinity — solved problems.

But there's a new kind of noisy neighbour, and it lives somewhere your cgroups can't reach. It's sitting on the same GPU as your request. In the same batch. On the same decode iteration. And your traces — your beautiful distributed traces — can't see it.

Today I'm going to show you how to find it. Let's go.

---

## [0:30] SLIDE 2 — Your p99 Is Lying to You

Here's a scenario. Your LLM inference service — let's say you're running vLLM in production, serving an internal chatbot. Your p99 latency spikes 8×. Dashboard goes red. PagerDuty fires.

You open your traces. You find the request that hit p99. You look at it. 47 tokens generated. Simple prompt — "summarize this Jira ticket." Nothing weird. 190 milliseconds of actual compute. So why did it take 1.8 seconds?

The answer isn't in your trace. The request that caused this spike was in a completely different user's session. It was generating a 4,000-token detailed report. And it was sitting in the same batch on the same GPU as your 47-token summarization.

That long request held onto KV cache blocks for thousands of iterations. It made every decode step slower for every other request in the batch. And when it finished — 30 seconds before your request even started — the damage was already done. The KV cache was fragmented. Your request got preempted twice.

Your per-request trace shows none of this. It can't. The trace only sees one request. The problem was the batch.

---

## [1:30] SLIDE 3 — The Neighbour You Can't See

To understand why, you need to understand how modern LLM servers work. And I promise this won't be a computer science lecture — just enough to know where to look.

Old-school inference used static batching. You collect 8 requests, pad them all to the same length, run them as a batch, and return the results. The problem? If request A generates 4,000 tokens and request C generates 50, request C sits there doing nothing for 3,950 iterations. Terrible GPU utilization.

vLLM, TGI, TensorRT-LLM — they all use continuous batching. The batch reshuffles every single iteration. A new request doesn't wait for the batch to finish — it jumps in on the next decode step. When a request finishes, it leaves immediately and frees its slot.

This is brilliant for throughput. But it means something fundamentally different for observability. Your request is now fused onto the GPU alongside strangers'. Every decode step — and there are hundreds per second — your request shares GPU cycles with every other request currently running. The neighbour sitting next to you on the GPU? You have no idea who they are, how many tokens they're generating, or how much KV cache they're hogging. And neither does your trace.

---

## [4:00] SLIDE 4 — Your RED Dashboard Is Wrong

So let's talk about what your dashboard actually shows you. Rate, errors, duration — the RED method. The holy trinity of service monitoring.

You look at your LLM inference service. Rate: 142 requests per second. Normal. Errors: 0.2%. Normal. Duration: p50 is 210 milliseconds. Normal. P99 is 1.8 seconds. That's an 8× spike.

The obvious conclusion? "We have slow requests." Maybe the model is overloaded. Maybe we need to scale up.

Here's the truth. That p99 request — the 1.8-second one — generated 47 tokens. Its actual compute was 190 milliseconds. The other 1.6 seconds? Waiting. The KV cache was 94% full. The batch had 28 active requests. Three of those batch-mates were generating 3,000+ tokens each. Their KV blocks were eating all the memory. Our request's KV blocks got preempted — evicted to make room — twice. Each preemption means recomputing those blocks from scratch.

The request was fine. The batch was noisy. And RED — rate, errors, duration — can't tell you that. It gives you the symptom. Not the cause.

---

## [5:30] SLIDE 5 — The Two Latencies That Matter

Here's the mental model that changes everything. There are two latencies in LLM inference, and you need to track them separately.

Time-to-first-token — TTFT. This is how long from when the request arrives until the first token comes back to the user. It's queue time — how long you waited to get scheduled — plus prefill time — how long it took to process your prompt. TTFT is what the user feels as "responsiveness." A high TTFT means "I clicked send and nothing happened for 2 seconds."

Inter-token latency — ITL. This is the gap between each subsequent token. Once you start streaming, this is how fast the tokens flow. ITL is what the user feels as "speed." A high ITL means "the response is typing... really... slowly..."

Here's the key insight. The noisy neighbour mostly inflates ITL, not TTFT. Why? Because every decode iteration, your request shares GPU cycles with every other request in the batch. More requests in the batch, more attention heads to compute, longer each iteration takes. Your total latency is TTFT plus ITL times the number of output tokens. A 3× ITL spike on a 50-token response? That's 50 times the extra 30 milliseconds. That's 1.5 seconds of phantom latency that doesn't show up anywhere in a per-request trace as a single identifiable bottleneck.

If your ITL spikes while your TTFT stays stable — you have a batch problem. That's the signal.

---

## [7:00] SLIDE 6 — Inside a vLLM Scheduler Step

Let me make this concrete. Here's what happens inside vLLM every single iteration. This runs hundreds of times per second.

Step one: check the queue. Are new requests waiting? If yes, schedule them for prefill on the next pass.

Step two: allocate KV cache. Every active request needs memory for its key-value pairs — that's the "memory" of the attention mechanism. vLLM uses PagedAttention, which allocates memory in blocks, like virtual memory pages. In our example, 3,153 blocks used, 847 free — that's 79% full.

Step three — and this is where it gets interesting — preempt if needed. If the KV cache is full and a new request needs to prefill, vLLM evicts the lowest-priority request's KV blocks. That request will have to recompute them later. Preemptions are expensive and invisible in per-request traces.

Step four: run the forward pass on the GPU. All 24 requests in this batch — every single one — shares the GPU for this one forward pass. This is where the noisy neighbour lives. The more requests in the batch, the larger the attention matrix, the longer the forward pass takes.

Step five: return one token per request. Some requests finish — they got their stop token — and leave the batch. Others continue to the next iteration. And the whole thing repeats.

The batch reshuffles every iteration. This is fundamentally different from a container sharing a CPU. There's no cgroup for GPU batch scheduling.

---

## [8:00] SLIDE 7 — The Observability Stack

OK, enough theory. Let me show you the stack. It's four components, all open-source.

vLLM exposes a /metrics endpoint with everything we need. Time-to-first-token, inter-token latency, KV cache usage percentage, number of requests running — that's your batch size — queue depth, prefill time, decode time. All as Prometheus metrics. You don't need to instrument anything. Just expose the port.

DCGM Exporter — that's NVIDIA's Data Center GPU Manager — gives us the GPU-level view. Tensor core activity tells you whether the GPU is actually computing or waiting on memory. Framebuffer usage tells you how much GPU memory is consumed. Temperature and power tell you if you're thermal throttling.

Prometheus scrapes both every 15 seconds. Grafana gives us the dashboard. Six panels. TTFT p99, ITL p99, KV cache usage, batch occupancy, tensor core activity, queue depth. That's the entire observability surface. No agents, no vendor lock-in. Let me show you what this looks like in practice.

---

## [9:00] SLIDE 8 — Demo Phase 1: Healthy Baseline

I pre-recorded this on a cloud GPU instance running vLLM with Llama 3.2 3B. Let me walk you through it.

Phase one: the baseline. Five concurrent short requests. Each one sends a 100-token system prompt — think "you are an SRE assistant" — and asks for about 50 tokens of output. Simple summarizations, quick answers.

Look at the Grafana dashboard. TTFT p99: 82 milliseconds. ITL p99: 14 milliseconds. KV cache at 18% — plenty of room. Batch size of 5 — just our five requests. Tensor core activity at 38% — the GPU is cruising. Queue depth: zero. Nobody's waiting. 

Everything is flat. Everything is healthy. Remember these numbers. I'm about to ruin them.

---

## [11:00] SLIDE 9 — Demo Phase 2: Inject the Noisy Neighbour

Phase two. I inject three noisy neighbours. Same vLLM instance, same GPU. These are requests with a 500-token system prompt — a detailed context about an infrastructure environment — and they ask the model to generate a comprehensive 3,000-token analysis.

The five short requests are still running. Same prompts, same max tokens, same everything. The only thing that changed is who else is in the batch.

Watch the Grafana panels. TTFT goes from 82 to 420 milliseconds. That's a 5× spike. ITL goes from 14 to 43 milliseconds. 3× spike. KV cache rockets from 18% to 87%. The three noisy neighbours are holding onto enormous KV blocks — each one needs memory for 3,500 tokens of context.

Batch size goes from 5 to 8. And tensor core activity jumps to 74%. The GPU is working harder — much harder.

But here's the critical one: look at queue depth. Still zero. No requests are waiting in the queue. Everyone got scheduled immediately. The problem isn't queueing. It's not a capacity problem in the traditional sense. The problem is what happens after you're in the batch. Eight requests sharing one GPU, three of them generating thousands of tokens, all of them competing for KV cache and GPU cycles every single iteration.

The short requests — the exact same requests that were completing in 210 milliseconds — now take 482 milliseconds. 2.3× slower. They're generating the same number of tokens. The model isn't slower. The neighbours are just... noisy.

---

## [13:30] SLIDE 10 — Demo Phase 3: Pin the Cause

Let me connect the dots, because this is the diagnosis your dashboard won't give you.

Three long requests join the batch. Batch size goes from 5 to 8. That means more work per forward pass — the GPU has to compute attention for all 8 requests on every iteration. Each iteration takes longer. That's the ITL spike.

KV cache fills from 18% to 87%. Those long requests hold onto their KV blocks for thousands of iterations — they're generating 3,000 tokens, and each token adds a key-value pair. When it gets tight, vLLM starts preempting — evicting shorter requests' KV blocks to make room for the long ones. Those short requests have to recompute their KV blocks next time they're scheduled. That's wasted GPU cycles.

And the GPU metrics confirm it. Tensor core activity at 74%. The GPU isn't idle. It's not waiting on I/O. It's doing compute — but it's doing compute for the noisy neighbours.

Now here's what your traditional dashboard tells you. GPU utilization 74%, p99 latency doubled. The obvious conclusion: "We need more GPUs." The real answer: you don't need more GPUs. You need fewer neighbours. Cap your batch size. Route long-generation requests to a separate pool. The problem isn't capacity. The problem is contention.

---

## [16:00] SLIDE 11 — Six Queries for Your Dashboard

Six PromQL queries. Put these on your dashboard tomorrow. I'll go through them quickly.

Number one — TTFT p99. histogram_quantile 0.99 on `vllm:time_to_first_token_seconds`. This is your user-facing responsiveness metric. If this is high, users are staring at a blank screen.

Number two — ITL p99. Same pattern, but on `vllm:inter_token_latency_seconds`. This is the noisy-neighbour signal. If ITL spikes while TTFT stays stable, you have a batch problem. Full stop.

Number three — KV cache usage percentage. Just a gauge: `vllm:kv_cache_usage_perc`. Above 85% and you're in the preemption zone. You'll see it in the ITL within seconds.

Number four — prefix cache hit rate. Hits divided by queries on the prefix cache counters. If you're serving a chatbot with the same system prompt across every request, this should be above 80%. Low hit rate means you're recomputing prefills you've already done — wasting GPU cycles on repeat work.

Number five — batch occupancy. `vllm:num_requests_running`. How many requests are sharing the GPU right now? This is the number that controls your ITL. More requests, longer iterations.

Number six — from DCGM — tensor core utilization. `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`. This tells you whether the GPU is doing math or waiting on memory. High tensor activity plus high ITL? The GPU is busy — busy serving someone else's request.

Take a photo of this slide. These six queries are the difference between "our LLM is slow" and "our batch is contended."

---

## [18:00] SLIDE 12 — Alerts That Actually Work

You don't need thirty alert rules. You need three.

Alert one: KV cache above 90% for 2 minutes. This means preemptions are happening or imminent. Your ITL is about to spike. Action: check your batch size, consider lowering `max-num-seqs`.

Alert two: TTFT p99 above 2 seconds for 5 minutes. This is your user-facing SLO. If the first token takes more than 2 seconds, your users are staring at a spinner. They'll close the tab. Action: check queue depth. If requests are queuing, scale horizontally. If the queue is empty but TTFT is high, your prefill is overloaded — you might need a larger instance or tensor parallelism.

Alert three: `num_requests_waiting` above zero for 3 minutes sustained. This means you've hit real capacity. Requests can't even get into the batch. This is the one alert that actually means "add more GPUs." Action: scale out.

Three alerts. They cover batch pressure, user experience, and capacity. Everything else is a dashboard you check when one of these fires.

---

## [19:30] SLIDE 13 — Taming the Neighbour

Four mitigations. All of them are config changes, not architecture changes.

Number one: cap your batch size. vLLM's default `max-num-seqs` is 256. That's 256 requests fighting for one GPU on every iteration. I've seen production instances running at default. Don't do this. Start at 16 or 32 and tune up while watching ITL p99. You're trading throughput for latency predictability. Find the sweet spot for your workload.

Number two: route by estimated output length. If you're serving both "summarize this in one sentence" and "write a 2,000-word analysis," don't put them on the same GPU. Build a simple router — estimate output length from prompt structure. "Summarize" goes to Pool A with small batch limits. "Write a detailed report" goes to Pool B with larger batch limits but fewer concurrent requests. You don't need a perfect predictor. Even a rough split eliminates the worst noisy-neighbour scenarios.

Number three: enable prefix caching. If you're running a chatbot with the same system prompt — and most of you are — every single request recomputes the KV for that system prompt from scratch. That's wasted GPU time. Pass `--enable-prefix-caching` to vLLM and the KV blocks for shared prefixes get cached and reused. Monitor the hit rate. It should be above 80% for chatbot workloads.

Number four: autoscale on queue depth, not GPU utilization. GPU utilization is a lagging indicator — by the time it's high, your users are already waiting. Queue depth is the leading indicator. If `num_requests_waiting` is above zero for 60 seconds, scale up. Don't wait for the GPU to hit 90%.

---

## [21:00] SLIDE 14 — What to Do Monday Morning

Here's your Monday morning checklist. Six items.

One: expose vLLM's /metrics to Prometheus. It's already there — you just need to scrape it.

Two: add DCGM Exporter to your GPU nodes. It's a DaemonSet if you're on Kubernetes, or a sidecar container if you're on Docker Compose.

Three: build the six-panel Grafana dashboard from slide 11. The PromQL is up there — take a photo.

Four: set the three alerts from slide 12.

Five: tune `--max-num-seqs`. Start at 16. Watch ITL p99. Increase until ITL starts climbing, then back off.

Six: enable `--enable-prefix-caching` if you have shared system prompts.

I'll share the Grafana dashboard JSON and the full demo repo. Everything is open-source. Everything runs on Docker Compose so you can test it locally before touching production.

**[Pause]**

Next time your LLM p99 spikes, don't ask "which request is slow?"

Ask: "who else is in the batch?"

Thank you.

---

## Q&A

**Q: Does this apply to TGI too?**
> "Absolutely. TGI uses continuous batching with the same dynamics. The metric names are different — TGI exposes `tgi_request_duration`, `tgi_batch_current_size`, `tgi_queue_size` — but the signals are identical. TTFT, ITL, batch size, queue depth. Any server that fuses requests onto the same GPU has this problem."

**Q: What about multi-GPU with tensor parallelism?**
> "Same problem, amplified. With tensor parallelism the batch is sharded across all GPUs in the TP group. Every GPU processes every request. A noisy neighbour in a TP=4 setup wastes cycles on all four GPUs, not just one. The metrics are the same — just watch them per-replica."

**Q: How do you route by output length if you don't know it in advance?**
> "You estimate. Prompt structure gives you a lot — 'summarize in one sentence' is short, 'write a detailed analysis' is long. Historical data for the same endpoint and user type helps. You don't need a perfect predictor. Even a binary split — short pool, long pool — eliminates the 50-token-meets-4000-token scenario."

**Q: What model size does this matter for?**
> "Any model using continuous batching. It's more visible with larger models because KV cache per request scales with hidden dimensions times number of layers times sequence length. A 70B model fills KV cache 20× faster than a 3B model. But even at 3B, we showed a 3× ITL spike with just three noisy neighbours."

**Q: Can't you just set max-num-seqs to 1?**
> "You could, and your latency will be perfect — for one user at a time. Throughput drops 10-20× because you've eliminated batching entirely. The GPU sits idle between iterations. The goal isn't to avoid batching — it's to observe it, understand it, and manage it. Cap at 16-32, not 1."

---

## Sources

- vLLM metrics documentation: docs.vllm.ai
- vLLM PagedAttention paper: "Efficient Memory Management for Large Language Model Serving with PagedAttention" (Kwon et al., 2023)
- NVIDIA DCGM Exporter: github.com/NVIDIA/dcgm-exporter
- Continuous batching: "Orca: A Distributed Serving System for Transformer-Based Generative Models" (Yu et al., 2022)
- Prefix caching: vLLM automatic prefix caching documentation
