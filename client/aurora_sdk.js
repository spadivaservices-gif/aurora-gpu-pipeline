"""
Aurora GPU Pipeline SDK - JavaScript/Node.js Client
Easy integration for image, video, lip sync, and motion generation
"""

class AuroraSDK {
  constructor(baseUrl = "http://localhost:8000", apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.headers = { "Content-Type": "application/json" };
    if (apiKey) {
      this.headers["Authorization"] = `Bearer ${apiKey}`;
    }
  }

  async generateImage({
    prompt,
    negativePrompt = "",
    steps = 20,
    cfgScale = 7.5,
    width = 768,
    height = 768,
    wait = false,
    timeout = 3600
  }) {
    const payload = {
      prompt,
      negative_prompt: negativePrompt,
      steps,
      cfg_scale: cfgScale,
      width,
      height
    };

    const response = await fetch(`${this.baseUrl}/api/v1/image-gen`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    const jobId = data.job_id;

    if (wait) {
      return this.waitForJob(jobId, timeout);
    }
    return { job_id: jobId, status: "queued" };
  }

  async generateVideo({
    prompt,
    duration = 10,
    fps = 24,
    resolution = "1080p",
    wait = false,
    timeout = 3600
  }) {
    const payload = {
      prompt,
      duration,
      fps,
      resolution
    };

    const response = await fetch(`${this.baseUrl}/api/v1/video-gen`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    const jobId = data.job_id;

    if (wait) {
      return this.waitForJob(jobId, timeout);
    }
    return { job_id: jobId, status: "queued" };
  }

  async applyLipSync({
    videoUrl,
    audioUrl,
    faceIndex = 0,
    wait = false,
    timeout = 3600
  }) {
    const payload = {
      video_url: videoUrl,
      audio_url: audioUrl,
      face_index: faceIndex
    };

    const response = await fetch(`${this.baseUrl}/api/v1/lip-sync`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    const jobId = data.job_id;

    if (wait) {
      return this.waitForJob(jobId, timeout);
    }
    return { job_id: jobId, status: "queued" };
  }

  async transferMotion({
    videoUrl,
    poseVideoUrl,
    wait = false,
    timeout = 3600
  }) {
    const payload = {
      video_url: videoUrl,
      pose_video_url: poseVideoUrl
    };

    const response = await fetch(`${this.baseUrl}/api/v1/motion-transfer`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    const jobId = data.job_id;

    if (wait) {
      return this.waitForJob(jobId, timeout);
    }
    return { job_id: jobId, status: "queued" };
  }

  async getJobStatus(jobId) {
    const response = await fetch(`${this.baseUrl}/api/v1/job/${jobId}`, {
      headers: this.headers
    });
    return await response.json();
  }

  async waitForJob(jobId, timeout = 3600, pollInterval = 5000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout * 1000) {
      const job = await this.getJobStatus(jobId);

      if (job.status === "completed" || job.status === "failed") {
        return job;
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Job ${jobId} timed out after ${timeout} seconds`);
  }

  async getStats() {
    const response = await fetch(`${this.baseUrl}/api/v1/stats`, {
      headers: this.headers
    });
    return await response.json();
  }

  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        headers: this.headers
      });
      return response.status === 200;
    } catch (e) {
      return false;
    }
  }
}

module.exports = AuroraSDK;
