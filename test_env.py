import os
from dotenv import load_dotenv

load_dotenv()

print("NVIDIA_API_KEY:", os.getenv("NVIDIA_API_KEY", "NOT SET"))
print("NVIDIA_NIM_BASE_URL:", os.getenv("NVIDIA_NIM_BASE_URL", "NOT SET"))
print("All env vars containing NVIDIA:")
for key, value in os.environ.items():
    if "NVIDIA" in key:
        print(f"  {key}: {value}")