"""
Base provider adapter interface.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from core.anthropic.models import ChatCompletionRequest


class ProviderError(Exception):
    """A sanitized provider failure whose HTTP semantics survive failover."""

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status_code: int | None = None,
        category: str = "provider_error",
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.category = category


class ProviderAdapter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def stream(
        self, request: ChatCompletionRequest, model: str, api_key: str, base_url: str, **kwargs
    ) -> AsyncIterator[dict]:
        """
        Stream a request to the provider.

        :param request: The normalized Anthropic request.
        :param model: The model identifier to use.
        :param api_key: The API key for authentication.
        :param base_url: The base URL of the provider's API.
        :param kwargs: Additional provider-specific arguments.
        :return: An async iterator of normalized events (to be converted to SSE by the core).
        """
        pass
