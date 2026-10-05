# Demo Plan v2 — Noisy Neighbour Observatory

> **Mapped to slides:** 13 (Baseline) → 14 (Blake Arrives) → 15 (Chain Reaction)
> **Total demo time:** ~4 min of talk time (slides 13-15)
> **Format:** Pre-recorded Grafana screenshots embedded in slides
> **Story:** "Quiet Sunday morning → Renovators arrive → Chain reaction"

---

## Pre-Recording Infrastructure

| Option | Path | When to use |
|--------|------|-------------|
| **Kubernetes (recommended)** | `demo/kubernetes/` | You have a GPU K8s cluster (e.g., coder cluster) |
| **Docker Compose** | `demo/docker-compose.yml` | Standalone GPU machine |

**Model:** `meta-llama/Llama-3.2-3B-Instruct` (fits single GPU, fast enough for demo)

---

## Pre-Flight Checklist

- [ ] GPU available (K8s node or Docker with nvidia-container-toolkit)
- [ ] HuggingFace token exported as `HF_TOKEN`
- [ ] vLLM pod/container running and model loaded
- [ ] Load generator deployed and accessible on port 8080
- [ ] Grafana dashboard imported ("LLM Inference: Noisy Neighbour Observatory")
- [ ] All 6 panels visible without scrolling
- [ ] Grafana dark theme enabled
- [ ] Screen recording tool ready (OBS / QuickTime)

---

## Recording Session

### Phase 1: Baseline (for Slide 13)

```bash
# Start 5 short requests
curl -s -X POST http://localhost:8080/baseline | jq .

# Wait 60s for metrics to stabilize
sleep 60

# Verify steady state
curl -s http://localhost:8080/status | jq .
```

**📸 Screenshot the Grafana dashboard now.** Expected values:

| Panel | Value | Color |
|-------|-------|-------|
| TTFT p99 | ~82ms | Green |
| ITL p99 | ~14ms | Green |
| KV Cache | ~18% | Green |
| Occupancy | 5 | Blue |
| Tensor Core | ~38% | Blue |
| Queue Depth | 0 | Green |

**What to say on this slide:** "Everything flat. Everything green. Remember these numbers."

---

### Phase 2: Inject Noisy Neighbours (for Slide 14)

```bash
# Keep baseline running. Add 3 long-output requests.
curl -s -X POST http://localhost:8080/noisy | jq .

# Wait 60-90s for full impact
sleep 90

# Check impact
curl -s http://localhost:8080/status | jq .
```

**📸 Screenshot the Grafana dashboard now.** Expected values:

| Panel | Before | After | Δ |
|-------|--------|-------|---|
| TTFT p99 | 82ms | ~420ms | ▲ 5× |
| ITL p99 | 14ms | ~43ms | ▲ 3× |
| KV Cache | 18% | ~87% | ▲ DANGER |
| Occupancy | 5 | ~8 | +3 |
| Tensor Core | 38% | ~74% | ▲ 2× |
| Queue Depth | 0 | 0 | ✓ STILL ZERO |

**The key reveal:** Lobby is STILL ZERO. It's not a building shortage. It's a neighbour problem.

---

### Phase 3: Recovery (optional, for completeness)

```bash
# Stop all load
curl -s -X POST http://localhost:8080/stop | jq .

# Wait 30s, metrics return to baseline
sleep 30
```

**📸 Screenshot if you want a "recovery" slide for Q&A backup.**

---

## How Screenshots Become Slides

1. Take high-res screenshots (Retina/2×) of the full 6-panel Grafana dashboard
2. Crop out browser chrome — dashboard only
3. The PPTX has placeholder metric boxes on slides 13 and 14
4. **Option A:** Replace placeholder boxes with actual Grafana screenshots
5. **Option B:** Keep the clean metric boxes, update the numbers to match your actual readings
6. **Recommended:** Use Option B for the slides (cleaner on projector), keep screenshots as backup

---

## Adapting to Coder Cluster

If running on the DEV coder cluster:

| Setting | Default in manifests | Coder cluster value |
|---------|---------------------|-------------------|
| GPU node selector | `nvidia.com/gpu.present: "true"` | Check: `kubectl get nodes -l nvidia.com/gpu.present=true` |
| GPU toleration | `nvidia.com/gpu` NoSchedule | Check: `kubectl describe node <gpu-node>` for actual taints |
| Prometheus label | `release: prometheus` | Check: `kubectl get prometheus -A -o yaml | grep serviceMonitorSelector` |
| Grafana sidecar | `grafana_dashboard: "1"` | Check: `kubectl get deploy -A | grep grafana` then check sidecar labels |
| Image registry | `load-generator:latest` | Push to your internal registry or use `kubectl cp` workaround |

---

## Fallback Plan

| Priority | If... | Do... |
|----------|-------|-------|
| 1 | Screenshots don't look good | Use the clean metric boxes already in the PPTX — just update numbers |
| 2 | GPU cluster unavailable | Run via Docker Compose on a cloud GPU (Vast.ai, Lambda, RunPod) |
| 3 | Can't run demo at all | The PPTX has representative numbers baked in — tell the story verbally |

---

## Demo Aliases

```bash
#!/bin/bash
# source demo-aliases.sh
alias demo-baseline='curl -s -X POST http://localhost:8080/baseline | jq .'
alias demo-noisy='curl -s -X POST http://localhost:8080/noisy | jq .'
alias demo-stop='curl -s -X POST http://localhost:8080/stop | jq .'
alias demo-status='curl -s http://localhost:8080/status | jq .'
alias demo-vllm='curl -s http://localhost:8000/metrics | grep -E "vllm:(time_to_first|inter_token|kv_cache|num_requests)" | head -20'
alias demo-dcgm='curl -s http://localhost:9400/metrics | grep DCGM_FI_PROF_PIPE_TENSOR | head -5'
```
