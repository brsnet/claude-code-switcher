import os
from typing import List, Optional

# Manually load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"')  # Remove quotes if present
else:
    # Fallback to loading from environment if .env not found
    pass

class Settings:
    def __init__(self):
        # Credentials
        self.NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

        # NVIDIA NIM models (discover NVIDIA_NIM_MODEL1, NVIDIA_NIM_MODEL2, ...)
        self.NVIDIA_NIM_MODELS = self._discover_nvidia_models()
        # Legacy support
        legacy_model = os.getenv("NVIDIA_NIM_MODEL")
        if legacy_model and legacy_model not in self.NVIDIA_NIM_MODELS:
            self.NVIDIA_NIM_MODELS.insert(0, legacy_model)

        # Other models
        self.OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "")
        self.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")

        # Local endpoints
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        self.LLAMACPP_BASE_URL = os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080/v1")

        # Remote provider endpoints (with sensible defaults)
        self.NVIDIA_NIM_BASE_URL = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

        # Logical routes
        self.ROUTER_OPUS = self._parse_route(os.getenv("ROUTER_OPUS", ""))
        self.ROUTER_SONNET = self._parse_route(os.getenv("ROUTER_SONNET", ""))
        self.ROUTER_HAIKU = self._parse_route(os.getenv("ROUTER_HAIKU", ""))

        # Performance and tools
        self.TOOL_ALLOWLIST = self._parse_tool_allowlist(os.getenv("TOOL_ALLOWLIST", "Read,Edit,Write,Bash,Glob,Grep"))
        self.ENABLE_THINKING = os.getenv("ENABLE_THINKING", "false").lower() == "true"
        self.HTTP_READ_TIMEOUT = int(os.getenv("HTTP_READ_TIMEOUT", "600"))
        self.PROVIDER_MAX_CONCURRENCY = int(os.getenv("PROVIDER_MAX_CONCURRENCY", "5"))
        self.PROVIDER_MAX_RETRIES = int(os.getenv("PROVIDER_MAX_RETRIES", "3"))

        # Ollama Haiku specific adjustments
        self.HAIKU_LOCAL_NUM_CTX = os.getenv("HAIKU_LOCAL_NUM_CTX", "")
        self.HAIKU_LOCAL_THINK = os.getenv("HAIKU_LOCAL_THINK", "false").lower() == "true"
        self.HAIKU_LOCAL_MAX_CONCURRENCY = os.getenv("HAIKU_LOCAL_MAX_CONCURRENCY", "")

    def _discover_nvidia_models(self) -> List[str]:
        models = []
        i = 1
        while True:
            key = f"NVIDIA_NIM_MODEL{i}"
            value = os.getenv(key)
            if value is None:
                break
            if value not in models:
                models.append(value)
            i += 1
        return models

    def _parse_route(self, route_str: str) -> List[str]:
        if not route_str:
            return []
        # Split by comma and strip whitespace
        return [part.strip() for part in route_str.split(",") if part.strip()]

    def _parse_tool_allowlist(self, tool_str: str) -> List[str]:
        if not tool_str:
            return []
        return [tool.strip() for tool in tool_str.split(",") if tool.strip()]

# Singleton instance
settings = Settings()