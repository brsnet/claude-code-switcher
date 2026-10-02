#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load .env from current directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
print(f"Loading .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

# Load the environment variables
load_dotenv(env_path)

# Check the values
nvidia_base_url = os.getenv("NVIDIA_NIM_BASE_URL")
nvidia_api_key = os.getenv("NVIDIA_API_KEY")

print(f"NVIDIA_NIM_BASE_URL: {nvidia_base_url}")
print(f"NVIDIA_API_KEY: {nvidia_api_key[:20] if nvidia_api_key else 'NOT SET'}...")

# Now test importing the settings module
import sys

sys.path.insert(0, ".")

# Clear settings module from cache if it exists
if "config.settings" in sys.modules:
    del sys.modules["config.settings"]

from config.settings import Settings

s = Settings()

print(f"Settings.NVIDIA_NIM_BASE_URL: {s.NVIDIA_NIM_BASE_URL}")
print(f"Settings.NVIDIA_API_KEY: {s.NVIDIA_API_KEY[:20] if s.NVIDIA_API_KEY else 'NOT SET'}...")

# Test model router
from api.model_router import ModelRouter

router = ModelRouter()
candidates = router.resolve_route("opus")
print(f"Candidates for opus: {candidates}")
