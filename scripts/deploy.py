#!/usr/bin/env python3
"""
Deployment script for Aurora GPU Pipeline
Handles Pod, Workers, Serverless, and Jupyter setup
"""

import argparse
import os
import sys
import subprocess
import json
from typing import Dict, List
import requests

class AuroraDeployer:
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY environment variable not set")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def deploy_pod(self):
        """Deploy RunPod Pod (Dedicated GPU)"""
        print("[*] Deploying RunPod Pod...")
        
        pod_config = {
            "name": "aurora-gpu-pod",
            "image_name": "nvidia/cuda:11.8.0-devel-ubuntu22.04",
            "gpu_count": 1,
            "volume_in_gb": 50,
            "container_disk_in_gb": 20,
            "min_vcpu_count": 8,
            "min_memory_in_gb": 32,
            "gpu_type_id": "RTX4090"
        }
        
        print(f"[+] Pod configuration:")
        print(json.dumps(pod_config, indent=2))
        print("[+] Deploy via RunPod console: https://www.runpod.io/console/pods")
        
        return pod_config

    def deploy_workers(self):
        """Deploy RunPod Workers"""
        print("[*] Deploying RunPod Workers...")
        
        workers = [
            {
                "name": "aurora-comfyui-worker",
                "type": "COMFYUI",
                "gpu": "RTX4090",
                "vram": "24GB"
            },
            {
                "name": "aurora-kling-worker",
                "type": "KLING",
                "gpu": "A40",
                "vram": "48GB"
            },
            {
                "name": "aurora-lipsync-worker",
                "type": "LIPSYNC",
                "gpu": "RTX4080",
                "vram": "12GB"
            },
            {
                "name": "aurora-motion-worker",
                "type": "MOTION",
                "gpu": "RTX4080",
                "vram": "12GB"
            }
        ]
        
        print("[+] Worker configuration:")
        for worker in workers:
            print(f"  - {worker['name']} ({worker['gpu']})")
        print("[+] Deploy workers via RunPod console: https://www.runpod.io/console/serverless")
        
        return workers

    def deploy_serverless(self):
        """Deploy RunPod Serverless Endpoints"""
        print("[*] Deploying RunPod Serverless...")
        
        endpoints = [
            "aurora-comfyui-serverless",
            "aurora-kling-serverless",
            "aurora-lipsync-serverless",
            "aurora-motion-serverless"
        ]
        
        for endpoint in endpoints:
            print(f"  [-] Creating endpoint: {endpoint}")
        
        print("[+] Deploy serverless via RunPod console: https://www.runpod.io/console/serverless")
        
        return endpoints

    def deploy_jupyter(self):
        """Deploy Jupyter Notebook with GPU"""
        print("[*] Deploying Jupyter Notebook...")
        
        jupyter_config = {
            "name": "aurora-jupyter",
            "image_name": "jupyter/datascience-notebook",
            "gpu_count": 1,
            "gpu_type_id": "RTX4070",
            "volume_in_gb": 30,
            "container_disk_in_gb": 10,
            "min_vcpu_count": 4,
            "min_memory_in_gb": 16
        }
        
        print("[+] Jupyter Pod configuration:")
        print(json.dumps(jupyter_config, indent=2))
        print("[+] Deploy via RunPod console: https://www.runpod.io/console/pods")
        
        return jupyter_config

    def deploy_monitoring(self):
        """Deploy monitoring and health checks"""
        print("[*] Setting up monitoring...")
        print("[+] Health check available at: http://localhost:8000/health")
        print("[+] Stats endpoint: http://localhost:8000/api/v1/stats")
        return True

    def deploy_all(self):
        """Deploy entire stack"""
        print("\n" + "="*60)
        print("Aurora GPU Pipeline - Full Stack Deployment Guide")
        print("="*60 + "\n")
        
        results = {
            "pod": self.deploy_pod(),
            "workers": self.deploy_workers(),
            "serverless": self.deploy_serverless(),
            "jupyter": self.deploy_jupyter(),
        }
        
        self.deploy_monitoring()
        
        print("\n" + "="*60)
        print("Next Steps")
        print("="*60)
        print("\n1. Configure environment (.env file):")
        print("   cp .env.example .env")
        print("   Edit .env with your RunPod API key and endpoints\n")
        
        print("2. Start the API server:")
        print("   python -m uvicorn api.main:app --reload\n")
        
        print("3. Start the worker manager:")
        print("   python -m worker_manager.worker_manager\n")
        
        print("4. Test endpoints:")
        print("   curl http://localhost:8000/health")
        print("   curl http://localhost:8000/api/v1/stats\n")
        
        return results

    def deploy_workers_only(self):
        """Deploy only workers"""
        print("[*] Workers Deployment Guide")
        return self.deploy_workers()

    def deploy_pod_only(self):
        """Deploy only Pod"""
        print("[*] Pod Deployment Guide")
        return self.deploy_pod()

    def deploy_serverless_only(self):
        """Deploy only Serverless"""
        print("[*] Serverless Deployment Guide")
        return self.deploy_serverless()

    def deploy_jupyter_only(self):
        """Deploy only Jupyter"""
        print("[*] Jupyter Deployment Guide")
        return self.deploy_jupyter()


def main():
    parser = argparse.ArgumentParser(description="Aurora GPU Pipeline Deployer")
    parser.add_argument(
        "--mode",
        choices=["all", "pod", "workers", "serverless", "jupyter"],
        default="all",
        help="Deployment mode"
    )
    
    args = parser.parse_args()
    
    try:
        deployer = AuroraDeployer()
        
        if args.mode == "all":
            deployer.deploy_all()
        elif args.mode == "pod":
            deployer.deploy_pod_only()
        elif args.mode == "workers":
            deployer.deploy_workers_only()
        elif args.mode == "serverless":
            deployer.deploy_serverless_only()
        elif args.mode == "jupyter":
            deployer.deploy_jupyter_only()
        
        print("\n[+] Deployment configuration complete!")
        
    except Exception as e:
        print(f"\n[-] Deployment failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
