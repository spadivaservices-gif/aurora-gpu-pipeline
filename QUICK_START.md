# Aurora GPU Pipeline - Quick Start Guide

## Installation

### 1. Extract Files
```bash
unzip aurora-gpu-pipeline.zip
cd aurora-gpu-pipeline
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your RunPod API key
```

## Quick Start

### Option 1: Local Development (Fastest)

```bash
# Terminal 1: Start API Server
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Start Worker Manager
python -m worker_manager.worker_manager
```

### Option 2: Deploy to RunPod

```bash
export RUNPOD_API_KEY="your_api_key"
python scripts/deploy.py --mode all
```

## Integration Examples

### Python
```python
from client.aurora_sdk import AuroraSDK

sdk = AuroraSDK("http://localhost:8000")

# Generate image
image = sdk.generate_image(
    prompt="a beautiful sunset",
    wait=True
)
print(f"Image result: {image.result}")

# Generate video
video = sdk.generate_video(
    prompt="cinematic scene",
    duration=10
)
print(f"Video job: {video.job_id}")
status = sdk.wait_for_job(video.job_id)
print(f"Status: {status}")
```

### JavaScript/Node.js
```javascript
const AuroraSDK = require('./client/aurora_sdk.js');

const sdk = new AuroraSDK('http://localhost:8000');

// Generate image
const image = await sdk.generateImage({
  prompt: 'a beautiful sunset',
  wait: true
});
console.log('Image:', image);

// Generate video
const video = await sdk.generateVideo({
  prompt: 'cinematic scene',
  duration: 10
});
console.log('Video job:', video.job_id);
```

### cURL
```bash
# Generate image
curl -X POST http://localhost:8000/api/v1/image-gen \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset"}'

# Check job status
curl http://localhost:8000/api/v1/job/{job_id}

# Get stats
curl http://localhost:8000/api/v1/stats
```

## API Endpoints

### Image Generation
**POST** `/api/v1/image-gen`
```json
{
  "prompt": "string",
  "negative_prompt": "string (optional)",
  "steps": 20,
  "cfg_scale": 7.5,
  "width": 768,
  "height": 768
}
```

### Video Generation
**POST** `/api/v1/video-gen`
```json
{
  "prompt": "string",
  "duration": 10,
  "fps": 24,
  "resolution": "1080p"
}
```

### Lip Sync
**POST** `/api/v1/lip-sync`
```json
{
  "video_url": "string",
  "audio_url": "string",
  "face_index": 0
}
```

### Motion Transfer
**POST** `/api/v1/motion-transfer`
```json
{
  "video_url": "string",
  "pose_video_url": "string"
}
```

### Job Status
**GET** `/api/v1/job/{job_id}`

### Health Check
**GET** `/health`

### Statistics
**GET** `/api/v1/stats`

## Docker Deployment

```bash
# Build images
docker build -f docker/Dockerfile.comfyui -t aurora-comfyui .
docker build -f docker/Dockerfile.kling -t aurora-kling .

# Run containers
docker run --gpus all -p 8000:8000 aurora-comfyui
```

## Jupyter Notebooks

Interactive notebooks for testing:

```bash
jupyter notebook notebooks/
```

- `notebooks/image_generation.ipynb` - Image gen examples
- `notebooks/video_generation.ipynb` - Video gen examples

## Troubleshooting

### Workers not starting
```bash
# Check worker health
curl http://localhost:8000/api/v1/stats
```

### Jobs failing
```bash
# Check job status
curl http://localhost:8000/api/v1/job/{job_id}
```

### GPU not detected
```bash
# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

## Support

For issues:
1. Check logs: `logs/aurora.log`
2. View stats: `http://localhost:8000/api/v1/stats`
3. Open GitHub issue: https://github.com/spadivaservices-gif/aurora-gpu-pipeline/issues
