import os
from dotenv import load_dotenv

# Load the .env file explicitly
load_dotenv(dotenv_path="D:/projetos/claude-code-switcher/.env")

print("Environment variables after load_dotenv:")
nvidia_url = os.getenv("NVIDIA_NIM_BASE_URL")
print(f"NVIDIA_NIM_BASE_URL: {nvidia_url}")

# Now test importing settings
import sys

sys.path.insert(0, "D:/projetos/claude-code-switcher")

# Force reload of the settings module
if "config.settings" in sys.modules:
    del sys.modules["config.settings"]
if "config" in sys.modules:
    del sys.modules["config"]

from config.settings import Settings

s = Settings()
print(f"Settings.NVIDIA_NIM_BASE_URL: {s.NVIDIA_NIM_BASE_URL}")
