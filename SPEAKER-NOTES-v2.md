# Speaker Notes — The Noisy Neighbour Inside Your GPU

> **Event:** Observability Summit Europe 2026 · 5 Oct · 10:30–10:55
> **Slot:** 25 min (22 min content + 2 min Q&A + 1 min buffer)
> **Format:** 24 slides · 3 acts · Pre-recorded demo
> **Pacing:** ~60 sec/slide average. Demo slides get 90s each.

---

## Timing Overview

| Act | Slides | Duration | Cumulative | Theme |
|-----|--------|----------|------------|-------|
| **1: The Problem** | 1–9 | 8 min | 0:00–8:00 | CPU bridge → GPU pivot → apartment → fundamentals → impact |
| **2: The Signals** | 10–17 | 8 min | 8:00–16:00 | Dashboard lies → causes → stack → demo → queries → alerts |
| **3: The Fix** | 18–24 | 6 min | 16:00–22:00 | Mitigations → PagedAttention → disaggregation → checklist → close |
| Q&A | — | 2 min | 22:00–24:00 | |

---

## ACT 1: THE PROBLEM (8 min)

### [0:00] SLIDE 1 — Title

> Hi, I'm Sagar. I run GPU infrastructure for AI workloads at CrowdStrike.
>
> Today we're hunting a ghost — a latency spike you can see on your dashboard but can't explain with your traces. The victim is Alex. The culprit is Blake. And they both live inside the same GPU.

**Key:** Name the characters immediately. Sets up the story.

---

### [0:45] SLIDE 2 — The Neighbour You Already Know

> You've all debugged this. Container B is a rogue batch job. It eats CPU. Your app gets throttled. Latency spikes. No errors in the logs.
>
> And you fixed it. cgroups — the kernel's soundproof walls between tenants. Resource limits cap the bully. Node pools give physical separation. Anti-affinity rules keep enemies apart.
>
> CPU noisy neighbours? Solved. You had soundproof walls.
>
> [PAUSE] Now let's talk about a building with no soundproofing.

**Key:** Start where the audience lives — they KNOW this problem. Build confidence before pulling the rug.

---

### [1:45] SLIDE 3 — Now Forget Everything

> [Let the table sink in for 3 seconds before speaking]
>
> GPUs don't have cgroups. There are no soundproof walls. 32 requests share one chip at the same time.
>
> You could isolate — run one request per GPU — but you'd use 10% of a $40,000 card.
>
> The fix isn't isolation. It's observability. That's what this talk is about.

**Key:** The pivot. "Paper-thin walls" is the image that should stick.

---

### [2:45] SLIDE 4 — The Apartment Building

> This is the mental model for the entire talk.
>
> GPU is an apartment building. The batch is the elevator — shared, one trip serves everyone. KV cache is the storage room — every tenant's stuff accumulates. When the storage room fills, someone gets evicted — that's preemption.
>
> Keep this picture. Every slide from here maps back to it.

**Key:** Pause after each mapping. Let each one land. They'll be referencing this for the next 20 minutes.

---

### [3:30] SLIDE 5 — Two Phases, Two Numbers

> Every LLM reply has two phases. Prefill reads your entire prompt — fast, compute-heavy, the GPU loves this. Decode writes back one token at a time — slow, memory-bound, the GPU waits a lot.
>
> Two numbers to know. TTFT — time to first token — is the elevator wait time. How long before the door opens.
>
> ITL — inter-token latency — is the elevator speed. How fast it moves between floors.
>
> [PAUSE] ITL is THE noisy neighbour signal. When Blake loads furniture in the elevator, ITL is what spikes for everyone.

**Key:** ITL is the star of the talk. Say "THE signal" with emphasis. Point at the slide.

---

### [4:30] SLIDE 6 — Meet Your Neighbours

> Meet Alex. Quick question — "summarise this Jira ticket." 64 tokens. A quick errand. In and out.
>
> Meet Blake. "Write me a capacity report." 4,000 tokens. Five pages. Same building, same elevator, same trip.
>
> [PAUSE] Alex is about to have a very bad morning.

**Key:** Personify the requests. The audience should start rooting for Alex.

---

### [5:15] SLIDE 7 — Why Everyone Shares the Elevator

> One tenant on a GPU — 10% utilized. You're paying for a building that's 90% empty.
>
> Eight tenants — 65% utilized. Same building, eight times the revenue.
>
> Continuous batching checks after every elevator trip: someone got off? Fill the spot immediately. 36× more tenants served versus static batching. That's from the Orca paper in 2022.
>
> [PAUSE] But now they all share every single trip. And Blake's renovation materials? They slow the elevator for everyone.

**Key:** Hit the 20-30% stat. The audience needs to understand WHY isolation isn't an option.

---

### [6:15] SLIDE 8 — The Storage Room Crisis

> KV cache is the storage room. Every token generated adds to the pile.
>
> Alex's 64 tokens — three small boxes, 8% of the room. Blake's 4,000 tokens — fills 79% of the room. About 4 gigabytes of GPU memory.
>
> When storage hits capacity, someone gets evicted. Their stuff goes to the basement — CPU memory. When they get rescheduled, they must re-prefill from scratch. That re-prefill? That's your mystery TTFT spike.
>
> It's not a new request. It's a returning tenant whose stuff got thrown out.

**Key:** "Re-prefill from scratch" should land with a wince. The audience has seen these TTFT spikes.

**Metric:** `vllm:kv_cache_usage_perc` — over 85% is the danger zone.

---

### [7:15] SLIDE 9 — What Alex Experiences

> Here's what Alex feels. Alone: elevator wait 82ms, each floor 14ms, done in 210 milliseconds. Express elevator.
>
> With Blake in the batch: elevator wait 120ms, each floor 45ms — same 64 tokens, done in 482ms. 2.3× slower. Zero errors. Zero timeouts. Nothing in the traces.
>
> [PAUSE] ITL times tokens equals phantom latency. The elevator slowed down. Alex didn't change. The building did.

**Key:** "Alex didn't change. The building did." — this is the thesis in one line. Deliver it slowly.

**⏱️ CHECKPOINT: Should be at ~8:00. If >9:00, compress Slide 10 narration.**

---

## ACT 2: THE SIGNALS + DEMO (8 min)

### [8:00] SLIDE 10 — Your Dashboard Lies

> Your RED dashboard says: rate fine, errors zero, p99 is 1.8 seconds. Conclusion? Slow tenant. Build more buildings.
>
> [PAUSE] Wrong.
>
> That 1.8 seconds was 190 milliseconds of actual compute and 1,610 milliseconds of waiting. KV cache 94% full. 28 tenants in the batch. Blake generating 3,000 tokens. Alex got evicted twice.
>
> The tenant was fine. The building was noisy.

**Key:** This is the "aha" moment for observability folks. RED metrics — their bread and butter — are misleading them.

---

### [9:00] SLIDE 11 — Three Causes

> Three causes of latency. Think of it as a diagnostic flowchart.
>
> Scheduling — people waiting in the lobby. Real capacity issue. Build more buildings.
>
> Memory — storage room full, evictions happening. Cap the occupancy. Enable shared storage.
>
> Neighbour — Blake's furniture slowing the elevator. Route renovators to a different building.
>
> Your dashboard shows the complaint. These three tell you the actual cause.

**Key:** This is the mental framework they'll use Monday. Three boxes, three fixes.

---

### [9:45] SLIDE 12 — The Monitoring System

> Quick architecture. Grafana is security cameras. Prometheus is the sensor network, scraping every 15 seconds. Two sources: vLLM metrics for the elevator, storage, and lobby. DCGM Exporter for power, temperature, and structural load.
>
> Four components. All open-source. No vendor lock-in. Moving on.

**Key:** 30 seconds max. Don't linger — the audience knows this stack.

---

### [10:15] SLIDE 13 — [DEMO] Quiet Morning

> [Pre-recorded screenshot] This is baseline. Five Alexes, quiet Sunday morning.
>
> TTFT 82 milliseconds. ITL 14 milliseconds. Storage 18 percent. Occupancy 5. Power 38 percent. Lobby zero.
>
> Everything flat. Everything green. [PAUSE] Remember these six numbers. I'm about to change three of them dramatically.

**Key:** Read each metric deliberately. They need the baseline numbers in memory.

---

### [11:15] SLIDE 14 — [DEMO] The Renovators Arrive

> [Dramatic pause] Three Blakes move in.
>
> TTFT — 5× slower. ITL — 3× slower. Storage jumps to 87 percent. Occupancy goes to 8. Power doubles.
>
> [LONG PAUSE] And the lobby? ...Still zero. Nobody is waiting to get in.
>
> This is NOT a building shortage. This is a noisy neighbour problem. The GPU isn't overloaded — it's sharing badly.

**Key:** The lobby-still-zero reveal is the emotional peak. Pause for 3 full seconds before saying "still zero."

---

### [12:30] SLIDE 15 — The Chain Reaction

> The chain reaction in one picture. Blake moves in → occupancy grows → storage fills → evictions start → ITL spikes → Alex goes from 210 to 482 milliseconds.
>
> Your dashboard says: GPU at 74%, latency doubled, scale up. The real answer: cap the occupancy, send renovators to their own building.
>
> You don't need more buildings. You need fewer neighbours.

**Key:** "You don't need more buildings. You need fewer neighbours." — deliver this like a punchline.

**⏱️ CHECKPOINT: Should be at ~13:00. If >14:00, read 3 of 6 queries on slide 16.**

---

### [13:15] SLIDE 16 — Six Sensors for Your Building

> Six sensors. [Say to audience] Take a photo of this slide.
>
> [Point to each] TTFT: elevator wait time. ITL — THE signal — elevator speed. KV cache: storage fullness, over 85% is danger. Prefix cache hit rate: are we re-reading mail we already read? Batch size: building occupancy. Tensor core: is the GPU actually working or just heating the room?
>
> ITL is number two and it's the one that changes everything.

**Key:** "Take a photo" — this is a conference technique. It tells them this slide matters AND gives them a takeaway.

**ESCAPE HATCH:** If behind on time, read only TTFT, ITL, and KV cache. Say "the other three are on GitHub."

---

### [14:30] SLIDE 17 — Three Alarms

> Three alarms. Not thirty.
>
> Storage over 90% for 2 minutes — evictions are imminent, cap occupancy now.
> TTFT over 2 seconds for 5 minutes — tenants are banging on the door, scale up or shed load.
> Lobby greater than zero for 3 minutes — this is a real capacity limit, time to build more.
>
> Three alarms. Not thirty. You can configure these in 20 minutes.

**Key:** "Not thirty" is the memorable hook. Repeat it at the end.

---

## ACT 3: THE FIX (6 min)

### [15:30] SLIDE 18 — Taming the Renovators

> Four ways to tame Blake.
>
> [One] Cap occupancy at 16. The default is 256 — that's 256 tenants sharing one elevator. Madness. Start at 16, watch ITL as you tune up.
>
> [Two] Separate building. Route short and long requests to different GPU pools. You don't need ML for this — "write a detailed report" goes to Pool B.
>
> [Three] Enable shared storage. Prefix caching reuses KV cache for common system prompts. Saves 30 to 50 percent memory.
>
> [Four] Scale on lobby count, not power. Lobby is a leading indicator. Power is lagging — by the time GPU hits 80%, Alex has already been evicted three times.

**Key:** Each mitigation maps back to the apartment analogy. Audience should be nodding.

---

### [17:00] SLIDE 19 — PagedAttention: Why This Works

> Why does continuous batching actually work? PagedAttention.
>
> Before: you pre-reserved the full context length for every request. Like reserving an entire storage unit for each tenant even if they only bring one box. 60 to 80 percent waste.
>
> After: vLLM allocates fixed-size blocks on demand. Like virtual memory. Near-zero waste. This is what enables dynamic slot-filling.
>
> James Phoenix has an amazing interactive visualization of this at understandingdata.com — link is on the slide.

**Key:** 60 seconds max. Connect back to "why we can't just isolate."

---

### [18:00] SLIDE 20 — Disaggregate Prefill & Decode

> For the advanced folks. Prefill is compute-bound. Decode is memory-bound. Running both on the same GPU causes head-of-line blocking.
>
> The cutting-edge fix: separate worker pools. Prefill gets dedicated GPUs. Decode gets dedicated GPUs. TTFT stays fast. ITL stays stable.
>
> This is emerging in TensorRT-LLM and Sarathi-Serve. Watch this space.

**Key:** "For the advanced folks" — signals this is bonus content. If behind, skip entirely.

**ESCAPE HATCH:** If >19:00, skip this slide. Jump to Monday Morning.

---

### [19:00] SLIDE 21 — Monday Morning

> Monday morning. Six items.
>
> Install elevator sensors — vLLM metrics to Prometheus. Install power monitors — DCGM on GPU nodes. Build the six-sensor dashboard from slide 16. Set the three alarms from slide 17. Cap occupancy at 16. Enable prefix caching.
>
> Two to four hours of work. 50 to 70 percent p99 reduction on mixed workloads.
>
> That's the ROI of observing your neighbours.

**Key:** This is the take-home. Make it feel achievable. "Two to four hours" should sound easy.

---

### [20:00] SLIDE 22 — The Closing Line

> [Slow, deliberate delivery. Look at the audience, not the screen.]
>
> Next time your LLM p99 spikes...
>
> Don't ask "which tenant is slow?"
>
> [3-second pause]
>
> Ask: "who else is in the building?"
>
> [PAUSE]
>
> Thank you.

**Key:** This line IS the talk. If they remember nothing else, they remember this.

---

### [20:30] SLIDE 23 — Resources

> Everything is on GitHub — slides, demo infrastructure, Grafana dashboard, load generator. The links to James Phoenix's visualizations are there too — amazing interactive explainers for KV cache and prefill-decode.
>
> Find me on Twitter. And thank you to the Observability Summit team for having me.

**Key:** 30 seconds. Don't linger. Let people take a photo.

---

### [21:00] SLIDE 24 — Q&A

> [Open for questions]

---

## Q&A Prep — Five Likely Questions

### 1. "Does this apply to TGI / TensorRT-LLM too?"
Yes. Any engine using continuous batching has the same dynamics. TGI, TensorRT-LLM, SGLang — all of them. Metric names differ but the three causes (scheduling, memory, neighbour) are universal.

### 2. "What about multi-GPU / tensor parallelism?"
Same problem. The batch is shared across all GPUs in the tensor-parallelism group. Every GPU in the TP group processes every request in the batch. The noisy neighbour affects all of them simultaneously.

### 3. "How do you route by output length without knowing it?"
Estimate from prompt structure + historical data. "Summarise this" → short pool. "Write a detailed report" → long pool. You don't need a classifier — simple keyword rules get you 80% of the way. Refine with p90 output length per prompt template over time.

### 4. "Can you just set max_num_seqs to 1?"
Technically yes — throughput drops 10-20×. A $40K GPU serving one request at a time. The goal isn't disabling batching — it's observing and managing it. Start at 16, watch ITL, tune up gradually.

### 5. "What model size does this matter for?"
Any model using continuous batching. More visible with larger models because KV cache per token is bigger (Llama 3 70B uses ~4× more KV per token than 8B). But even 3B models show the effect clearly — that's what the demo uses.

### 6. "What about speculative decoding?"
Great question. Speculative decoding uses a small draft model to predict multiple tokens, then the large model verifies in one pass. It can actually reduce the noisy neighbour effect because it reduces the number of decode iterations. But it adds complexity and the draft model itself competes for GPU memory.

---

## Escape Hatches

| If at... | And slide is... | Do this |
|----------|----------------|---------|
| 9:30 | Still on Slide 9 | Cut Slide 10 narration to 30s — just show the two columns |
| 14:00 | Still on Slide 15 | Read only 3 of 6 queries on Slide 16 |
| 17:00 | Haven't reached Slide 18 | Skip Slides 19-20 entirely (PagedAttention + Disaggregation) |
| 19:00 | Still on Slide 20 | Jump directly to Slide 22 (closing line). Skip Monday checklist. |
| 20:30 | On Slide 22 | Deliver closing line. Skip Resources slide. Show Q&A. |

---

## Pre-Talk Checklist

- [ ] Laptop plugged in (not on battery)
- [ ] Presentation in full-screen mode
- [ ] Font rendering verified on projector
- [ ] Speaker notes visible on presenter display
- [ ] Water bottle accessible
- [ ] Phone on silent
- [ ] Timer visible (phone or watch)
- [ ] Demo screenshots loaded in slides (not loading from network)
- [ ] Backup PDF version on USB stick
