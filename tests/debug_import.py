#!/usr/bin/env python3
import os
import sys

print("Current working directory:", os.getcwd())
print(".env file exists:", os.path.exists(".env"))

# Read .env file directly
print("\n=== Reading .env file directly ===")
with open(".env", "r") as f:
    for line in f:
        if "NVIDIA" in line:
            print(f"  {line.strip()}")

# Check environment
print("\n=== Environment variables ===")
print(f"NVIDIA_NIM_BASE_URL: {os.environ.get('NVIDIA_NIM_BASE_URL', 'NOT SET')}")
print(f"NVIDIA_API_KEY: {os.environ.get('NVIDIA_API_KEY', 'NOT SET')[:20]}...")

# Try loading with dotenv
print("\n=== Using dotenv ===")
from dotenv import load_dotenv

load_dotenv()
print(
    f"After load_dotenv - NVIDIA_NIM_BASE_URL: {os.environ.get('NVIDIA_NIM_BASE_URL', 'NOT SET')}"
)

# Test importing settings
print("\n=== Importing settings ===")
sys.path.insert(0, ".")

# Clear any cached modules
modules_to_remove = [k for k in sys.modules.keys() if k.startswith("config")]
for mod in modules_to_remove:
    del sys.modules[mod]

try:
    from config.settings import Settings

    s = Settings()
    print(f"Settings.NVIDIA_NIM_BASE_URL: {s.NVIDIA_NIM_BASE_URL}")
    print(f"Settings.NVIDIA_API_KEY: {s.NVIDIA_API_KEY[:20]}...")
except Exception as e:
    print(f"Error importing settings: {e}")
    import traceback

    traceback.print_exc()
