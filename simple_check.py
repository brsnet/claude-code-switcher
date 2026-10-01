import os

print("Checking environment...")

# Check if .env exists
env_path = r"D:\projetos\claude-code-switcher\.env"
print(f".env exists: {os.path.exists(env_path)}")

# Read .env file
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        content = f.read()
        print(f".env file length: {len(content)}")
        # Look for NVIDIA_NIM_BASE_URL
        for line in content.split("\n"):
            if "NVIDIA_NIM_BASE_URL" in line:
                print(f"Found line: {line}")
                # Check if it's the one we want
                if "https://ai.api.nvidia.com/v1" in line:
                    print("SUCCESS: Found correct NVIDIA_NIM_BASE_URL")
                else:
                    print("WARNING: Found NVIDIA_NIM_BASE_URL but with different value")
else:
    print(".env file not found!")

# Check current directory
print(f"Current directory: {os.getcwd()}")

# Check if we can import settings
try:
    import sys

    sys.path.insert(0, r"D:\projetos\claude-code-switcher")
    from config.settings import Settings

    s = Settings()
    print(f"Settings.NVIDIA_NIM_BASE_URL: {s.NVIDIA_NIM_BASE_URL}")
    if s.NVIDIA_NIM_BASE_URL == "https://ai.api.nvidia.com/v1":
        print("SUCCESS: Settings loaded correct URL")
    else:
        print(f"ERROR: Settings has wrong URL: {s.NVIDIA_NIM_BASE_URL}")
except Exception as e:
    print(f"Error importing settings: {e}")
    import traceback

    traceback.print_exc()
