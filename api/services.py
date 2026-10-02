"""
Service layer for handling requests, retries, failover, and tool filtering.
"""

import asyncio
import logging
import random
import time
from typing import AsyncIterator

import httpx
from fastapi import HTTPException

from api.model_router import ModelRouter
from config import settings
from core.anthropic.models import ChatCompletionRequest, ToolChoice
from providers import registry as provider_registry
from providers.base import ProviderError

logger = logging.getLogger(__name__)


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

        choice = request.tool_choice
        if isinstance(choice, ToolChoice):
            choice = choice.model_dump(exclude_none=True)
        forced_name = None
        if isinstance(choice, dict):
            if choice.get("type") == "tool":
                forced_name = choice.get("name")
            elif choice.get("type") == "function":
                function = choice.get("function")
                if isinstance(function, dict):
                    forced_name = function.get("name")

        available_names = {self._tool_name(tool) for tool in request.tools if self._tool_name(tool)}
        if forced_name and forced_name not in available_names:
            raise HTTPException(
                status_code=400,
                detail=f"Forced tool '{forced_name}' is not present in the request",
            )

        allowed_tools = []
        seen_names = set()
        for tool in request.tools:
            name = self._tool_name(tool)
            if not name or name in seen_names:
                continue
            if name in settings.TOOL_ALLOWLIST or name == forced_name:
                allowed_tools.append(tool)
                seen_names.add(name)

        filtered_request = request.model_copy(deep=True)
        filtered_request.tools = allowed_tools if allowed_tools else None
        if not allowed_tools:
            filtered_request.tool_choice = None
        return filtered_request

    @staticmethod
    def _tool_name(tool: object) -> str | None:
        if not isinstance(tool, dict):
            return None
        name = tool.get("name")
        if isinstance(name, str):
            return name
        function = tool.get("function")
        if isinstance(function, dict) and isinstance(function.get("name"), str):
            return function["name"]
        return None

    def _is_retryable_same_candidate(self, exception: Exception) -> bool:
        """Determine if an exception is eligible for retry in the same candidate."""
        status_code = getattr(exception, "status_code", None)
        if status_code is not None:
            return status_code in {429, 500, 502, 503, 504, 529}
        if isinstance(exception, httpx.RequestError):
            return True
        return False

    def _is_retryable_for_failover(self, exception: Exception) -> bool:
        """Determine if an exception is eligible for failover (try next candidate)."""
        status_code = getattr(exception, "status_code", None)
        if status_code is not None:
            return status_code in {401, 402, 403, 404, 429, 500, 502, 503, 504, 529}
        if isinstance(exception, httpx.RequestError):
            return True
        return False

    async def _try_provider(
        self,
        request: ChatCompletionRequest,
        provider_name: str,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs,
    ) -> AsyncIterator[dict]:
        """Try a single provider with retries and concurrency limit."""
        # Get the semaphore for this provider
        semaphore = self.provider_semaphores.get(provider_name)
        if semaphore is None:
            semaphore = asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY)

        async with semaphore:
            # Retry with exponential backoff
            max_retries = (
                settings.PROVIDER_MAX_RETRIES if hasattr(settings, "PROVIDER_MAX_RETRIES") else 3
            )
            for attempt in range(max_retries):
                try:
                    adapter = self.provider_registry.get_adapter(provider_name)
                    if not adapter:
                        raise HTTPException(
                            status_code=500, detail=f"Provider {provider_name} not registered"
                        )

                    # Log the start of the attempt
                    logger.info(
                        "Starting provider call attempt",
                        extra={
                            "provider": provider_name,
                            "model": model,
                            "url": base_url,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                        },
                    )

                    # Wrap the adapter stream to log on exit
                    async def logged_stream():
                        start_time = time.time()
                        try:
                            async for event in adapter.stream(
                                request=request,
                                model=model,
                                api_key=api_key,
                                base_url=base_url,
                                **kwargs,
                            ):
                                yield event
                        finally:
                            end_time = time.time()
                            logger.info(
                                "Provider call attempt finished",
                                extra={
                                    "provider": provider_name,
                                    "model": model,
                                    "url": base_url,
                                    "duration": end_time - start_time,
                                    "attempt": attempt + 1,
                                },
                            )

                    # Now we use the logged_stream
                    async for event in logged_stream():
                        yield event
                    # If we successfully exited the loop, break out of the retry loop
                    break
                except Exception as e:
                    # Log the error for this attempt
                    logger.error(
                        "Provider call attempt failed",
                        extra={
                            "provider": provider_name,
                            "model": model,
                            "url": base_url,
                            "attempt": attempt + 1,
                            "error": str(e),
                        },
                        exc_info=True,
                    )
                    if attempt == max_retries - 1 or not self._is_retryable_same_candidate(e):
                        # If we've exhausted retries or the error is not retryable in same candidate, re-raise
                        raise
                    # Otherwise, wait for the next attempt with exponential backoff and jitter
                    wait_time = (2**attempt) + random.uniform(0, 1)
                    await asyncio.sleep(wait_time)

    async def handle_request(
        self, request: ChatCompletionRequest, logical_model: str
    ) -> AsyncIterator[dict]:
        """
        Handle a request by resolving the route, trying providers with retries and failover.
        """
        # Get the candidate chain for the logical model
        candidates = self.model_router.resolve_route(logical_model)
        if not candidates:
            raise HTTPException(
                status_code=500, detail=f"No candidates found for model {logical_model}"
            )

        # Filter tools once (we'll use the same filtered request for all attempts)
        filtered_request = self._filter_tools(request)

        # We'll try each candidate in order
        last_error = None
        attempted_candidates = []
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
                attempted_candidates.append(candidate)
                logger.info(
                    "Attempting candidate",
                    extra={
                        "provider": provider_name,
                        "model": model_name,
                        "candidate": candidate,
                    },
                )
                async for event in self._try_provider(
                    request=filtered_request,
                    provider_name=provider_name,
                    model=model_name,
                    api_key=api_key,
                    base_url=base_url,
                ):
                    stream_started = True
                    yield event
                return
            except Exception as e:
                last_error = e
                if stream_started:
                    enhanced_msg = (
                        f"Error during streaming from {provider_name}/{model_name}: {str(e)}"
                    )
                    raise ProviderError(
                        provider_name,
                        enhanced_msg,
                        status_code=getattr(e, "status_code", None),
                        category="stream_error",
                    ) from e
                if not self._is_retryable_for_failover(e):
                    break

        # If we've tried all candidates and none worked, raise the last error
        if last_error:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"All candidates failed. Last error: {str(last_error)}. "
                    f"Candidates tried: {attempted_candidates}"
                ),
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=(
                    "All candidates failed (no errors recorded). "
                    f"Candidates: {attempted_candidates}"
                ),
            )

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
