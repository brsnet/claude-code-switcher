#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

print("Testing settings import...")
try:
    from config.settings import Settings
    s = Settings()
    print("SUCCESS: Settings imported")
    print(f"NVIDIA_NIM_BASE_URL: {s.NVIDIA_NIM_BASE_URL}")
    print(f"NVIDIA_API_KEY: {s.NVIDIA_API_KEY[:20]}...")
    print(f"NVIDIA_NIM_MODELS: {s.NVIDIA_NIM_MODELS}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)