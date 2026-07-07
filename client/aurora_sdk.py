"""
Aurora GPU Pipeline SDK - Python Client
Easy integration for image, video, lip sync, and motion generation
"""

import requests
import time
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class JobResult:
    job_id: str
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None


class AuroraSDK:
    """SDK for Aurora GPU Pipeline"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        steps: int = 20,
        cfg_scale: float = 7.5,
        width: int = 768,
        height: int = 768,
        wait: bool = False,
        timeout: int = 3600
    ) -> JobResult:
        """Generate an image from text"""
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height
        }

        response = requests.post(
            f"{self.base_url}/api/v1/image-gen",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        job_id = data["job_id"]

        if wait:
            return self.wait_for_job(job_id, timeout=timeout)
        return JobResult(job_id=job_id, status="queued")

    def generate_video(
        self,
        prompt: str,
        duration: int = 10,
        fps: int = 24,
        resolution: str = "1080p",
        wait: bool = False,
        timeout: int = 3600
    ) -> JobResult:
        """Generate a video from text"""
        payload = {
            "prompt": prompt,
            "duration": duration,
            "fps": fps,
            "resolution": resolution
        }

        response = requests.post(
            f"{self.base_url}/api/v1/video-gen",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        job_id = data["job_id"]

        if wait:
            return self.wait_for_job(job_id, timeout=timeout)
        return JobResult(job_id=job_id, status="queued")

    def apply_lip_sync(
        self,
        video_url: str,
        audio_url: str,
        face_index: int = 0,
        wait: bool = False,
        timeout: int = 3600
    ) -> JobResult:
        """Apply lip sync to a video"""
        payload = {
            "video_url": video_url,
            "audio_url": audio_url,
            "face_index": face_index
        }

        response = requests.post(
            f"{self.base_url}/api/v1/lip-sync",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        job_id = data["job_id"]

        if wait:
            return self.wait_for_job(job_id, timeout=timeout)
        return JobResult(job_id=job_id, status="queued")

    def transfer_motion(
        self,
        video_url: str,
        pose_video_url: str,
        wait: bool = False,
        timeout: int = 3600
    ) -> JobResult:
        """Transfer motion from pose video"""
        payload = {
            "video_url": video_url,
            "pose_video_url": pose_video_url
        }

        response = requests.post(
            f"{self.base_url}/api/v1/motion-transfer",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        job_id = data["job_id"]

        if wait:
            return self.wait_for_job(job_id, timeout=timeout)
        return JobResult(job_id=job_id, status="queued")

    def get_job_status(self, job_id: str) -> JobResult:
        """Get status of a job"""
        response = requests.get(
            f"{self.base_url}/api/v1/job/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()

        return JobResult(
            job_id=data["job_id"],
            status=data["status"],
            result=data.get("result"),
            error=data.get("error")
        )

    def wait_for_job(self, job_id: str, timeout: int = 3600, poll_interval: int = 5) -> JobResult:
        """Wait for a job to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            job = self.get_job_status(job_id)

            if job.status == "completed":
                return job
            elif job.status == "failed":
                return job

            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} timed out after {timeout} seconds")

    def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        response = requests.get(
            f"{self.base_url}/api/v1/stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> bool:
        """Check if pipeline is healthy"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# Example usage
if __name__ == "__main__":
    sdk = AuroraSDK("http://localhost:8000")

    # Generate image
    print("Generating image...")
    image_job = sdk.generate_image(
        prompt="a beautiful sunset over mountains",
        wait=True,
        timeout=300
    )
    print(f"Image job: {image_job}")

    # Generate video
    print("\nGenerating video...")
    video_job = sdk.generate_video(
        prompt="cinematic shot of a city at night",
        duration=10
    )
    print(f"Video job ID: {video_job.job_id}")
    print(f"Check status: {sdk.get_job_status(video_job.job_id)}")
