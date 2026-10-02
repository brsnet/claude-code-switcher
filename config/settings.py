import os
import re
from typing import List

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(env_path, override=False)


class Settings:
    def __init__(self):
        # Credentials
        self.NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
        self.CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
        self.CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

        # NVIDIA NIM models (discover NVIDIA_NIM_MODEL1, NVIDIA_NIM_MODEL2, ...)
        self.NVIDIA_NIM_MODELS = self._discover_models("NVIDIA_NIM_MODEL")

        # Other models
        self.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
        configured_openrouter_models = self._discover_models("OPENROUTER_MODEL")
        self.OPENROUTER_MODELS = [
            model
            for model in configured_openrouter_models
            if model == "openrouter/free" or model.endswith(":free")
        ] or ["openrouter/free"]
        self.OPENROUTER_MODEL = self.OPENROUTER_MODELS[0]
        self.DEEPSEEK_MODELS = self._discover_models("DEEPSEEK_MODEL")
        self.OLLAMA_MODELS = self._discover_models("OLLAMA_MODEL")
        self.GROQ_MODELS = self._discover_models("GROQ_MODEL")
        self.GEMINI_MODELS = self._discover_models("GEMINI_MODEL")
        self.CEREBRAS_MODELS = self._discover_models("CEREBRAS_MODEL")
        self.CLOUDFLARE_MODELS = self._discover_models("CLOUDFLARE_MODEL")

        # Local endpoints
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        self.LLAMACPP_BASE_URL = os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080/v1")

        # Remote provider endpoints (with sensible defaults)
        self.NVIDIA_NIM_BASE_URL = os.getenv(
            "NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"
        )
        self.OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.GEMINI_BASE_URL = os.getenv(
            "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
        )
        self.CEREBRAS_BASE_URL = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1")
        cloudflare_default = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.CLOUDFLARE_ACCOUNT_ID}/ai/v1"
            if self.CLOUDFLARE_ACCOUNT_ID
            else ""
        )
        self.CLOUDFLARE_BASE_URL = os.getenv("CLOUDFLARE_BASE_URL", cloudflare_default)

        # Logical routes
        self.ROUTER_OPUS = self._parse_route(os.getenv("ROUTER_OPUS", ""))
        self.ROUTER_SONNET = self._parse_route(os.getenv("ROUTER_SONNET", ""))
        self.ROUTER_HAIKU = self._parse_route(os.getenv("ROUTER_HAIKU", ""))

        # Performance and tools
        self.TOOL_ALLOWLIST = self._parse_tool_allowlist(
            os.getenv("TOOL_ALLOWLIST", "Read,Edit,Write,Bash,Glob,Grep")
        )
        self.ENABLE_THINKING = os.getenv("ENABLE_THINKING", "false").lower() == "true"
        self.HTTP_READ_TIMEOUT = int(os.getenv("HTTP_READ_TIMEOUT", "600"))
        self.PROVIDER_MAX_CONCURRENCY = int(os.getenv("PROVIDER_MAX_CONCURRENCY", "5"))
        self.PROVIDER_MAX_RETRIES = int(os.getenv("PROVIDER_MAX_RETRIES", "3"))

        # Ollama Haiku specific adjustments
        self.HAIKU_LOCAL_NUM_CTX = os.getenv("HAIKU_LOCAL_NUM_CTX", "")
        self.HAIKU_LOCAL_THINK = os.getenv("HAIKU_LOCAL_THINK", "false").lower() == "true"
        self.HAIKU_LOCAL_MAX_CONCURRENCY = os.getenv("HAIKU_LOCAL_MAX_CONCURRENCY", "")

        # Metrics configuration
        self.METRICS_STORAGE_PATH = os.getenv("METRICS_STORAGE_PATH", "./data/metrics.jsonl")
        self.METRICS_FLUSH_INTERVAL = float(os.getenv("METRICS_FLUSH_INTERVAL", "5.0"))

    def _discover_models(self, variable_prefix: str) -> List[str]:
        """Discover PREFIX1..N models and prepend the legacy PREFIX value."""
        numbered = []
        pattern = re.compile(rf"^{re.escape(variable_prefix)}(\d+)$")
        for key, raw_value in os.environ.items():
            match = pattern.match(key)
            value = raw_value.strip()
            if match and value:
                numbered.append((int(match.group(1)), value))

        models: List[str] = []
        legacy_model = os.getenv(variable_prefix, "").strip()
        if legacy_model:
            models.append(legacy_model)
        for _, value in sorted(numbered):
            if value not in models:
                models.append(value)
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
