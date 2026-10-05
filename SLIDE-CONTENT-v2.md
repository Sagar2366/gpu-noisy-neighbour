# Slide Content v2 — The Noisy Neighbour Inside Your GPU

> **24 slides · 25 min · 3 acts · Apartment building analogy**
> **Observability Summit Europe 2026 · 5 Oct · 10:30–10:55**

---

## Analogy Key

| GPU Concept | Apartment Analogy | Color |
|-------------|------------------|-------|
| GPU | 🏢 The Building | — |
| Batch | 🛗 The Elevator (shared) | Purple |
| KV Cache | 🧳 The Storage Room | Amber |
| Requests | 👤 Tenants | — |
| Preemption | 📦 Eviction (stuff to basement) | Red |
| TTFT | Elevator wait time | Blue |
| ITL | Elevator speed | Amber |
| Queue | Lobby | Yellow |
| cgroups (CPU) | Soundproof walls | Green |
| No GPU cgroups | Paper-thin walls | Red |
| Alex | 💙 Quiet tenant (64 tok) | Blue #00D4FF |
| Blake | ❤️ Renovator (4,000 tok) | Red #FF4444 |

---

## ACT 1: THE PROBLEM (Slides 1–9, 8 min)

### Slide 1: Title
- "The Noisy Neighbour Inside Your GPU"
- "Observing Batched LLM Inference"
- Sagar Utekar · Senior SRE, CrowdStrike · CNCF Ambassador · Kubestronaut
- Observability Summit Europe 2026
- ⏱️ 45s

### Slide 2: The Neighbour You Already Know
- Left: 🔥 CPU Problem — rogue container steals CPU, latency spikes, no errors
- Right: ✅ How You Fixed It — cgroups, resource limits, node pools, anti-affinity
- Bottom line: "CPU noisy neighbours? Solved. You had soundproof walls."
- ⏱️ 60s

### Slide 3: Now Forget Everything
- Two columns: CPU World ✓ (cgroups, limits, isolation) vs GPU World ✗ (no cgroups, no limits, 32 requests = 1 chip)
- Bottom: "On a GPU, requests MUST share the chip. The walls are paper-thin."
- "The fix isn't soundproofing — it's installing noise monitors."
- ⏱️ 60s

### Slide 4: The Apartment Building
- Five rows mapping GPU → Apartment concepts
- GPU = Building, Batch = Elevator, KV Cache = Storage Room, Requests = Tenants, Preemption = Eviction
- "Keep this picture. Every slide maps back to it."
- ⏱️ 45s

### Slide 5: Two Phases, Two Numbers
- Prefill (compute-bound, GPU loves it) vs Decode (memory-bound, GPU waits)
- TTFT = elevator wait time
- ITL = elevator speed ← THE SIGNAL
- ⏱️ 60s

### Slide 6: Meet Your Neighbours
- Alex 💙: "Summarise this Jira ticket" · 64 tokens · quick errand
- Blake ❤️: "Write a capacity report" · 4,000 tokens · same elevator
- "Alex will file the noise complaint. Blake is about to ruin Alex's morning."
- ⏱️ 45s

### Slide 7: Why Everyone Shares the Elevator
- 1 tenant = 10% GPU utilization (red) vs 8 tenants = 65% (green)
- Continuous batching: 36× throughput vs static (Orca 2022)
- "But now everyone shares the elevator. Blake's furniture slows it for everyone."
- ⏱️ 60s

### Slide 8: The Storage Room Crisis
- Alex: 8% of storage room · Blake: 79% · ~4 GB
- ⚠️ STORAGE FULL → EVICTION → re-prefill from scratch
- "That's your mystery TTFT spike."
- Metric: `vllm:kv_cache_usage_perc` >85% = danger zone
- ⏱️ 60s

### Slide 9: What Alex Experiences
- Alone: TTFT 82ms → ITL 14ms → 210ms total ✅
- With Blake: TTFT 120ms → ITL 45ms → 482ms total ❌ (2.3× slower, zero errors)
- **"ITL × tokens = phantom latency. The elevator slowed. Alex didn't change. The building did."**
- ⏱️ 45s

---

## ACT 2: THE SIGNALS + DEMO (Slides 10–17, 8 min)

### Slide 10: Your Dashboard Lies
- Left: RED shows Rate ✓, Errors 0, P99 1.8s ✗ → "Slow tenants. Build more buildings."
- Right: Reality — 190ms compute + 1,610ms WAITING, storage 94%, Blake generating 3,000+ tok
- "The tenant was fine. The building was noisy."
- ⏱️ 60s

### Slide 11: Three Causes of Latency
- 🕐 SCHEDULING — waiting in lobby → `num_requests_waiting` → Build more buildings
- 🧠 MEMORY — storage full, evictions → `kv_cache_usage_perc` → Occupancy cap + shared storage
- 👥 NEIGHBOUR — elevator slowed → `inter_token_latency_seconds` → Different building for renovators
- ⏱️ 45s

### Slide 12: The Monitoring System
- Grafana (security cameras) → Prometheus (sensor network, 15s) → vLLM /metrics + DCGM Exporter
- "Four components. All open-source. No vendor lock-in."
- ⏱️ 30s

### Slide 13: [DEMO] Quiet Sunday Morning
- 6-panel metric snapshot — all green
- TTFT 82ms · ITL 14ms · Storage 18% · Occupancy 5 · Power 38% · Lobby 0
- "Everything flat. Everything green. Remember these numbers."
- ⏱️ 60s

### Slide 14: [DEMO] The Renovators Arrive
- 6-panel before → after with deltas
- TTFT ▲5× · ITL ▲3× · Storage ▲DANGER · Occupancy +3 · Power ▲2× · Lobby ✓ STILL ZERO
- **"Lobby is EMPTY. It's not a building shortage. It's a neighbour problem."**
- ⏱️ 75s (the emotional peak — pause on lobby reveal)

### Slide 15: The Chain Reaction
- Flow: Blake moves in → Occupancy 5→8 → Storage 18→87% → Evictions start → ITL 14→43ms → Alex: 210→482ms
- ❌ Dashboard: "BUILD MORE BUILDINGS" vs ✓ Reality: "FEWER NEIGHBOURS"
- ⏱️ 60s

### Slide 16: Six Sensors for Your Building
- "📸 Take a photo of this slide."
- 6 PromQL queries in a grid: TTFT, ITL (THE SIGNAL), KV Cache, Prefix Cache Hits, Batch Size, Tensor Core
- ⏱️ 75s

### Slide 17: Three Alarms. Not Thirty.
- ⚠️ Storage > 90% for 2 min → cap occupancy
- 🚨 TTFT > 2s for 5 min → scale or shed load
- 📊 Lobby > 0 for 3 min → build more
- ⏱️ 60s

---

## ACT 3: THE FIX (Slides 18–24, 6 min)

### Slide 18: Taming the Renovators
- 2×2 grid:
  1. Occupancy Cap: `--max-num-seqs 16` (default 256!)
  2. Separate Building: route by estimated output length
  3. Shared Storage: `--enable-prefix-caching` (30-50% savings)
  4. Scale on Lobby: lobby count = leading indicator, not GPU %
- ⏱️ 90s

### Slide 19: PagedAttention: Why This Works
- Before: pre-reserve max context per request → 60-80% waste
- After (vLLM): virtual memory paging → near-zero waste → enables continuous batching
- 🔗 understandingdata.com visualization + credit: James Phoenix
- ⏱️ 60s

### Slide 20: Advanced: Disaggregate Prefill & Decode
- Conflict: prefill (compute-heavy) vs decode (memory-heavy) on same GPU → head-of-line blocking
- Fix: dedicated prefill workers + dedicated decode workers
- "Emerging in TensorRT-LLM, Sarathi-Serve. Watch this space."
- ⏱️ 60s (SKIPPABLE if behind)

### Slide 21: Monday Morning
- 6 checkboxes: install sensors, install monitors, build dashboard (slide 16), set alarms (slide 17), cap occupancy, enable prefix caching
- "2-4 hours to install. 50-70% fewer complaints."
- ⏱️ 60s

### Slide 22: The Closing Line
- "Next time your LLM p99 spikes..."
- "don't ask 'which tenant is slow?'"
- **"Ask: 'who else is in the building?'"**
- ⏱️ 30s

### Slide 23: Resources
- GitHub: github.com/Sagar2366/gpu-noisy-neighbour
- Visualizations: understandingdata.com (KV cache, prefill/decode) — credit James Phoenix
- Papers: PagedAttention (2309.06180), Orca (2206.00364)
- @SaijUtekar
- ⏱️ 30s

### Slide 24: Q&A
- "Q & A"
- GitHub link + Twitter handle
- ⏱️ 2 min

---

## Design Specs

- **Background:** Dark navy #0A0E27
- **Text:** White #E8E8E8 · Calibri
- **Code:** Green #39FF14 · Consolas
- **Accents:** Blue #00D4FF · Green #39FF14 · Amber #FFB347 · Red #FF4444 · Purple #B877D9
- **Alex:** Blue #00D4FF · **Blake:** Red #FF4444
- **Layout:** 16:9 (13.333" × 7.5")
- **Title:** 36pt bold · **Body:** 20-22pt · **Big numbers:** 48-60pt bold · **Code:** 14-18pt
