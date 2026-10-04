# LLM Inference: Noisy Neighbour Observatory -- Demo

A self-contained demo stack that visualises the **noisy-neighbour effect** in
batched LLM inference. It runs vLLM serving Llama 3.2 3B, scrapes GPU and
inference metrics with DCGM Exporter and Prometheus, and renders them in a
pre-built Grafana dashboard -- all in Docker Compose.

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker Engine 24+ | With Compose v2 (`docker compose`) |
| NVIDIA GPU | Tested on A100/A10G/L4; any Ampere+ GPU with >= 8 GB VRAM |
| NVIDIA Driver 535+ | `nvidia-smi` should show the driver version |
| nvidia-container-toolkit | [Install guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) |
| HuggingFace token | Required for gated models -- get one at https://huggingface.co/settings/tokens |

Verify GPU access in Docker before proceeding:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

## Quick Start

```bash
# 1. Clone and enter the demo directory
cd demo/

# 2. Create the environment file
cp .env.example .env

# 3. Set your HuggingFace token (required for Llama 3.2 gated access)
#    Edit .env and replace the placeholder:
#    HF_TOKEN=hf_your_actual_token_here

# 4. Start the stack
docker compose up -d

# 5. Wait for vLLM to finish loading the model (watch for "healthy")
docker compose logs -f vllm
#    This takes 2-5 minutes on first run (model download) and ~30s after that.
#    Wait until you see: "Uvicorn running on http://0.0.0.0:8000"

# 6. Verify health
curl http://localhost:8000/health
```

## Running the Demo

The demo has three phases. Run them from a second terminal.

### Phase 1 -- Baseline (calm state)

```bash
# Start 5 lightweight workers sending short requests
curl -X POST http://localhost:8080/baseline
```

Let this run for **60 seconds**. Observe in Grafana:
- TTFT p99 is low and stable
- KV cache usage is moderate
- Batch occupancy hovers around 5
- Queue depth stays near zero

### Phase 2 -- Inject the noisy neighbour

```bash
# Start 3 heavy workers sending long-generation requests
curl -X POST http://localhost:8080/noisy
```

Let this run for **90 seconds**. Watch what happens:
- TTFT p99 spikes -- the short requests now wait longer for their first token
- KV cache usage climbs sharply toward saturation
- Batch occupancy jumps (more concurrent sequences)
- Queue depth rises as requests back up
- Tensor core activity increases

### Phase 3 -- Stop and recover

```bash
# Stop all workers
curl -X POST http://localhost:8080/stop
```

Watch the metrics return to zero. The tail-off shape tells a story about how
vLLM drains its batch.

### Check status at any time

```bash
curl http://localhost:8080/status | python3 -m json.tool
```

## Viewing Metrics

Open Grafana at **http://localhost:3000**

- Username: `admin`
- Password: `demo`

The **LLM Inference: Noisy Neighbour Observatory** dashboard is auto-loaded as
the home dashboard. It has six panels in a 3x2 grid:

| Panel | What it shows |
|---|---|
| TTFT p99 | Time to first token -- the metric users feel |
| ITL p99 | Inter-token latency -- smoothness of streaming |
| KV Cache Usage | GPU memory pressure from cached attention states |
| Batch Occupancy | Number of sequences being processed concurrently |
| Tensor Core Activity | Raw GPU compute utilisation from DCGM |
| Queue Depth | Requests waiting to enter the batch |

## Pre-Recording Tips

This demo is designed for a pre-recorded conference talk. Here is a suggested
recording workflow:

1. **Terminal recording** -- Use [asciinema](https://asciinema.org/) to record
   the curl commands and their output:
   ```bash
   asciinema rec demo-terminal.cast
   ```

2. **Dashboard recording** -- Use OBS Studio or QuickTime to screen-record the
   Grafana dashboard. Set Grafana to fullscreen (F11) and use the kiosk mode
   URL: `http://localhost:3000/d/noisy-neighbour-demo?orgId=1&kiosk`

3. **Screenshot each phase** -- Take a screenshot of the dashboard at:
   - T+60s (baseline only -- the "before")
   - T+120s (noisy neighbour active -- the "during")
   - T+210s (after stop -- the "recovery")

4. **Narration sync** -- The 5-second auto-refresh in Grafana means panels
   update smoothly for video. Align your narration to the phase transitions.

## Cleanup

```bash
# Stop and remove all containers, networks, and volumes
docker compose down -v
```

This removes the model cache volume as well. Omit `-v` to keep the downloaded
model for faster restarts.

## Troubleshooting

### GPU not detected

```
Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

The nvidia-container-toolkit is not installed or not configured. Install it and
restart Docker:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Model download is slow

The Llama 3.2 3B model is approximately 6 GB. On a slow connection, the first
start can take 15+ minutes. The model is cached in a Docker volume
(`model-cache`), so subsequent starts are fast.

If the download stalls, you can pre-pull the model:

```bash
docker compose run --rm vllm python -c \
  "from huggingface_hub import snapshot_download; snapshot_download('meta-llama/Llama-3.2-3B-Instruct')"
```

### vLLM OOM (Out of Memory)

```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

The default configuration uses 90% GPU memory. If your GPU has less than 8 GB
VRAM, reduce the allocation in `docker-compose.yml`:

```yaml
command:
  - --gpu-memory-utilization
  - "0.80"   # Lower this value
  - --max-model-len
  - "2048"   # Also reduce context length
```

### vLLM health check keeps failing

The model takes time to load. The health check has a 120-second start period
and retries 40 times. If your GPU is slow, increase `start_period` in the
`docker-compose.yml` healthcheck section.

Check logs for the actual error:

```bash
docker compose logs vllm --tail 50
```

### Grafana shows "No data"

- Verify Prometheus is scraping: visit http://localhost:9090/targets -- both
  `vllm` and `dcgm` should show as UP.
- Metrics only appear after the first request. Start the baseline workload
  first, then check the dashboard.
- If the datasource UID does not match, go to Grafana > Connections > Data
  sources > Prometheus and note the UID, then check the dashboard JSON.
