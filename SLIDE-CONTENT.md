# The Noisy Neighbour Inside Your GPU: Observing Batched LLM Inference

## Complete 14-Slide Presentation

> **Duration:** 23 min + 2 min Q&A
> **Format:** Dark theme, big numbers, ASCII diagrams, pre-recorded demo
> **Story Arc:** Problem → Why Dashboards Lie → Signals + Demo → Production Patterns → Action

---

## TIMING OVERVIEW

| Section | Slides | Duration | Cumulative |
|---------|--------|----------|------------|
| The Problem | 1–3 | 4 min | 4 min |
| Why Dashboards Lie | 4–6 | 4 min | 8 min |
| The Signals + Demo | 7–10 | 8 min | 16 min |
| Production Patterns | 11–13 | 5 min | 21 min |
| Action + Close | 14 | 2 min | 23 min |
| Q&A buffer | — | 2 min | 25 min |

---

## ACT 1: THE PROBLEM (Slides 1–3)

---

### SLIDE 1 — Title

**Title:** The Noisy Neighbour Inside Your GPU: Observing Batched LLM Inference

**Visual:**
```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   The Noisy Neighbour                                            ║
║   Inside Your GPU                                                ║
║                                                                  ║
║   Observing Batched LLM Inference                                ║
║                                                                  ║
║   ─────────────────────────────────────                          ║
║                                                                  ║
║   Sagar Utekar · Senior SRE, CrowdStrike                        ║
║   CNCF Ambassador · Kubestronaut                                 ║
║                                                                  ║
║   Observability Summit Europe 2026                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**Speaker Notes:**
> "Hey everyone. I'm Sagar Utekar, Senior SRE at CrowdStrike, CNCF Ambassador and Kubestronaut. Today I'm going to talk about a neighbour problem that your dashboards can't see. Not a container stealing CPU — a request sitting on the same GPU, in the same batch, on the same decode iteration as yours. And I'll show you exactly how to find it."

**Time:** 0:00

---

### SLIDE 2 — Your p99 Is Lying to You

**Title:** The Latency Spike That Wasn't

**Visual:**
```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   Your LLM p99:    1,800 ms                                     ║
║                    ████████████████████░░░░  8× spike            ║
║                                                                  ║
║   The "slow" request:                                            ║
║     • Generated 47 tokens                                        ║
║     • Actual compute: 190 ms                                     ║
║     • Nothing was wrong with it                                  ║
║                                                                  ║
║   The cause:                                                     ║
║     • A different user's request                                 ║
║     • Generating 4,000 tokens                                    ║
║     • Sitting in the same batch                                  ║
║     • Finished 30 seconds ago                                    ║
║                                                                  ║
║   Your per-request trace shows none of this.                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**Speaker Notes:**
> "Here's a scenario I've seen in production. Your LLM inference p99 spikes 8×. You open your traces. You find a request that took 1.8 seconds. You look at it — 47 tokens, simple prompt, nothing unusual. So what happened? The answer isn't in your trace. The request that caused this spike was in a different user's session, generating 4,000 tokens, sitting in the same GPU batch. It finished half a minute ago. Your traces never connected the two."

**Time:** 0:30

---

### SLIDE 3 — The Neighbour You Can't See

**Title:** Static Batching vs Continuous Batching

**Visual:**
```
  STATIC BATCHING                    CONTINUOUS BATCHING
  (Old world)                        (vLLM, TGI, TensorRT-LLM)

  ┌─────────────────────────┐        ┌─────────────────────────┐
  │ Batch 1                 │        │ Iteration 1             │
  │                         │        │ ┌─A──B──C──D──────────┐ │
  │ ┌─A───────────────────┐ │        │ └─────────────────────┘ │
  │ ├─B───────────────────┤ │        ├─────────────────────────┤
  │ ├─C───┐               │ │        │ Iteration 2             │
  │ ├─D──┐│  ← C,D done   │ │        │ ┌─A──B──C──D──E──────┐ │
  │ │    ││    but wait    │ │        │ └──────────↑──────────┘ │
  │ │    ││    for A       │ │        │            E joins!     │
  │ └────┘└───────────────┘ │        ├─────────────────────────┤
  │                         │        │ Iteration 3             │
  │ A finishes → batch done │        │ ┌─A──B──E──F──────────┐ │
  │ C,D wasted 80% of time │        │ └──↑───────↑───────────┘ │
  └─────────────────────────┘        │   C,D done → F joins    │
                                     └─────────────────────────┘

  ✗ Short requests blocked           ✓ Requests join/leave freely
    by longest in batch              ✗ But now they SHARE the GPU
                                       every single iteration
```

**Speaker Notes:**
> "To understand the problem, you need to understand how modern LLM servers work. Old-school static batching pads every request to the longest one. vLLM, TGI, TensorRT-LLM — they use continuous batching. Requests join and leave the batch every iteration. A new request doesn't wait for the batch to finish — it jumps in on the next decode step. This is great for throughput. But it means your request is now fused onto the GPU alongside strangers'. Decoded token by token, in a batch that reshuffles every step. The neighbour sitting next to you on the GPU? You can't see them. And they're affecting your latency."

**Time:** 1:30

---

## ACT 2: WHY DASHBOARDS LIE (Slides 4–6)

---

### SLIDE 4 — Your RED Dashboard Is Wrong

**Title:** Why Classic Observability Misleads You

**Visual:**
```
  ┌─────────────────────────────────────────────────────────┐
  │  YOUR DASHBOARD (looks alarming)                         │
  │                                                          │
  │  Rate:     142 req/s    ✓ normal                         │
  │  Errors:   0.2%         ✓ normal                         │
  │  Duration: p50 = 210ms  ✓ normal                         │
  │            p99 = 1,800ms ✗ 8× spike!                     │
  │                                                          │
  │  Conclusion: "We have slow requests"                     │
  └─────────────────────────────────────────────────────────┘
                        ↓
  ┌─────────────────────────────────────────────────────────┐
  │  THE TRUTH                                               │
  │                                                          │
  │  The p99 request:                                        │
  │    • Generated 47 tokens in 190ms of actual compute      │
  │    • Waited 1,610ms because:                             │
  │      → KV cache was 94% full                             │
  │      → Batch had 28 active requests                      │
  │      → 3 batch-mates generating 3,000+ tokens each       │
  │      → Its KV blocks were preempted twice                │
  │                                                          │
  │  The request was fine. The batch was noisy.              │
  └─────────────────────────────────────────────────────────┘
```

**Speaker Notes:**
> "Here's what your RED dashboard shows. Rate, errors, duration — the holy trinity. Rate is normal. Errors are normal. But p99 spiked. So you conclude: we have slow requests. Here's the truth. That p99 request generated 47 tokens. Its actual compute was 190 milliseconds. It waited 1.6 seconds because the KV cache was 94% full, the batch had 28 active requests, three of its batch-mates were generating 3,000 tokens each, and its KV blocks got preempted twice. The request was fine. The batch was noisy. RED can't tell you that."

**Time:** 4:00

---

### SLIDE 5 — The Two Latencies That Matter

**Title:** TTFT vs Inter-Token Latency

**Visual:**
```
  Request A (short: 50 tokens output)
  ┌──────────┬──┬──┬──┬──┬──┬──┐
  │ Prefill  │t1│t2│t3│..│49│50│  Done!
  └──────────┴──┴──┴──┴──┴──┴──┘
  ├── TTFT ──┤                        TTFT = queue + prefill
  │          ├─ ITL ─┤                ITL  = gap between tokens
  │          │       │
  │   80ms   │  15ms │                Healthy: TTFT short, ITL stable

  Request A (same request, noisy batch)
  ┌──────────┬────┬────┬────┬────┬────┬────┐
  │ Prefill  │ t1 │ t2 │ t3 │ .. │ 49 │ 50 │  Done!
  └──────────┴────┴────┴────┴────┴────┴────┘
  ├── TTFT ──┤                        TTFT = 120ms (slightly worse)
  │          ├── ITL ──┤              ITL  = 45ms  (3× worse!)
  │          │         │
  │  120ms   │  45ms   │              Noisy: TTFT drifts, ITL SPIKES

  ──────────────────────────────────────────────────────────
  The noisy neighbour inflates ITL, not TTFT.
  Your per-request latency = TTFT + (ITL × output_tokens).
  A 3× ITL spike on 50 tokens = +1,500ms you can't explain.
```

**Speaker Notes:**
> "Two latencies matter for LLM inference. Time-to-first-token — TTFT — is how long from request arrival until the first token comes back. It's queue time plus prefill. Inter-token latency — ITL — is the gap between each subsequent token. Here's the key insight: the noisy neighbour mostly inflates ITL, not TTFT. Why? Because every decode iteration, your request shares GPU cycles with every other request in the batch. More requests in the batch means each iteration takes longer. Your total latency is TTFT plus ITL times the number of tokens. A 3× ITL spike on a 50-token response adds 1.5 seconds. And you'll never see it in an end-to-end latency histogram."

**Time:** 5:30

---

### SLIDE 6 — Inside a vLLM Scheduler Step

**Title:** What Happens Every Iteration

**Visual:**
```
  One vLLM Scheduler Iteration (~10-50ms)
  ═══════════════════════════════════════

  ┌─────────────────────┐
  │ 1. CHECK QUEUE       │    New requests waiting?
  │    waiting: 3        │    → Schedule for prefill
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │ 2. ALLOCATE KV CACHE │    Each request needs memory
  │    blocks_free: 847  │    for its key-value pairs
  │    blocks_used: 3153 │    ← 79% full
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │ 3. PREEMPT IF NEEDED │    KV cache full?
  │    preempted: 2      │    → Evict lowest-priority
  │    recompute later ↻ │      request's KV blocks
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │ 4. RUN ON GPU        │    Prefill new + decode active
  │    batch_size: 24    │    ALL 24 share the GPU
  │    this iteration    │    for this one forward pass
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │ 5. RETURN TOKENS     │    Each request gets one token
  │    finished: 1       │    Some requests finish → leave
  │    still_running: 23 │    Others continue next iteration
  └─────────────────────┘

  This repeats hundreds of times per second.
  Step 4 is where the noisy neighbour lives.
```

**Speaker Notes:**
> "Let me make this concrete. Here's what happens inside vLLM every single iteration — and this runs hundreds of times per second. First, check the queue. Are new requests waiting? Schedule them for prefill. Second, allocate KV cache blocks. Every request needs memory for its key-value pairs. If the cache is filling up, that's your first warning sign. Third — and this is where it gets interesting — if the KV cache is full, vLLM preempts. It evicts the lowest-priority request's KV blocks. That request will have to recompute them later. Fourth, run the forward pass on the GPU. All 24 requests in this batch share the GPU for this one pass. That's the noisy neighbour — step 4. Finally, return one token per request. Some finish and leave the batch. Others continue. And this repeats. The batch reshuffles every iteration."

**Time:** 7:00

---

## ACT 3: THE SIGNALS + DEMO (Slides 7–10)

---

### SLIDE 7 — The Observability Stack

**Title:** vLLM + DCGM + Prometheus + Grafana

**Visual:**
```
  ┌───────────────────────────────────────────────────────────┐
  │                      GRAFANA :3000                         │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
  │  │ TTFT p99 │ │ ITL p99  │ │ KV Cache │ │ Batch Size   │ │
  │  │  ▁▂▁▂▆█ │ │  ▁▁▁▂▅█ │ │  ▂▃▃▅▇█ │ │  ▃▃▃▅▆█     │ │
  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │
  │  ┌──────────────────────┐ ┌────────────────────────────┐  │
  │  │ Tensor Core Activity │ │ Queue Depth                │  │
  │  │  ▃▃▃▅▆▇             │ │  ▁▁▁▁▁▁   (zero = good)   │  │
  │  └──────────────────────┘ └────────────────────────────┘  │
  └──────────────────────────┬────────────────────────────────┘
                             │ queries
                             ↓
  ┌───────────────────────────────────────────────────────────┐
  │                    PROMETHEUS :9090                         │
  │         scrapes every 15s                                  │
  └──────────┬──────────────────────────────┬─────────────────┘
             │                              │
    ┌────────┴────────┐           ┌─────────┴──────────┐
    │  vLLM :8000     │           │ DCGM Exporter :9400│
    │  /metrics       │           │ /metrics           │
    │                 │           │                    │
    │ • TTFT          │           │ • GPU utilization  │
    │ • ITL           │           │ • Tensor core %    │
    │ • KV cache %    │           │ • Memory used/free │
    │ • Batch size    │           │ • Temperature      │
    │ • Queue depth   │           │ • Power draw       │
    │ • Prefill time  │           │                    │
    │ • Decode time   │           │                    │
    └─────────────────┘           └────────────────────┘
```

**Speaker Notes:**
> "Here's the stack. vLLM exposes a /metrics endpoint with everything we need — TTFT, ITL, KV cache usage, batch size, queue depth. DCGM Exporter gives us the GPU-level view — tensor core activity, memory, power. Prometheus scrapes both every 15 seconds. Grafana gives us the dashboard. Six panels. That's it. No vendor lock-in, no agents, no magic. Open-source Prometheus and Grafana. Let me show you what this looks like in practice."

**Time:** 8:00

---

### SLIDE 8 — Demo Phase 1: Healthy Baseline

**Title:** [PRE-RECORDED] Five Short Requests, Happy Metrics

**Visual:**
```
  ┌─────────────────────────────────────────────────────────┐
  │  📹 PRE-RECORDED DEMO — Phase 1: Baseline               │
  └─────────────────────────────────────────────────────────┘

  Terminal:
  ┌─────────────────────────────────────────────────────────┐
  │ $ python load-generator.py --phase baseline              │
  │ Sending 5 concurrent requests (100 tok prompt, 50 max)   │
  │ Request 1: 47 tokens, 210ms ✓                            │
  │ Request 2: 50 tokens, 225ms ✓                            │
  │ Request 3: 42 tokens, 198ms ✓                            │
  │ Request 4: 50 tokens, 231ms ✓                            │
  │ Request 5: 49 tokens, 219ms ✓                            │
  └─────────────────────────────────────────────────────────┘

  Grafana:
  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
  │ TTFT p99     │ │ ITL p99      │ │ KV Cache             │
  │              │ │              │ │                      │
  │    82ms      │ │    14ms      │ │    18%               │
  │  ▁▁▁▂▁▁▁▁   │ │  ▁▁▁▁▁▁▁▁   │ │  ▂▂▂▂▂▂▂▂           │
  └──────────────┘ └──────────────┘ └──────────────────────┘
  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
  │ Batch Size   │ │ Tensor Core  │ │ Queue Depth          │
  │              │ │              │ │                      │
  │    5         │ │    38%       │ │    0                 │
  │  ▃▃▃▃▃▃▃▃   │ │  ▃▃▃▃▃▃▃▃   │ │  ▁▁▁▁▁▁▁▁           │
  └──────────────┘ └──────────────┘ └──────────────────────┘

  Everything flat. Everything healthy. Remember these numbers.
```

**Speaker Notes:**
> "I pre-recorded this on a cloud GPU instance running vLLM with Llama 3.2 3B. Five concurrent short requests — 100-token prompts, generating about 50 tokens each. Look at the metrics. TTFT p99: 82 milliseconds. ITL p99: 14 milliseconds. KV cache at 18%. Batch size of 5. Tensor cores at 38%. Queue depth is zero — no one's waiting. Everything is flat. Everything is healthy. Remember these numbers."

**Time:** 9:00

---

### SLIDE 9 — Demo Phase 2: Inject the Noisy Neighbour

**Title:** [PRE-RECORDED] Three Long Requests Join the Batch

**Visual:**
```
  ┌─────────────────────────────────────────────────────────┐
  │  📹 PRE-RECORDED DEMO — Phase 2: Noisy Neighbours       │
  └─────────────────────────────────────────────────────────┘

  Terminal:
  ┌─────────────────────────────────────────────────────────┐
  │ $ python load-generator.py --phase noisy                 │
  │ Baseline still running (5 short requests)                │
  │ Injecting 3 noisy neighbours (500 tok prompt, 3000 max)  │
  │                                                          │
  │ Short request 6:  50 tokens,  482ms  ⚠️  (was 210ms)     │
  │ Short request 7:  47 tokens,  511ms  ⚠️  (was 198ms)     │
  │ Noisy request 1: 2847 tokens, 38.2s  ← generating...    │
  │ Short request 8:  50 tokens,  497ms  ⚠️  (2.3× slower)   │
  └─────────────────────────────────────────────────────────┘

  Grafana:
  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
  │ TTFT p99     │ │ ITL p99      │ │ KV Cache             │
  │              │ │              │ │                      │
  │   420ms ▲    │ │   43ms ▲     │ │    87% ▲             │
  │  ▁▁▁▂▅▇█▇   │ │  ▁▁▁▂▅▇█▇   │ │  ▂▂▂▃▅▇██           │
  │      ↑       │ │      ↑       │ │       ↑              │
  │  5× spike    │ │  3× spike    │ │   from 18%           │
  └──────────────┘ └──────────────┘ └──────────────────────┘
  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
  │ Batch Size   │ │ Tensor Core  │ │ Queue Depth          │
  │              │ │              │ │                      │
  │    8 ▲       │ │    74% ▲     │ │    0                 │
  │  ▃▃▃▅▇▇▇▇   │ │  ▃▃▃▅▆▇▇▇   │ │  ▁▁▁▁▁▁▁▁           │
  │  +3 requests │ │  GPU busy!   │ │  no queue!           │
  └──────────────┘ └──────────────┘ └──────────────────────┘
```

**Speaker Notes:**
> "Now I inject three noisy neighbours. Same GPU, same vLLM instance. These are requests with 500-token prompts asking for 3,000 tokens of output. The short requests are still running — same prompts, same max tokens. Watch what happens. TTFT jumps from 82ms to 420ms — 5× worse. ITL goes from 14ms to 43ms — 3× worse. KV cache rockets from 18% to 87%. Batch size goes from 5 to 8. And here's the critical one — look at tensor core activity. 74%. The GPU is working harder. And queue depth? Still zero. No requests are waiting. Everyone got scheduled. The problem isn't queueing. The problem is what happens after you're in the batch."

**Time:** 11:00

---

### SLIDE 10 — Demo Phase 3: Pin the Cause

**Title:** [PRE-RECORDED] It's Not the Queue. It's the Batch.

**Visual:**
```
  ┌─────────────────────────────────────────────────────────┐
  │  📹 PRE-RECORDED DEMO — Phase 3: Root Cause              │
  └─────────────────────────────────────────────────────────┘

  The correlation chain:
  ┌─────────────────────────────────────────────────────────┐
  │                                                          │
  │  3 long requests join    KV cache          Short request │
  │  the batch               fills up          ITL spikes    │
  │        │                    │                    │       │
  │        ↓                    ↓                    ↓       │
  │   batch_size: 5→8    kv_cache: 18%→87%    ITL: 14→43ms  │
  │        │                    │                    │       │
  │        ↓                    ↓                    ↓       │
  │   More work per        Preemptions          Each decode  │
  │   forward pass         start happening      step slower  │
  │        │                    │                    │       │
  │        └────────────────────┴────────────────────┘       │
  │                             │                            │
  │                             ↓                            │
  │                   e2e latency: 210→482ms                 │
  │                   (same 50-token request)                │
  │                                                          │
  └─────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────┐
  │  THE MISLEADING DASHBOARD:                             │
  │                                                        │
  │  "GPU utilization 74% and p99 doubled.                 │
  │   You need more GPUs."                                 │
  │                                                        │
  │  THE REAL ANSWER:                                      │
  │                                                        │
  │  "Cap --max-num-seqs to 16.                            │
  │   Route long-generation requests to a separate pool.   │
  │   You don't need more GPUs. You need fewer neighbours."│
  └───────────────────────────────────────────────────────┘
```

**Speaker Notes:**
> "Let me connect the dots. Three long requests join the batch. Batch size goes from 5 to 8. That means more work per forward pass — the GPU has to compute attention for all 8 requests on every iteration. KV cache fills from 18% to 87% because those long requests hold onto their KV blocks for thousands of iterations. When it gets tight, vLLM starts preempting — evicting shorter requests' KV blocks to make room. Those short requests have to recompute their KV next time they're scheduled. Result: ITL triples. The same 50-token request now takes 482ms instead of 210ms. And here's what your dashboard tells you: GPU utilization is 74%, p99 doubled, you need more GPUs. The real answer? You don't need more GPUs. You need fewer neighbours. Cap your batch size. Route long-generation requests to a separate pool."

**Time:** 13:30

---

## ACT 4: PRODUCTION PATTERNS (Slides 11–13)

---

### SLIDE 11 — Six Queries for Your Dashboard

**Title:** The PromQL That Actually Matters

**Visual:**
```
  ┌─ 1. TTFT p99 ─────────────────────────────────────────┐
  │ histogram_quantile(0.99,                                │
  │   rate(vllm:time_to_first_token_seconds_bucket[5m]))    │
  │ → How long until the first token? (queue + prefill)     │
  └─────────────────────────────────────────────────────────┘

  ┌─ 2. ITL p99 ──────────────────────────────────────────┐
  │ histogram_quantile(0.99,                                │
  │   rate(vllm:inter_token_latency_seconds_bucket[5m]))    │
  │ → Gap between tokens. THIS is the noisy-neighbour signal│
  └─────────────────────────────────────────────────────────┘

  ┌─ 3. KV Cache Pressure ────────────────────────────────┐
  │ vllm:kv_cache_usage_perc                                │
  │ → Above 85%? Preemptions incoming.                      │
  └─────────────────────────────────────────────────────────┘

  ┌─ 4. Prefix Cache Hit Rate ────────────────────────────┐
  │ rate(vllm:prefix_cache_hits[5m])                        │
  │   / rate(vllm:prefix_cache_queries[5m])                 │
  │ → Low hit rate = wasted prefill compute.                │
  └─────────────────────────────────────────────────────────┘

  ┌─ 5. Batch Occupancy ──────────────────────────────────┐
  │ vllm:num_requests_running                               │
  │ → How crowded is the GPU right now?                     │
  └─────────────────────────────────────────────────────────┘

  ┌─ 6. Tensor Core Utilization ──────────────────────────┐
  │ DCGM_FI_PROF_PIPE_TENSOR_ACTIVE                         │
  │ → Is the GPU computing or waiting on memory?            │
  └─────────────────────────────────────────────────────────┘
```

**Speaker Notes:**
> "Six queries. Put these on your dashboard today. Number one — TTFT p99. How long until the first token? This is queue time plus prefill. Number two — ITL p99. This is the noisy-neighbour signal. If ITL spikes while TTFT stays stable, you have a batch problem. Number three — KV cache usage. Above 85% and vLLM starts preempting. You'll see it in the ITL. Number four — prefix cache hit rate. If you're serving a chatbot with the same system prompt, this should be above 80%. Low hit rate means you're recomputing prefills you've already done. Number five — batch occupancy, which is just num_requests_running. How crowded is the GPU? And number six — from DCGM — tensor core utilization. This tells you whether the GPU is actually computing or waiting on memory. High tensor activity plus high ITL means the GPU is doing work — for someone else."

**Time:** 16:00

---

### SLIDE 12 — Alerts That Actually Work

**Title:** Three Rules, Not Thirty

**Visual:**
```
  ┌─────────────────────────────────────────────────────────┐
  │  ALERT 1: KV Cache Pressure                             │
  │                                                          │
  │  expr: vllm:kv_cache_usage_perc > 0.90                  │
  │  for:  2m                                                │
  │  ──────────────────────────────────────                  │
  │  Why: Preemptions are imminent or happening.             │
  │  Action: Check batch size. Consider --max-num-seqs cap.  │
  └─────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │  ALERT 2: TTFT SLO Breach                               │
  │                                                          │
  │  expr: histogram_quantile(0.99,                          │
  │    rate(vllm:time_to_first_token_seconds_bucket[5m]))    │
  │    > 2                                                   │
  │  for:  5m                                                │
  │  ──────────────────────────────────────────              │
  │  Why: Users waiting >2s for first token = bad UX.        │
  │  Action: Check queue depth → scale or shed load.         │
  └─────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │  ALERT 3: Queue Building                                 │
  │                                                          │
  │  expr: vllm:num_requests_waiting > 0                     │
  │  for:  3m                                                │
  │  ──────────────────────────────────────                  │
  │  Why: Sustained queue = capacity limit reached.          │
  │  Action: Scale horizontally or increase --max-num-seqs.  │
  └─────────────────────────────────────────────────────────┘
```

**Speaker Notes:**
> "You don't need thirty alert rules. You need three. First — KV cache above 90% for 2 minutes. This means preemptions are happening or about to. Check your batch size. Second — TTFT p99 above 2 seconds for 5 minutes. This is your user-facing SLO. If the first token takes more than 2 seconds, your users are staring at a spinner. Check queue depth, check if you need to scale. Third — any requests waiting in the queue for more than 3 minutes sustained. This means you've hit capacity. Either scale horizontally or increase max-num-seqs if you have headroom. Three alerts. They cover batch pressure, user experience, and capacity."

**Time:** 18:00

---

### SLIDE 13 — Taming the Neighbour

**Title:** Four Mitigations That Work

**Visual:**
```
  ┌─ 1. CAP BATCH SIZE ───────────────────────────────────┐
  │                                                         │
  │  vllm serve model --max-num-seqs 16                     │
  │                                                         │
  │  Default is 256. That's 256 requests sharing one GPU.   │
  │  Start at 16-32. Tune based on ITL p99.                 │
  └─────────────────────────────────────────────────────────┘

  ┌─ 2. ROUTE BY OUTPUT LENGTH ───────────────────────────┐
  │                                                         │
  │  ┌───────────┐    short (est <200 tok) → Pool A        │
  │  │  Router   │───────────────────────────────────       │
  │  └───────────┘    long  (est >200 tok) → Pool B        │
  │                                                         │
  │  Estimate from prompt structure + historical averages.  │
  │  "Summarize this" → short. "Write a report" → long.    │
  └─────────────────────────────────────────────────────────┘

  ┌─ 3. ENABLE PREFIX CACHING ────────────────────────────┐
  │                                                         │
  │  vllm serve model --enable-prefix-caching               │
  │                                                         │
  │  Same system prompt across requests?                    │
  │  Cache the KV blocks. Skip re-prefill. Save GPU cycles. │
  │  Monitor: prefix_cache_hits / prefix_cache_queries      │
  └─────────────────────────────────────────────────────────┘

  ┌─ 4. AUTOSCALE ON QUEUE, NOT GPU% ────────────────────┐
  │                                                         │
  │  ✗ Scale on GPU utilization   (too late, already busy)  │
  │  ✓ Scale on num_requests_waiting > 0 for 60s            │
  │                                                         │
  │  Queue depth is the leading indicator.                   │
  │  GPU utilization is the lagging one.                     │
  └─────────────────────────────────────────────────────────┘
```

**Speaker Notes:**
> "Four things you can do about it. One — cap your batch size. The default in vLLM is 256. That's 256 requests fighting for one GPU. Start at 16 or 32 and tune based on your ITL p99. Two — route by estimated output length. 'Summarize this paragraph' goes to Pool A. 'Write a detailed 2000-word report' goes to Pool B. You can estimate from prompt structure and historical averages. Three — enable prefix caching. If you're running a chatbot with the same system prompt, you're recomputing the same KV blocks for every request. Turn on prefix caching, and monitor the hit rate. Four — autoscale on queue depth, not GPU utilization. GPU utilization is a lagging indicator — by the time it's high, your users are already waiting. Queue depth is the leading indicator. If requests are queuing, scale up."

**Time:** 19:30

---

## ACT 5: ACTION + CLOSE (Slide 14)

---

### SLIDE 14 — What to Do Monday Morning

**Title:** Whose Request Is Actually Slow, and Why?

**Visual:**
```
  ┌─────────────────────────────────────────────────────────┐
  │  MONDAY MORNING CHECKLIST                                │
  │                                                          │
  │  □ Expose vLLM /metrics to Prometheus                    │
  │  □ Add DCGM Exporter to your GPU nodes                   │
  │  □ Build the 6-panel Grafana dashboard (slide 11)        │
  │  □ Set the 3 alerts (slide 12)                           │
  │  □ Tune --max-num-seqs (start at 16, watch ITL)          │
  │  □ Enable --enable-prefix-caching                        │
  └─────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │  RESOURCES                                               │
  │                                                          │
  │  📊 Grafana dashboard JSON → github.com/sagar/...        │
  │  📖 vLLM metrics docs      → docs.vllm.ai/metrics       │
  │  📖 DCGM Exporter          → github.com/NVIDIA/dcgm-    │
  │                                exporter                  │
  │  🐦 Questions?             → @SaijUtekar                 │
  └─────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────┐
  │                                                          │
  │   Next time your LLM p99 spikes, don't ask              │
  │   "which request is slow?"                               │
  │                                                          │
  │   Ask: "who else is in the batch?"                       │
  │                                                          │
  └─────────────────────────────────────────────────────────┘

  Thank you.
```

**Speaker Notes:**
> "Here's your Monday morning checklist. Six items. Expose vLLM metrics to Prometheus. Add DCGM Exporter to your GPU nodes. Build the six-panel dashboard — the PromQL is on slide 11, take a photo. Set the three alerts from slide 12. Tune your batch size — start at 16, watch ITL. Enable prefix caching. I'll share the Grafana dashboard JSON and the demo repo. Everything is open-source, everything runs on Docker Compose for testing. **[Pause]** Next time your LLM p99 spikes, don't ask 'which request is slow?' Ask: 'who else is in the batch?' Thank you."

**Time:** 21:00

---

## APPENDIX: Q&A Preparation

**Q1: Does this apply to TGI / TensorRT-LLM too?**
> Yes. TGI uses continuous batching with the same dynamics. TensorRT-LLM has its own in-flight batching. The metric names differ — TGI uses `tgi_request_duration`, `tgi_batch_current_size`, etc. — but the signals are identical. TTFT, ITL, batch size, queue depth. The noisy-neighbour problem exists in any system that shares a GPU across requests.

**Q2: What about multi-GPU / tensor parallelism?**
> Same problem. With tensor parallelism, the batch is sharded across all GPUs in the TP group. Every GPU processes every request in the batch. A noisy neighbour in a TP=4 setup wastes cycles on all four GPUs, not just one.

**Q3: How do you route by output length if you don't know it in advance?**
> You estimate. Use prompt structure heuristics — "summarize" vs "write a detailed report." Use historical data — same user, same endpoint, similar prompt length → similar output length. You don't need to be perfect. Even a rough split (short pool / long pool) eliminates the worst noisy-neighbour scenarios.

**Q4: What model size does this matter for?**
> Any model using continuous batching. The effect is more visible with larger models because KV cache per request is bigger (proportional to hidden dimensions × num layers × sequence length). A 70B model with 80 layers will fill KV cache much faster than a 3B model. But even at 3B, we showed a 3× ITL spike with just 3 noisy neighbours.

**Q5: Can you just set max_num_seqs to 1?**
> You could, and your latency will be perfect — for one user. Throughput drops 10-20× because you've eliminated batching entirely. The GPU sits idle between iterations. The goal isn't to avoid batching — it's to observe it, understand it, and manage it. Cap at 16-32, not 1.

---

## SUGGESTED VISUAL STYLE

- **Theme:** Dark background (navy/charcoal), white text
- **Accent colours:** Electric blue (`#00D4FF`) for metrics, neon green (`#39FF14`) for good values, warning amber (`#FFB347`) for spikes, red (`#FF4444`) for alerts
- **Font:** Monospace for all code, PromQL, and numbers. Sans-serif for titles.
- **Design principle:** One big idea per slide. Numbers should be BIG.
- **Diagrams:** Recreate ASCII art in Excalidraw or Figma for the actual deck. Keep the hand-drawn feel.

---

## TALK TIPS

- **Open with the mystery** — the p99 spike that wasn't a slow request. The audience needs to feel the frustration before you explain it.
- **The demo moment** — Phase 2 (injecting the noisy neighbour) is the emotional peak. Pause when the metrics shift. Let the audience see it.
- **The aha** — "You don't need more GPUs. You need fewer neighbours." This is the line they'll remember.
- **End with the action** — The Monday morning checklist is concrete. People photograph it. Make the text readable from the back of the room.
