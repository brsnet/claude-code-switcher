#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Environment Variables ===")
print(f"NVIDIA_API_KEY: {os.getenv('NVIDIA_API_KEY', 'NOT SET')[:20]}...")
print(f"NVIDIA_NIM_BASE_URL: {os.getenv('NVIDIA_NIM_BASE_URL', 'NOT SET')}")
print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY', 'NOT SET')[:20]}...")
print()

print("=== Settings Module ===")
try:
    from config.settings import Settings

    s = Settings()
    print(f"NVIDIA_API_KEY from settings: {s.NVIDIA_API_KEY[:20]}...")
    print(f"NVIDIA_NIM_BASE_URL from settings: {s.NVIDIA_NIM_BASE_URL}")
    print(f"NVIDIA_NIM_MODELS: {s.NVIDIA_NIM_MODELS}")
    print(f"ROUTER_OPUS: {s.ROUTER_OPUS}")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print("\n=== Model Router Test ===")
try:
    from api.model_router import ModelRouter

    router = ModelRouter()
    opus_candidates = router.resolve_route("opus")
    print(f"Candidates for 'opus': {opus_candidates}")
    sonnet_candidates = router.resolve_route("sonnet")
    print(f"Candidates for 'sonnet': {sonnet_candidates}")
    haiku_candidates = router.resolve_route("haiku")
    print(f"Candidates for 'haiku': {haiku_candidates}")
except Exception as e:
    print(f"Error testing model router: {e}")
    import traceback

    traceback.print_exc()
