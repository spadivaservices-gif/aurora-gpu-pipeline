# Aurora GPU Pipeline - Integration Guide

## For Your Aurora-Prime Replit App

This guide shows how to integrate the GPU pipeline into your existing Aurora app.

## Step 1: Add SDK to Your Project

### If using Python (Flask/FastAPI):
```python
# app.py or main.py
from client.aurora_sdk import AuroraSDK

sdk = AuroraSDK("http://localhost:8000")  # Or RunPod URL

@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    prompt = request.json.get("prompt")
    
    result = sdk.generate_image(
        prompt=prompt,
        wait=False  # Return job_id immediately
    )
    
    return {"job_id": result.job_id}

@app.route("/api/job-status/<job_id>", methods=["GET"])
def job_status(job_id):
    status = sdk.get_job_status(job_id)
    return status.__dict__
```

### If using Node.js (Express):
```javascript
// server.js or api.js
const AuroraSDK = require('./client/aurora_sdk.js');
const sdk = new AuroraSDK('http://localhost:8000');

app.post('/api/generate-image', async (req, res) => {
  const { prompt } = req.body;
  
  const result = await sdk.generateImage({
    prompt,
    wait: false
  });
  
  res.json({ job_id: result.job_id });
});

app.get('/api/job-status/:jobId', async (req, res) => {
  const status = await sdk.getJobStatus(req.params.jobId);
  res.json(status);
});
```

## Step 2: Frontend Integration (React)

```javascript
// GenerateImage.jsx
import { useState } from 'react';

const GenerateImage = () => {
  const [prompt, setPrompt] = useState('');
  const [jobId, setJobId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    
    // Call your backend
    const res = await fetch('/api/generate-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    
    const { job_id } = await res.json();
    setJobId(job_id);
    
    // Poll for results
    const pollResult = async () => {
      const statusRes = await fetch(`/api/job-status/${job_id}`);
      const status = await statusRes.json();
      
      if (status.status === 'completed') {
        setResult(status.result);
        setLoading(false);
      } else if (status.status === 'failed') {
        console.error('Job failed:', status.error);
        setLoading(false);
      } else {
        // Poll again in 2 seconds
        setTimeout(pollResult, 2000);
      }
    };
    
    pollResult();
  };

  return (
    <div>
      <input
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter prompt..."
      />
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate'}
      </button>
      {result && <img src={result} alt="Generated" />}
    </div>
  );
};
```

## Step 3: WebSocket for Real-time Updates (Optional)

```javascript
// socket-client.js
const socket = io('http://localhost:8000');

socket.on('job-update', (data) => {
  console.log(`Job ${data.job_id}: ${data.status}`);
  
  if (data.status === 'completed') {
    // Update UI with result
  }
});

// Subscribe to job
socket.emit('subscribe-job', { job_id: 'your-job-id' });
```

## Step 4: Environment Variables

```bash
# .env in your Aurora app
GPU_PIPELINE_URL=http://localhost:8000
# OR for RunPod:
GPU_PIPELINE_URL=https://your-pod-id.runpod.io
GPU_API_KEY=your_api_key (if needed)
```

## Step 5: Error Handling

```javascript
const handleGenerateWithErrors = async () => {
  try {
    const res = await fetch('/api/generate-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    const { job_id, error } = await res.json();
    
    if (error) {
      console.error('API error:', error);
      return;
    }
    
    // Continue with job polling...
  } catch (error) {
    console.error('Failed to generate:', error);
    // Show error to user
  }
};
```

## Architecture

```
┌──────────────────────────────┐
│  Aurora App                  │
│  (Your Replit)               │
└──────────────┬────────────────┘
               │ API calls
               ▼
┌──────────────────────────────┐
│ Your Backend                 │
│ (Python/Node)                │
└──────────────┬────────────────┘
               │ SDK calls
               ▼
┌──────────────────────────────┐
│  GPU Pipeline                │
│  (FastAPI)                   │
└──────────────┬────────────────┘
               │
    ┌──────────┴───────────────────────────────────────────┐
    │                                                       │
    ▼                                                       ▼
┌──────────────────────────────┐  ┌──────────────────────────────────┐
│ RunPod Pod                   │  │ RunPod Workers                   │
│ (Primary)                    │  │ (Failover)                       │
└──────────────────────────────┘  └──────────────────────────────────┘
```

## Complete Example: Image Generation Flow

1. **Frontend:** User enters prompt and clicks "Generate"
2. **Frontend:** Sends prompt to backend: `POST /api/generate-image`
3. **Backend:** Calls GPU Pipeline SDK: `sdk.generate_image(prompt)`
4. **GPU Pipeline:** Queues job, returns `job_id`
5. **Backend:** Returns `job_id` to frontend
6. **Frontend:** Polls `/api/job-status/{job_id}` every 2 seconds
7. **GPU Pipeline:** Processes image on GPU (RunPod Pod or Workers)
8. **Frontend:** When status = "completed", display result image

## Testing

```bash
# Test health
curl http://localhost:8000/health

# Test image generation
curl -X POST http://localhost:8000/api/v1/image-gen \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Check job status
curl http://localhost:8000/api/v1/job/job-xyz
```

## Production Deployment

### On RunPod:
1. Deploy GPU Pipeline to RunPod Pod
2. Update `GPU_PIPELINE_URL` in Aurora app to RunPod URL
3. Deploy Aurora app to your hosting (Replit, Vercel, Heroku, etc.)

### Environment-specific URLs:
```javascript
const getPipelineUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    return process.env.GPU_PIPELINE_URL; // RunPod URL
  } else {
    return 'http://localhost:8000'; // Local development
  }
};
```

## Rate Limiting & Queuing

The GPU pipeline automatically queues jobs. To add rate limiting on your end:

```javascript
const jobQueue = [];
const maxConcurrent = 5;
let activeJobs = 0;

const queueJob = async (jobFn) => {
  jobQueue.push(jobFn);
  processQueue();
};

const processQueue = async () => {
  while (jobQueue.length > 0 && activeJobs < maxConcurrent) {
    activeJobs++;
    const job = jobQueue.shift();
    
    try {
      await job();
    } finally {
      activeJobs--;
      processQueue();
    }
  }
};
```

## Next Steps

1. ✅ Copy SDK to your Aurora project
2. ✅ Add GPU Pipeline backend API
3. ✅ Create frontend components
4. ✅ Test locally
5. ✅ Deploy GPU Pipeline to RunPod
6. ✅ Update API URLs for production
7. ✅ Deploy Aurora app

You're ready to go! 🚀
