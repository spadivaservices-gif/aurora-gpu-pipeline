# Aurora GPU Pipeline

Unified GPU infrastructure for Aurora app - video generation, image synthesis, lip sync, and motion transfer using RunPod with ComfyUI, Stable Diffusion, Kling, and Jupyter.

## Features

- **Multi-Model Support**: ComfyUI, Stable Diffusion, Kling video gen, motion control
- **RunPod Integration**: Both Pods (dedicated) and Serverless (auto-scaling)
- **Workers**: Persistent background workers for batch processing
- **GPU Failover**: Automatic fallback to secondary providers if primary fails
- **Jupyter Notebooks**: Interactive GPU compute with persistent kernels
- **Lip Sync & Motion Transfer**: Real-time facial animation
- **REST API**: Easy integration with Aurora app
- **Cost Optimization**: Auto-scale serverless + dedicated pod backup

## Architecture

```
Aurora App
    ↓
API Gateway (FastAPI)
    ↓
RunPod Orchestrator
├── Primary: RunPod Pod (Dedicated GPU)
├── Workers: Persistent Background Jobs
│   ├── ComfyUI Worker (RTX4090)
│   ├── Kling Video Worker (A40)
│   ├── Lip Sync Worker (RTX4080)
│   └── Motion Transfer Worker (RTX4080)
├── Fallback 1: RunPod Serverless (Auto-scaling)
├── Fallback 2: Jupyter Notebook GPU Session
└── Fallback 3: External provider (optional)
```

## Components

### 1. RunPod Pod (Primary)
- **GPU**: RTX 4090 (24GB) or A40 (48GB)
- **Purpose**: Immediate synchronous requests
- **Cost**: $0.45/hr for RTX 4090
- **Latency**: Lowest (~5-10s start)

### 2. RunPod Workers
Persistent background workers for batch processing:

- **ComfyUI Worker** - Image generation, Stable Diffusion, upscaling
- **Kling Video Worker** - Text-to-video generation
- **Lip Sync Worker** - Wav2Lip, SyncNet facial animation
- **Motion Transfer Worker** - Pose transfer, DWPose, OpenPose

### 3. RunPod Serverless
- **Purpose**: Auto-scaling fallback for burst traffic
- **Cost**: Pay-per-request (~$0.0001/ms)
- **Timeout**: 900 seconds max
- **Latency**: 30s+ cold start

### 4. Jupyter Notebook
- **GPU**: RTX 4070 (12GB)
- **Purpose**: Interactive development & fallback compute
- **Port**: 8888

## Quick Start

### 1. Prerequisites
```bash
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
# Edit .env with your RunPod API key and endpoint URLs
```

### 3. Deploy

**Deploy everything:**
```bash
python scripts/deploy.py --mode all
```

**Deploy specific components:**
```bash
python scripts/deploy.py --mode pod        # Dedicated GPU
python scripts/deploy.py --mode workers    # Background workers
python scripts/deploy.py --mode serverless # Auto-scaling
python scripts/deploy.py --mode jupyter    # Notebook
```

### 4. Start API Server
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test Endpoints
```bash
# Generate image
curl -X POST http://localhost:8000/api/v1/image-gen \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful landscape"}'

# Generate video
curl -X POST http://localhost:8000/api/v1/video-gen \
  -H "Content-Type: application/json" \
  -d '{"prompt": "cinematic shot of a city at night", "duration": 10}'

# Check job status
curl http://localhost:8000/api/v1/job/{job_id}

# Get stats
curl http://localhost:8000/api/v1/stats
```

## API Reference

### Image Generation
```bash
POST /api/v1/image-gen
{
  "prompt": "string",
  "negative_prompt": "string",
  "steps": 20,
  "cfg_scale": 7.5,
  "width": 768,
  "height": 768,
  "batch_size": 1
}
```

### Video Generation (Kling)
```bash
POST /api/v1/video-gen
{
  "prompt": "string",
  "duration": 10,
  "fps": 24,
  "resolution": "1080p"
}
```

### Lip Sync
```bash
POST /api/v1/lip-sync
{
  "video_url": "string",
  "audio_url": "string",
  "face_index": 0
}
```

### Motion Transfer
```bash
POST /api/v1/motion-transfer
{
  "video_url": "string",
  "pose_video_url": "string"
}
```

### Job Status
```bash
GET /api/v1/job/{job_id}
```

### Statistics
```bash
GET /api/v1/stats
```

## GPU Requirements

**Recommended Setup:**
- **Pod**: RTX 4090 (24GB) - Primary compute
- **ComfyUI Worker**: RTX 4090 (24GB) - Image generation
- **Kling Worker**: A40 (48GB) - Video generation
- **Lip Sync Worker**: RTX 4080 (12GB) - Facial animation
- **Motion Worker**: RTX 4080 (12GB) - Pose transfer
- **Jupyter**: RTX 4070 (12GB) - Interactive dev

**Cost Estimation:**
```
Pod:           $0.45/hr (RTX4090)
ComfyUI Worker: $0.45/hr (RTX4090)
Kling Worker:   $0.35/hr (A40)
LipSync Worker: $0.28/hr (RTX4080)
Motion Worker:  $0.28/hr (RTX4080)
Jupyter:        $0.22/hr (RTX4070)
───────────────────────
Total (all):    $2.03/hr
Total (minimal): $0.45/hr (pod only)
```

## Failover Strategy

If a component fails, automatic fallback occurs:

1. **Pod fails** → Use Workers
2. **Workers fail** → Use Serverless
3. **Serverless fails** → Use Jupyter session
4. **All fail** → Return error with queue position

Each component has health checks every 30 seconds.

## Worker Management

```python
from worker_manager.worker_manager import WorkerManager, WorkerType

manager = WorkerManager()

# Submit job
job_id = await manager.submit_job(
    WorkerType.COMFYUI,
    {"prompt": "beautiful sunset"}
)

# Check status
job = manager.get_job_status(job_id)

# Get stats
stats = manager.get_stats()
print(f"Healthy workers: {stats['healthy_workers']}")
print(f"Queued jobs: {stats['queued_jobs']}")
```

## Documentation

- [RunPod Setup Guide](docs/runpod-setup.md)
- [Worker Configuration](docs/worker-configuration.md)
- [ComfyUI Workflows](docs/comfyui-guide.md)
- [API Reference](docs/api.md)
- [Failover Logic](docs/failover.md)
- [Jupyter Setup](docs/jupyter-setup.md)
- [Queue System](docs/queue-system.md)

## Troubleshooting

### Pod not responding
```bash
curl https://your-pod-id.runpod.io/health
```

### Check worker health
```bash
curl http://localhost:8000/api/v1/stats
```

### View logs
```bash
tail -f logs/aurora.log
```

## Support

For issues:
1. Check logs: `logs/aurora.log`
2. Check RunPod dashboard: https://www.runpod.io/console
3. Open GitHub issue: [issues](https://github.com/spadivaservices-gif/aurora-gpu-pipeline/issues)

## License

MIT
