"""
Provider adapter registry.
"""
from typing import Dict
from providers.base import ProviderAdapter

class ProviderRegistry:
    def __init__(self):
        self._adapters: Dict[str, ProviderAdapter] = {}

    def register(self, name: str, adapter: ProviderAdapter) -> None:
        """Register a provider adapter."""
        self._adapters[name] = adapter

    def get_adapter(self, name: str) -> ProviderAdapter:
        """Get a provider adapter by name."""
        adapter = self._adapters.get(name)
        if not adapter:
            raise ValueError(f"Provider adapter '{name}' not registered")
        return adapter

    def has_adapter(self, name: str) -> bool:
        """Check if a provider adapter is registered."""
        return name in self._adapters