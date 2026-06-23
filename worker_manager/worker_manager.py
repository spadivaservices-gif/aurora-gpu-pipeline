"""
Worker Manager - Manages RunPod Workers for Aurora GPU Pipeline
Handles job distribution, monitoring, and failover
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional
import aiohttp
import os
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerType(Enum):
    COMFYUI = "comfyui"
    KLING_VIDEO = "kling_video"
    LIP_SYNC = "lip_sync"
    MOTION_TRANSFER = "motion_transfer"
    UTILITY = "utility"


class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WorkerConfig:
    worker_id: str
    endpoint: str
    api_key: str
    worker_type: WorkerType
    gpu_type: str
    max_concurrent_jobs: int = 5
    health_check_interval: int = 30
    timeout: int = 3600


@dataclass
class Job:
    job_id: str
    worker_type: WorkerType
    payload: Dict
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict] = None
    error: Optional[str] = None


class WorkerManager:
    """Manages multiple RunPod workers with failover and load balancing"""

    def __init__(self, config_file: str = ".env"):
        self.workers: Dict[str, WorkerConfig] = {}
        self.job_queue: List[Job] = []
        self.active_jobs: Dict[str, Job] = {}
        self.worker_health: Dict[str, bool] = {}
        self.load_config(config_file)

    def load_config(self, config_file: str):
        """Load worker configuration from environment"""
        if os.getenv("COMFYUI_WORKER_ENDPOINT"):
            self.add_worker(
                WorkerConfig(
                    worker_id="comfyui-1",
                    endpoint=os.getenv("COMFYUI_WORKER_ENDPOINT"),
                    api_key=os.getenv("RUNPOD_API_KEY"),
                    worker_type=WorkerType.COMFYUI,
                    gpu_type=os.getenv("COMFYUI_GPU_TYPE", "RTX4090"),
                    max_concurrent_jobs=int(os.getenv("COMFYUI_MAX_JOBS", 5))
                )
            )

        if os.getenv("KLING_WORKER_ENDPOINT"):
            self.add_worker(
                WorkerConfig(
                    worker_id="kling-1",
                    endpoint=os.getenv("KLING_WORKER_ENDPOINT"),
                    api_key=os.getenv("RUNPOD_API_KEY"),
                    worker_type=WorkerType.KLING_VIDEO,
                    gpu_type=os.getenv("KLING_GPU_TYPE", "A40"),
                    max_concurrent_jobs=int(os.getenv("KLING_MAX_JOBS", 3))
                )
            )

        if os.getenv("LIPSYNC_WORKER_ENDPOINT"):
            self.add_worker(
                WorkerConfig(
                    worker_id="lipsync-1",
                    endpoint=os.getenv("LIPSYNC_WORKER_ENDPOINT"),
                    api_key=os.getenv("RUNPOD_API_KEY"),
                    worker_type=WorkerType.LIP_SYNC,
                    gpu_type=os.getenv("LIPSYNC_GPU_TYPE", "RTX4080"),
                    max_concurrent_jobs=int(os.getenv("LIPSYNC_MAX_JOBS", 4))
                )
            )

        if os.getenv("MOTION_WORKER_ENDPOINT"):
            self.add_worker(
                WorkerConfig(
                    worker_id="motion-1",
                    endpoint=os.getenv("MOTION_WORKER_ENDPOINT"),
                    api_key=os.getenv("RUNPOD_API_KEY"),
                    worker_type=WorkerType.MOTION_TRANSFER,
                    gpu_type=os.getenv("MOTION_GPU_TYPE", "RTX4080"),
                    max_concurrent_jobs=int(os.getenv("MOTION_MAX_JOBS", 4))
                )
            )

    def add_worker(self, config: WorkerConfig):
        """Add a worker to the pool"""
        self.workers[config.worker_id] = config
        self.worker_health[config.worker_id] = True
        logger.info(f"Added worker: {config.worker_id} ({config.worker_type.value})")

    async def submit_job(self, worker_type: WorkerType, payload: Dict) -> str:
        """Submit a job to the worker queue"""
        job = Job(
            job_id=f"job-{datetime.now().timestamp()}",
            worker_type=worker_type,
            payload=payload
        )
        self.job_queue.append(job)
        logger.info(f"Job queued: {job.job_id} for {worker_type.value}")
        return job.job_id

    async def process_jobs(self):
        """Process queued jobs with worker assignment and failover"""
        while True:
            if not self.job_queue:
                await asyncio.sleep(1)
                continue

            job = self.job_queue.pop(0)
            available_workers = self._get_workers_by_type(job.worker_type)
            
            if not available_workers:
                logger.error(f"No workers available for {job.worker_type.value}")
                job.status = JobStatus.FAILED
                job.error = "No available workers"
                self.active_jobs[job.job_id] = job
                continue

            success = False
            for worker_id in available_workers:
                try:
                    job.status = JobStatus.PROCESSING
                    job.started_at = datetime.now()
                    self.active_jobs[job.job_id] = job
                    
                    result = await self._send_to_worker(worker_id, job)
                    
                    job.status = JobStatus.COMPLETED
                    job.result = result
                    job.completed_at = datetime.now()
                    logger.info(f"Job completed: {job.job_id}")
                    success = True
                    break
                    
                except Exception as e:
                    logger.warning(f"Worker {worker_id} failed: {str(e)}")
                    job.retry_count += 1
                    
                    if job.retry_count < job.max_retries:
                        job.status = JobStatus.RETRYING
                        self.job_queue.append(job)
                        break
                    else:
                        job.status = JobStatus.FAILED
                        job.error = str(e)
                        job.completed_at = datetime.now()

            await asyncio.sleep(0.1)

    def _get_workers_by_type(self, worker_type: WorkerType) -> List[str]:
        """Get all healthy workers of a specific type"""
        return [
            worker_id for worker_id, config in self.workers.items()
            if config.worker_type == worker_type and self.worker_health.get(worker_id, False)
        ]

    async def _send_to_worker(self, worker_id: str, job: Job) -> Dict:
        """Send job to a specific worker via RunPod API"""
        config = self.workers[worker_id]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.endpoint}/run",
                json={"input": job.payload},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=config.timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Worker returned status {response.status}")

    async def health_check(self):
        """Periodic health check for all workers"""
        while True:
            for worker_id, config in self.workers.items():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{config.endpoint}/health",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            self.worker_health[worker_id] = response.status == 200
                except Exception as e:
                    logger.warning(f"Health check failed for {worker_id}: {str(e)}")
                    self.worker_health[worker_id] = False

            await asyncio.sleep(30)

    def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get status of a job"""
        return self.active_jobs.get(job_id)

    def get_stats(self) -> Dict:
        """Get manager statistics"""
        return {
            "total_workers": len(self.workers),
            "healthy_workers": sum(1 for h in self.worker_health.values() if h),
            "queued_jobs": len(self.job_queue),
            "active_jobs": len(self.active_jobs),
            "workers": {
                worker_id: {
                    "type": config.worker_type.value,
                    "gpu": config.gpu_type,
                    "healthy": self.worker_health.get(worker_id, False)
                }
                for worker_id, config in self.workers.items()
            }
        }


async def main():
    """Initialize and run worker manager"""
    manager = WorkerManager()
    
    asyncio.create_task(manager.process_jobs())
    asyncio.create_task(manager.health_check())
    
    logger.info(f"Worker Manager started with {len(manager.workers)} workers")
    logger.info(f"Stats: {manager.get_stats()}")
    
    await asyncio.sleep(float('inf'))


if __name__ == "__main__":
    asyncio.run(main())
