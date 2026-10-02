"""
Service layer for handling requests, retries, failover, and tool filtering.
"""

import asyncio
import logging
import random
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from fastapi import HTTPException

from api import metrics
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
            "groq": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "gemini": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "cerebras": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
            "cloudflare": asyncio.Semaphore(settings.PROVIDER_MAX_CONCURRENCY),
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
        request_id: str,
        candidate: str,
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
                attempt_number = attempt + 1
                started_at = time.perf_counter()
                stream_started = False
                input_tokens = None
                output_tokens = None
                total_tokens = None
                try:
                    adapter = self.provider_registry.get_adapter(provider_name)
                    if not adapter:
                        raise HTTPException(
                            status_code=500, detail=f"Provider {provider_name} not registered"
                        )

                    logger.info(
                        "PROVIDER_REQUEST: request_id=%s provider=%s model=%r attempt=%s",
                        request_id,
                        provider_name,
                        model,
                        attempt_number,
                        extra={
                            "event": "PROVIDER_REQUEST",
                            "request_id": request_id,
                            "provider": provider_name,
                            "model": model,
                            "candidate": candidate,
                            "attempt": attempt_number,
                            "max_retries": max_retries,
                        },
                    )

                    async for event in adapter.stream(
                        request=request,
                        model=model,
                        api_key=api_key,
                        base_url=base_url,
                        **kwargs,
                    ):
                        if not stream_started and event.get("type") in {"text", "tool_calls"}:
                            stream_started = True
                            first_event_ms = int((time.perf_counter() - started_at) * 1000)
                            logger.info(
                                "PROVIDER_STREAM: request_id=%s provider=%s model=%r "
                                "first_event_ms=%s",
                                request_id,
                                provider_name,
                                model,
                                first_event_ms,
                                extra={
                                    "event": "PROVIDER_STREAM",
                                    "request_id": request_id,
                                    "provider": provider_name,
                                    "model": model,
                                    "candidate": candidate,
                                    "attempt": attempt_number,
                                    "first_event_ms": first_event_ms,
                                },
                            )
                        # Capture usage if present
                        if event.get("type") == "usage":
                            input_tokens = event.get("input_tokens")
                            output_tokens = event.get("output_tokens")
                            total_tokens = event.get("total_tokens")
                        yield event
                    duration_ms = int((time.perf_counter() - started_at) * 1000)
                    logger.info(
                        "PROVIDER_RESULT: request_id=%s provider=%s model=%r attempt=%s "
                        "result=success duration_ms=%s",
                        request_id,
                        provider_name,
                        model,
                        attempt_number,
                        duration_ms,
                        extra={
                            "event": "PROVIDER_RESULT",
                            "request_id": request_id,
                            "provider": provider_name,
                            "model": model,
                            "candidate": candidate,
                            "attempt": attempt_number,
                            "result": "success",
                            "duration_ms": duration_ms,
                        },
                    )
                    # Record metrics for successful attempt
                    metrics.record_attempt(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "request_id": request_id,
                            "provider": provider_name,
                            "model": model,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": total_tokens,
                            "duration_ms": duration_ms,
                            "success": True,
                            "error_category": None,
                        }
                    )
                    return
                except Exception as e:
                    duration_ms = int((time.perf_counter() - started_at) * 1000)
                    category = getattr(e, "category", "unexpected_error")
                    status_code = getattr(e, "status_code", None)
                    logger.warning(
                        "PROVIDER_ERROR: request_id=%s provider=%s model=%r attempt=%s "
                        "status=%s category=%s streamed=%s duration_ms=%s error=%r",
                        request_id,
                        provider_name,
                        model,
                        attempt_number,
                        status_code,
                        category,
                        str(stream_started).lower(),
                        duration_ms,
                        str(e),
                        extra={
                            "event": "PROVIDER_ERROR",
                            "request_id": request_id,
                            "provider": provider_name,
                            "model": model,
                            "candidate": candidate,
                            "attempt": attempt_number,
                            "status_code": status_code,
                            "category": category,
                            "streamed": stream_started,
                            "duration_ms": duration_ms,
                            "error": str(e),
                        },
                    )
                    if (
                        stream_started
                        or attempt_number == max_retries
                        or not self._is_retryable_same_candidate(e)
                    ):
                        raise
                    wait_time = (2**attempt) + random.uniform(0, 1)
                    wait_ms = int(wait_time * 1000)
                    logger.warning(
                        "ROUTE_RETRY: request_id=%s candidate=%r attempt=%s wait_ms=%s reason=%s",
                        request_id,
                        candidate,
                        attempt_number + 1,
                        wait_ms,
                        category,
                        extra={
                            "event": "ROUTE_RETRY",
                            "request_id": request_id,
                            "provider": provider_name,
                            "model": model,
                            "candidate": candidate,
                            "attempt": attempt_number + 1,
                            "wait_ms": wait_ms,
                            "reason": category,
                        },
                    )
                    await asyncio.sleep(wait_time)

    async def handle_request(
        self,
        request: ChatCompletionRequest,
        logical_model: str,
        request_id: str | None = None,
    ) -> AsyncIterator[dict]:
        """
        Handle a request by resolving the route, trying providers with retries and failover.
        """
        request_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
        request_started_at = time.perf_counter()
        candidates = self.model_router.resolve_route(logical_model)
        if not candidates:
            raise HTTPException(
                status_code=500, detail=f"No candidates found for model {logical_model}"
            )

        logger.info(
            "ROUTE_CHAIN: request_id=%s claude_model=%r candidates=%r",
            request_id,
            logical_model,
            candidates,
            extra={
                "event": "ROUTE_CHAIN",
                "request_id": request_id,
                "logical_model": logical_model,
                "candidates": candidates,
            },
        )

        # Filter tools once (we'll use the same filtered request for all attempts)
        filtered_request = self._filter_tools(request)

        # We'll try each candidate in order
        last_error = None
        attempted_candidates = []
        for candidate_index, candidate in enumerate(candidates):
            # Parse candidate: it could be a provider (e.g., "nvidia_nim") or a specific model (e.g., "nvidia_nim/model-name")
            if "/" in candidate:
                provider_name, model_name = candidate.split("/", 1)
            else:
                provider_name = candidate
                expanded = self.model_router.expand_provider(provider_name)
                model_name = expanded[0].split("/", 1)[1] if expanded else ""

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
                    "ROUTE: request_id=%s claude_model=%r -> provider=%s model=%r",
                    request_id,
                    logical_model,
                    provider_name,
                    model_name,
                    extra={
                        "event": "ROUTE",
                        "request_id": request_id,
                        "logical_model": logical_model,
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
                    request_id=request_id,
                    candidate=candidate,
                ):
                    stream_started = True
                    yield event
                total_ms = int((time.perf_counter() - request_started_at) * 1000)
                logger.info(
                    "REQUEST_DONE: request_id=%s provider=%s model=%r result=success total_ms=%s",
                    request_id,
                    provider_name,
                    model_name,
                    total_ms,
                    extra={
                        "event": "REQUEST_DONE",
                        "request_id": request_id,
                        "provider": provider_name,
                        "model": model_name,
                        "result": "success",
                        "total_ms": total_ms,
                    },
                )
                return
            except Exception as e:
                last_error = e
                if stream_started:
                    total_ms = int((time.perf_counter() - request_started_at) * 1000)
                    logger.error(
                        "REQUEST_DONE: request_id=%s provider=%s model=%r "
                        "result=stream_error total_ms=%s",
                        request_id,
                        provider_name,
                        model_name,
                        total_ms,
                        extra={
                            "event": "REQUEST_DONE",
                            "request_id": request_id,
                            "provider": provider_name,
                            "model": model_name,
                            "result": "stream_error",
                            "total_ms": total_ms,
                        },
                    )
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
                if candidate_index + 1 < len(candidates):
                    next_candidate = candidates[candidate_index + 1]
                    reason = getattr(e, "category", "provider_error")
                    logger.warning(
                        "ROUTE_FAILOVER: request_id=%s from=%r to=%r reason=%s",
                        request_id,
                        candidate,
                        next_candidate,
                        reason,
                        extra={
                            "event": "ROUTE_FAILOVER",
                            "request_id": request_id,
                            "from_candidate": candidate,
                            "to_candidate": next_candidate,
                            "reason": reason,
                        },
                    )

        # If we've tried all candidates and none worked, raise the last error
        if last_error:
            total_ms = int((time.perf_counter() - request_started_at) * 1000)
            logger.error(
                "REQUEST_DONE: request_id=%s result=error total_ms=%s attempts=%s",
                request_id,
                total_ms,
                len(attempted_candidates),
                extra={
                    "event": "REQUEST_DONE",
                    "request_id": request_id,
                    "result": "error",
                    "total_ms": total_ms,
                    "attempt_count": len(attempted_candidates),
                },
            )
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
        keys = {
            "nvidia_nim": settings.NVIDIA_API_KEY,
            "open_router": settings.OPENROUTER_API_KEY,
            "deepseek": settings.DEEPSEEK_API_KEY,
            "groq": settings.GROQ_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
            "cerebras": settings.CEREBRAS_API_KEY,
            "cloudflare": settings.CLOUDFLARE_API_TOKEN,
        }
        return keys.get(provider_name, "")

    def _get_base_url(self, provider_name: str) -> str:
        """Get the base URL for a provider."""
        base_urls = {
            "ollama": settings.OLLAMA_BASE_URL,
            "lmstudio": settings.LMSTUDIO_BASE_URL,
            "llamacpp": settings.LLAMACPP_BASE_URL,
            "nvidia_nim": settings.NVIDIA_NIM_BASE_URL,
            "open_router": settings.OPENROUTER_BASE_URL,
            "deepseek": settings.DEEPSEEK_BASE_URL,
            "groq": settings.GROQ_BASE_URL,
            "gemini": settings.GEMINI_BASE_URL,
            "cerebras": settings.CEREBRAS_BASE_URL,
            "cloudflare": settings.CLOUDFLARE_BASE_URL,
        }
        return base_urls.get(provider_name, "")
