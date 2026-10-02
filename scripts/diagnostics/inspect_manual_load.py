#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, ".")

print("Testing manual environment loading...")
try:
    from config.settings import settings

    print("SUCCESS: Settings imported")
    print(f"NVIDIA_NIM_BASE_URL: {settings.NVIDIA_NIM_BASE_URL}")
    print(f"NVIDIA_API_KEY: {settings.NVIDIA_API_KEY[:20]}...")
    print(f"NVIDIA_NIM_MODELS: {settings.NVIDIA_NIM_MODELS}")

    # Test model router
    from api.model_router import ModelRouter

    router = ModelRouter()
    opus_candidates = router.resolve_route("opus")
    print(f"Candidates for 'opus': {opus_candidates}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
