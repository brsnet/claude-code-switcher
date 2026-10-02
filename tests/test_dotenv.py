from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv("D:/projetos/claude-code-switcher/.env")

# Check if the variable is loaded
nvidia_base_url = os.getenv("NVIDIA_NIM_BASE_URL")
print(f"NVIDIA_NIM_BASE_URL from os.getenv: {nvidia_base_url}")

# Check all environment variables with NVIDIA
print("\nAll NVIDIA environment variables:")
for key, value in os.environ.items():
    if "NVIDIA" in key:
        print(f"  {key}: {value}")
