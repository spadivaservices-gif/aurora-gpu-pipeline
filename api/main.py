"""
FastAPI endpoints for Aurora GPU Pipeline
Integrates with RunPod Pods, Workers, and Serverless
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
from datetime import datetime
from worker_manager.worker_manager import WorkerManager, WorkerType, Job

app = FastAPI(title="Aurora GPU Pipeline API")
worker_manager = WorkerManager()


# Pydantic Models
class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    steps: int = 20
    cfg_scale: float = 7.5
    width: int = 768
    height: int = 768
    batch_size: int = 1


class VideoGenerationRequest(BaseModel):
    prompt: str
    duration: int = 10
    fps: int = 24
    resolution: str = "1080p"


class LipSyncRequest(BaseModel):
    video_url: str
    audio_url: str
    face_index: int = 0


class MotionTransferRequest(BaseModel):
    video_url: str
    pose_video_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


# Image Generation
@app.post("/api/v1/image-gen")
async def generate_image(request: ImageGenerationRequest, background_tasks: BackgroundTasks):
    """Generate image using ComfyUI worker"""
    try:
        payload = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "steps": request.steps,
            "cfg_scale": request.cfg_scale,
            "width": request.width,
            "height": request.height,
            "batch_size": request.batch_size
        }
        
        job_id = await worker_manager.submit_job(WorkerType.COMFYUI, payload)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Image generation job submitted",
            "poll_url": f"/api/v1/job/{job_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Video Generation (Kling)
@app.post("/api/v1/video-gen")
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """Generate video using Kling worker"""
    try:
        payload = {
            "prompt": request.prompt,
            "duration": request.duration,
            "fps": request.fps,
            "resolution": request.resolution
        }
        
        job_id = await worker_manager.submit_job(WorkerType.KLING_VIDEO, payload)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Video generation job submitted",
            "poll_url": f"/api/v1/job/{job_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lip Sync
@app.post("/api/v1/lip-sync")
async def apply_lip_sync(request: LipSyncRequest, background_tasks: BackgroundTasks):
    """Apply lip sync to video using Lip Sync worker"""
    try:
        payload = {
            "video_url": request.video_url,
            "audio_url": request.audio_url,
            "face_index": request.face_index
        }
        
        job_id = await worker_manager.submit_job(WorkerType.LIP_SYNC, payload)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Lip sync job submitted",
            "poll_url": f"/api/v1/job/{job_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Motion Transfer
@app.post("/api/v1/motion-transfer")
async def transfer_motion(request: MotionTransferRequest, background_tasks: BackgroundTasks):
    """Transfer motion from pose video using Motion Transfer worker"""
    try:
        payload = {
            "video_url": request.video_url,
            "pose_video_url": request.pose_video_url
        }
        
        job_id = await worker_manager.submit_job(WorkerType.MOTION_TRANSFER, payload)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Motion transfer job submitted",
            "poll_url": f"/api/v1/job/{job_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Job Status
@app.get("/api/v1/job/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and results"""
    job = worker_manager.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error=job.error
    )


# Worker Stats
@app.get("/api/v1/stats")
async def get_stats():
    """Get worker manager statistics"""
    return worker_manager.get_stats()


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    stats = worker_manager.get_stats()
    return {
        "status": "healthy" if stats["healthy_workers"] > 0 else "degraded",
        "stats": stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
