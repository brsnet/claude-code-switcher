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
        if provider == "nvidia_nim":
            # Expand to a list of "nvidia_nim/<model_identifier>"
            return [f"nvidia_nim/{model}" for model in self.settings.NVIDIA_NIM_MODELS]
        elif provider == "open_router":
            if self.settings.OPENROUTER_MODEL:
                return [f"open_router/{self.settings.OPENROUTER_MODEL}"]
            return []
        elif provider == "deepseek":
            if self.settings.DEEPSEEK_MODEL:
                return [f"deepseek/{self.settings.DEEPSEEK_MODEL}"]
            return []
        elif provider == "ollama":
            if self.settings.OLLAMA_MODEL:
                return [f"ollama/{self.settings.OLLAMA_MODEL}"]
            return []
        elif provider == "lmstudio":
            # For LM Studio, we don't have a specific model setting; we'll return empty and let the adapter handle it
            return []
        elif provider == "llamacpp":
            # Similarly for llama.cpp
            return []
        else:
            # If it's a specific model (e.g., with a prefix like "nvidia_nim/some-model"), we return it as-is
            # But note: the router only gets provider names without slash? Actually, the route can have specific models.
            # We'll handle that in the route resolution: if the token contains a slash, split and treat the first part as provider, second as model.
            # For now, we'll assume the router is called with provider-only tokens and the route expansion is done elsewhere.
            return [provider]

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
                # Validate provider? We'll just add the full token as a candidate.
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
