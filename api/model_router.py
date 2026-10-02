"""
Model router for expanding logical model names to concrete candidates.
"""

from typing import List

from config import settings


class ModelRouter:
    def __init__(self):
        self.settings = settings

    def _normalize_model_name(self, model_name: str) -> str:
        """Convert Claude model names to logical names."""
        # Map Claude model names to logical names
        if model_name.startswith("claude-opus-"):
            return "opus"
        elif model_name.startswith("claude-sonnet-"):
            return "sonnet"
        elif model_name.startswith("claude-haiku-"):
            return "haiku"
        return model_name

    def expand_provider(self, provider: str) -> List[str]:
        """Expand a provider token into concrete model candidates."""
        provider_models = {
            "nvidia_nim": self.settings.NVIDIA_NIM_MODELS,
            "open_router": self.settings.OPENROUTER_MODELS,
            "deepseek": self.settings.DEEPSEEK_MODELS,
            "ollama": self.settings.OLLAMA_MODELS,
            "groq": self.settings.GROQ_MODELS,
            "gemini": self.settings.GEMINI_MODELS,
            "cerebras": self.settings.CEREBRAS_MODELS,
            "cloudflare": self.settings.CLOUDFLARE_MODELS,
        }
        models = provider_models.get(provider)
        if models is None:
            return []
        return [f"{provider}/{model}" for model in models]

    @staticmethod
    def _is_free_openrouter_model(model: str) -> bool:
        return model == "openrouter/free" or model.endswith(":free")

    def resolve_route(self, logical_model: str) -> List[str]:
        """Resolve a logical model name (opus, sonnet, haiku) to a list of candidates."""
        # First normalize the model name in case it's a Claude model name
        normalized_model = self._normalize_model_name(logical_model)

        route_map = {
            "opus": self.settings.ROUTER_OPUS,
            "sonnet": self.settings.ROUTER_SONNET,
            "haiku": self.settings.ROUTER_HAIKU,
        }
        route = route_map.get(normalized_model, [])
        candidates: List[str] = []
        for token in route:
            # If token contains a slash, it's a specific model (e.g., "nvidia_nim/model-name")
            if "/" in token:
                provider, model = token.split("/", 1)
                if provider == "open_router" and not self._is_free_openrouter_model(model):
                    raise ValueError(
                        "OpenRouter candidates must use openrouter/free or a :free model variant"
                    )
                candidates.append(token)
            else:
                # Expand the provider
                expanded = self.expand_provider(token)
                candidates.extend(expanded)
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        return unique_candidates
