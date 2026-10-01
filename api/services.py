"""
Service layer for handling requests, retries, failover, and tool filtering.
"""
import asyncio
import random
import time
from typing import AsyncIterator, Optional
from fastapi import HTTPException
import httpx
from config import settings
from api.model_router import ModelRouter
from providers import registry as provider_registry
from providers.base import ProviderHTTPError
from core.anthropic.models import ChatCompletionRequest

class RequestHandler:
    def __init__(self):
        self.model_router = ModelRouter()
        self.provider_registry = provider_registry
        # Initialize semaphores for provider concurrency control
        self.provider_semaphores = {
            "nvidia_nim": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "open_router": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "deepseek": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "ollama": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "lmstudio": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "llamacpp": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
        }

    def _filter_tools(self, request: ChatCompletionRequest) -> ChatCompletionRequest:
        """Create a copy of the request with only allowed tools."""
        if not request.tools:
            return request

        allowed_tools = []
        for tool in request.tools:
            # Tools come in Anthropic format: {'name': ..., 'description': ..., 'input_schema': ...}
            if isinstance(tool, dict) and tool.get("name") in settings.TOOL_ALLOWLIST:
                allowed_tools.append(tool)

        # Create a new request with filtered tools
        filtered_request = request.model_copy()
        filtered_request.tools = allowed_tools if allowed_tools else None
        return filtered_request

    def _is_retryable_same_candidate(self, exception: Exception) -> bool:
        """Determine if an exception is eligible for retry in the same candidate."""
        if isinstance(exception, ProviderHTTPError):
            # Retry on 429, 500, 502, 503, 504, 529
            return exception.status_code in {429, 500, 502, 503, 504, 529}
        elif isinstance(exception, HTTPException):
            return exception.status_code in {429, 500, 502, 503, 504, 529}
        elif isinstance(exception, httpx.RequestError):
            return True
        return False

    def _is_retryable_for_failover(self, exception: Exception) -> bool:
        """Determine if an exception is eligible for failover (try next candidate)."""
        if isinstance(exception, ProviderHTTPError):
            # Failover on 401, 402, 429, 500, 502, 503, 504, 529
            # Note: 404 (not found) is not retryable for failover? Actually we want to failover on 404 (model not found) but not retry same candidate.
            # According to spec: 404 of endpoint or model: not repeat inutilmente; allow next candidate.
            # So we should allow failover on 404 as well? The spec says: "não repetir inutilmente; permitir próximo candidato, registrando erro de configuração/modelo."
            # That means we should not retry same candidate, but we can try next candidate. So failover should be allowed for 404.
            # However, we also have to consider that 404 might be due to wrong endpoint, which might be same for all candidates of same provider?
            # But we are iterating over candidates, which may be same provider different model or different provider.
            # We'll allow failover on 404.
            return exception.status_code in {401, 402, 404, 429, 500, 502, 503, 504, 529}
        elif isinstance(exception, HTTPException):
            return exception.status_code in {401, 402, 404, 429, 500, 502, 503, 504, 529}
        elif isinstance(exception, httpx.RequestError):
            return True
        return False

    async def _try_provider(
        self,
        request: ChatCompletionRequest,
        provider_name: str,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs
    ) -> AsyncIterator[dict]:
        """Try a single provider with retries and concurrency limit."""
        # Get the semaphore for this provider
        semaphore = self.provider_semaphores.get(provider_name)
        if semaphore is None:
            # If we don't have a semaphore for this provider, we assume no limit
            semaphore = asyncio.Semaphore(float('inf'))

        async with semaphore:
            # Retry with exponential backoff
            max_retries = settings.PROVIDER_MAX_RETRIES if hasattr(settings, 'PROVIDER_MAX_RETRIES') else 3
            for attempt in range(max_retries):
                try:
                    adapter = self.provider_registry.get_adapter(provider_name)
                    if not adapter:
                        raise HTTPException(status_code=500, detail=f"Provider {provider_name} not registered")

                    async for event in adapter.stream(
                        request=request,
                        model=model,
                        api_key=api_key,
                        base_url=base_url,
                        **kwargs
                    ):
                        yield event
                    # If we successfully exited the loop, break out of the retry loop
                    break
                except Exception as e:
                    if attempt == max_retries - 1 or not self._is_retryable_same_candidate(e):
                        # If we've exhausted retries or the error is not retryable in same candidate, re-raise
                        raise
                    # Otherwise, wait for the next attempt with exponential backoff and jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)

    async def handle_request(
        self,
        request: ChatCompletionRequest,
        logical_model: str
    ) -> AsyncIterator[dict]:
        """
        Handle a request by resolving the route, trying providers with retries and failover.
        """
        # Get the candidate chain for the logical model
        candidates = self.model_router.resolve_route(logical_model)
        if not candidates:
            raise HTTPException(status_code=500, detail=f"No candidates found for model {logical_model}")

        # Filter tools once (we'll use the same filtered request for all attempts)
        filtered_request = self._filter_tools(request)

        # We'll try each candidate in order
        last_error = None
        for candidate in candidates:
            # Parse candidate: it could be a provider (e.g., "nvidia_nim") or a specific model (e.g., "nvidia_nim/model-name")
            if "/" in candidate:
                provider_name, model_name = candidate.split("/", 1)
            else:
                provider_name = candidate
                # Get the model name from the settings based on the provider
                if provider_name == "nvidia_nim":
                    model_name = settings.NVIDIA_NIM_MODELS[0] if settings.NVIDIA_NIM_MODELS else ""
                elif provider_name == "open_router":
                    model_name = settings.OPENROUTER_MODEL
                elif provider_name == "deepseek":
                    model_name = settings.DEEPSEEK_MODEL
                elif provider_name == "ollama":
                    model_name = settings.OLLAMA_MODEL
                else:
                    # For lmstudio and llamacpp, we don't have a model setting in the spec, so we leave it empty
                    model_name = ""

            if not model_name:
                # Skip if we don't have a model name for this provider
                continue

            # Get API key and base URL for the provider
            api_key = self._get_api_key(provider_name)
            base_url = self._get_base_url(provider_name)

            # Track if we've started streaming (yielded any events)
            stream_started = False

            try:
                async for event in self._try_provider(
                    request=filtered_request,
                    provider_name=provider_name,
                    model=model_name,
                    api_key=api_key,
                    base_url=base_url
                ):
                    stream_started = True
                    yield event
                # If we successfully yielded events, return
                return
            except Exception as e:
                last_error = e
                # If we've started streaming, we should not failover to avoid duplicating content
                if stream_started:
                    # Enhance the exception with context before re-raising
                    enhanced_msg = f"Error during streaming from {provider_name}/{model_name}: {str(e)}"
                    enhanced_exception = Exception(enhanced_msg)
                    # Re-raise the enhanced error to be sent as a valid SSE event upstream
                    raise enhanced_exception
                # Only continue to next candidate if it's eligible for failover
                if not self._is_retryable_for_failover(e):
                    break
                # Otherwise, continue to next candidate

        # If we've tried all candidates and none worked, raise the last error
        if last_error:
            # Include information about all the candidates we tried for better debugging
            raise HTTPException(
                status_code=500,
                detail=f"All candidates failed. Last error: {str(last_error)}. Candidates tried: {candidates}"
            )
        else:
            raise HTTPException(status_code=500, detail="All candidates failed (no errors recorded)")

    def _get_api_key(self, provider_name: str) -> str:
        """Get the API key for a provider."""
        if provider_name == "nvidia_nim":
            return settings.NVIDIA_API_KEY
        elif provider_name == "open_router":
            return settings.OPENROUTER_API_KEY
        elif provider_name == "deepseek":
            return settings.DEEPSEEK_API_KEY
        return ""

    def _get_base_url(self, provider_name: str) -> str:
        """Get the base URL for a provider."""
        if provider_name == "ollama":
            return settings.OLLAMA_BASE_URL
        elif provider_name == "lmstudio":
            return settings.LMSTUDIO_BASE_URL
        elif provider_name == "llamacpp":
            return settings.LLAMACPP_BASE_URL
        elif provider_name == "nvidia_nim":
            return settings.NVIDIA_NIM_BASE_URL
        elif provider_name == "open_router":
            return settings.OPENROUTER_BASE_URL
        elif provider_name == "deepseek":
            return settings.DEEPSEEK_BASE_URL
        return ""