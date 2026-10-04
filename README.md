# The Noisy Neighbour Inside Your GPU

> **Observing Batched LLM Inference**
>
> Observability Summit Europe 2026 · 5 October · South Hall 3A
>
> Sagar Utekar · Senior SRE, CrowdStrike · CNCF Ambassador · Kubestronaut

## 🎯 What This Talk Is About

Your LLM's p99 latency spiked 8×. The slow request? It was fine — 190ms of compute. The culprit finished 30 seconds ago, in a different user's session.

Traditional noisy neighbours fight over CPU containers. You fixed those with cgroups and resource limits. **GPU noisy neighbours share the exact same chip, the exact same decode iteration, and the exact same continuous batch.** There are no GPU cgroups. The fix isn't isolation — it's observability.

This repo contains everything from the talk: slides, demo infrastructure, Grafana dashboard, and the complete load-generation toolkit to reproduce the noisy neighbour effect on your own GPU cluster.

## 📂 What's In This Repo

```
├── slides.html                  # 35-slide reveal.js presentation (open in browser)
├── SLIDE-CONTENT.md             # Slide content with speaker notes
├── SPEAKER-SCRIPT.md            # Verbatim 23-min speaker script
├── DEMO-PLAN.md                 # Pre-recording runbook
└── demo/
    ├── docker-compose.yml       # Full stack: vLLM + DCGM + Prometheus + Grafana
    ├── .env.example             # HuggingFace token config
    ├── README.md                # Detailed setup instructions
    ├── kubernetes/              # K8s manifests (recommended path)
    │   ├── 00-namespace.yaml    # Namespace + HF token secret
    │   ├── 01-vllm.yaml         # vLLM deployment + service + ServiceMonitor
    │   ├── 02-load-generator.yaml
    │   └── 03-grafana-dashboard-cm.yaml
    ├── load-generator/          # FastAPI load generator
    │   ├── main.py              # 3-phase load: baseline / noisy / stop
    │   ├── Dockerfile
    │   └── requirements.txt
    ├── prometheus/
    │   └── prometheus.yml       # Scrape config for vLLM + DCGM
    └── grafana/
        ├── dashboards/
        │   └── noisy-neighbour.json   # 6-panel Grafana dashboard
        └── provisioning/
            ├── datasources/prometheus.yml
            └── dashboards/dashboard.yml
```

## 🚀 Quick Start (Kubernetes)

```bash
# 1. Create namespace + secret
export HF_TOKEN="hf_your_token_here"
envsubst < demo/kubernetes/00-namespace.yaml | kubectl apply -f -

# 2. Deploy vLLM
kubectl apply -f demo/kubernetes/01-vllm.yaml
kubectl -n llm-demo wait --for=condition=ready pod -l app=vllm --timeout=600s

# 3. Deploy load generator
docker build -t load-generator:latest demo/load-generator/
kubectl apply -f demo/kubernetes/02-load-generator.yaml

# 4. Import Grafana dashboard
kubectl apply -f demo/kubernetes/03-grafana-dashboard-cm.yaml

# 5. Port-forward
kubectl -n llm-demo port-forward svc/load-generator 8080:8080 &
kubectl -n llm-demo port-forward svc/vllm 8000:8000 &
```

## 🎬 Run the Demo

```bash
# Phase 1: Healthy baseline (5 short requests)
curl -s -X POST http://localhost:8080/baseline | jq .
# Wait 60s → Screenshot Grafana (everything green, flat)

# Phase 2: Inject noisy neighbours (3 long requests)
curl -s -X POST http://localhost:8080/noisy | jq .
# Wait 90s → Screenshot Grafana (TTFT 5×, ITL 3×, KV cache 87%, queue still 0)

# Phase 3: Stop and recover
curl -s -X POST http://localhost:8080/stop | jq .
```

## 📊 The Six Queries

| Signal | PromQL | What It Tells You |
|--------|--------|-------------------|
| TTFT p99 | `histogram_quantile(0.99, rate(vllm:time_to_first_token_seconds_bucket[5m]))` | Did they get a seat? |
| **ITL p99** | `histogram_quantile(0.99, rate(vllm:inter_token_latency_seconds_bucket[5m]))` | **How the seat feels — THE noisy neighbour signal** |
| KV Cache | `vllm:kv_cache_usage_perc` | How full is the luggage rack? (>85% = danger) |
| Prefix Hit Rate | `rate(vllm:prefix_cache_hits[5m]) / rate(vllm:prefix_cache_queries[5m])` | Are we re-reading what we already read? |
| Batch Size | `vllm:num_requests_running` | How crowded is the table? |
| Tensor Core | `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Is the GPU computing or waiting? |

## 🚨 Three Alerts That Work

| Alert | Threshold | Action |
|-------|-----------|--------|
| KV Cache | > 90% for 2m | Preemptions imminent → cap batch size |
| TTFT p99 | > 2s for 5m | Users staring at spinner → scale or shed load |
| Queue Depth | > 0 for 3m | Real capacity limit → scale out |

## 🔧 Mitigations

1. **Cap batch size:** `--max-num-seqs 16` (default is 256!)
2. **Route by length:** Short requests (<256 tokens) get their own pool
3. **Prefix caching:** `--enable-prefix-caching` — 30-50% memory savings
4. **Scale on queue:** `vllm:num_requests_waiting > 0` for 3m, not GPU %

## 🎨 View the Slides

```bash
# Just open in your browser
open slides.html
```

The presentation is a self-contained reveal.js HTML file — no build step needed. Press `S` for speaker notes.

## 🙏 Credits

- **Animations:** [James Phoenix / understandingdata.com](https://understandingdata.com/ai-engineering-visualised/) — KV cache, prefill/decode, and tokenization visualizations
- **PagedAttention:** [Kwon et al., 2023](https://arxiv.org/abs/2309.06180) — vLLM: Efficient Memory Management for Large Language Model Serving
- **Continuous Batching:** [Yu et al., 2022](https://arxiv.org/abs/2206.00364) — Orca: A Distributed Serving System for Transformer-Based Generative Models
- **Serving Fairness:** [Cohere, 2024](https://cohere.com/blog/serving-fairness) — Fair scheduling for multi-tenant LLM serving

## 📄 License

MIT

---

*"Next time your LLM p99 spikes, don't ask 'which request is slow?' Ask: 'who else is in the batch?'"*
