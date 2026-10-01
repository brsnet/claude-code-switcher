"""
Provider adapter registration.
"""
from providers.registry import ProviderRegistry
from providers.nvidia_nim.adapter import NVIDIANimAdapter
from providers.openrouter.adapter import OpenRouterAdapter
from providers.deepseek.adapter import DeepSeekAdapter
from providers.ollama.adapter import OllamaAdapter
from providers.lmstudio.adapter import LMStudioAdapter
from providers.llamacpp.adapter import LlamaCppAdapter

# Create a global registry instance
registry = ProviderRegistry()

# Register all adapters
registry.register("nvidia_nim", NVIDIANimAdapter())
registry.register("open_router", OpenRouterAdapter())
registry.register("deepseek", DeepSeekAdapter())
registry.register("ollama", OllamaAdapter())
registry.register("lmstudio", LMStudioAdapter())
registry.register("llamacpp", LlamaCppAdapter())