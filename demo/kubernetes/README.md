# Kubernetes Deployment — Noisy Neighbour Demo

Deploy the demo on your GPU-based K8s cluster instead of Docker Compose. More realistic for the audience, and you likely already have Prometheus + Grafana + DCGM Exporter running.

## Prerequisites

- K8s cluster with GPU nodes (NVIDIA device plugin installed)
- DCGM Exporter running as a DaemonSet (via GPU Operator or standalone)
- Prometheus (kube-prometheus-stack) scraping DCGM and ServiceMonitors
- Grafana accessible (via port-forward or ingress)
- `kubectl` configured for the target cluster
- HuggingFace token for gated Llama model

## Quick Start

```bash
# 1. Create namespace and secret
export HF_TOKEN="hf_your_token_here"
envsubst < 00-namespace.yaml | kubectl apply -f -

# 2. Deploy vLLM
kubectl apply -f 01-vllm.yaml

# 3. Wait for vLLM to load the model (~3-5 min)
kubectl -n llm-demo wait --for=condition=ready pod -l app=vllm --timeout=600s

# 4. Build and deploy load generator
#    Option A: Build locally and load into cluster
docker build -t load-generator:latest ../load-generator/
#    If using kind:
kind load docker-image load-generator:latest
#    If using a registry:
docker tag load-generator:latest <your-registry>/load-generator:latest
docker push <your-registry>/load-generator:latest
#    Update image in 02-load-generator.yaml if using a registry

kubectl apply -f 02-load-generator.yaml

# 5. Import Grafana dashboard
kubectl apply -f 03-grafana-dashboard-cm.yaml
#    If your Grafana has the dashboard sidecar (grafana_dashboard: "1" label),
#    the dashboard auto-imports. Otherwise, import the JSON manually via
#    Grafana UI → Dashboards → Import → paste the JSON from the ConfigMap.

# 6. Port-forward for demo access
kubectl -n llm-demo port-forward svc/load-generator 8080:8080 &
kubectl -n llm-demo port-forward svc/vllm 8000:8000 &
```

## Run the Demo

```bash
# Phase 1: Baseline (5 short requests)
curl -s -X POST http://localhost:8080/baseline | jq .

# Wait 60s for metrics to stabilize, then screenshot Grafana

# Phase 2: Inject noisy neighbours (3 long requests)
curl -s -X POST http://localhost:8080/noisy | jq .

# Wait 60-90s for full impact, screenshot Grafana

# Phase 3: Stop and recover
curl -s -X POST http://localhost:8080/stop | jq .

# Check stats
curl -s http://localhost:8080/status | jq .
```

## Verify Metrics Are Flowing

```bash
# vLLM metrics
curl -s http://localhost:8000/metrics | grep -E 'vllm:(time_to_first|inter_token|kv_cache|num_requests)' | head -10

# DCGM metrics (via Prometheus)
kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 &
curl -s 'http://localhost:9090/api/v1/query?query=DCGM_FI_PROF_PIPE_TENSOR_ACTIVE' | jq '.data.result[0].value'
```

## Adapting to Your Cluster

| Setting | Default | Adjust if... |
|---------|---------|-------------|
| `nvidia.com/gpu.present: "true"` nodeSelector | Standard GPU Operator label | Your GPU nodes use a different label |
| `nvidia.com/gpu` toleration | NoSchedule on GPU nodes | Your taints differ (check `kubectl describe node`) |
| `release: prometheus` label on ServiceMonitor | kube-prometheus-stack default | Your Prometheus uses a different selector |
| `grafana_dashboard: "1"` label on ConfigMap | Grafana sidecar default | Your Grafana sidecar uses a different label |
| `emptyDir` for model cache | Re-downloads on pod restart | Use a PVC for faster restarts |

## Cleanup

```bash
kubectl delete namespace llm-demo
```
