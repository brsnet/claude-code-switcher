import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("NVIDIA_NIM_BASE_URL")
print(f"NVIDIA_NIM_BASE_URL from os.getenv: {url}")

# Also check if it's in the environment
print("All NVIDIA_* env vars:")
for k, v in os.environ.items():
    if 'NVIDIA' in k:
        print(f"  {k} = {v}")