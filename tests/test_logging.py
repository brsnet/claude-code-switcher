"""
Test logging implementation in RequestHandler.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, patch

import pytest

from api.services import RequestHandler
from config import settings
from core.anthropic.models import ChatCompletionRequest
from providers.base import ProviderError


def test_request_handler_logs_external_call(monkeypatch):
    """
    Test that RequestHandler logs external call attempts with provider, model, and URL.
    """
    # Create a mock adapter that yields a single event and then exits
    mock_adapter = AsyncMock()

    async def mock_stream(*args, **kwargs):
        # Yield a mock event (in the format expected by the handler)
        yield {"type": "test_event"}

    mock_adapter.stream = mock_stream

    # Patch the provider registry to return our mock adapter
    with patch("api.services.provider_registry") as mock_registry:
        mock_registry.get_adapter.return_value = mock_adapter

        # Create a request handler
        handler = RequestHandler()
        monkeypatch.setattr(
            handler.model_router,
            "resolve_route",
            lambda _model: ["nvidia_nim/example-model"],
        )

        # Create a simple request
        request = ChatCompletionRequest(
            model="opus",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10,
            stream=False,
        )

        # Capture logs
        with patch("api.services.logger") as mock_logger:
            # Call handle_request (we expect it to succeed with our mock adapter)
            # We'll consume the async iterator to trigger the logging
            async def run_test():
                events = []
                async for event in handler.handle_request(request, "opus"):
                    events.append(event)
                return events

            events = asyncio.run(run_test())

            # Check that we got the event
            assert len(events) == 1
            assert events[0]["type"] == "test_event"

            # Check that logger.info was called for the attempt
            # We expect at least one info call for the attempt
            assert mock_logger.info.call_count >= 1

            # Check that the selected provider and concrete model are structured.
            found = False
            for call in mock_logger.info.call_args_list:
                args, kwargs = call
                if "extra" in kwargs:
                    extra = kwargs["extra"]
                    if (
                        extra.get("provider") == "nvidia_nim"
                        and extra.get("model") == "example-model"
                    ):
                        found = True
                        break
            assert found, "Expected info log with provider and model not found"


def test_request_handler_logs_retry_and_failover(monkeypatch):
    """
    Test that RequestHandler logs retries and failover attempts.
    """
    # We'll simulate a provider that fails twice then succeeds on the third attempt
    call_count = 0

    async def mock_stream(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ProviderError(
                "nvidia_nim",
                "Temporary error",
                status_code=503,
                category="http_error",
            )
        yield {"type": "test_event"}

    mock_adapter = AsyncMock()
    mock_adapter.stream = mock_stream

    with patch("api.services.provider_registry") as mock_registry:
        mock_registry.get_adapter.return_value = mock_adapter

        handler = RequestHandler()

        async def no_sleep(_delay):
            return None

        monkeypatch.setattr("api.services.asyncio.sleep", no_sleep)
        request = ChatCompletionRequest(
            model="opus",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10,
            stream=False,
        )

        with patch("api.services.logger") as mock_logger:

            async def run_test():
                events = []
                async for event in handler.handle_request(request, "opus"):
                    events.append(event)
                return events

            events = asyncio.run(run_test())

            assert len(events) == 1
            assert events[0]["type"] == "test_event"

            # Expected transient failures are compact warnings, not repeated tracebacks.
            assert mock_logger.warning.call_count >= 2
            assert mock_logger.error.call_count == 0

            # Check that we have info logs for each attempt (including the successful one)
            # We expect at least 3 info calls (one for each attempt)
            assert mock_logger.info.call_count >= 3

            # Check that the info logs have the attempt number increasing
            # We'll just check that we see attempts 1, 2, and 3 in the logs
            attempt_numbers = []
            for call in mock_logger.info.call_args_list:
                args, kwargs = call
                if "extra" in kwargs:
                    extra = kwargs["extra"]
                    if "attempt" in extra:
                        attempt_numbers.append(extra["attempt"])
            assert set([1, 2, 3]).issubset(set(attempt_numbers)), (
                f"Expected attempts 1,2,3 in logs, got {attempt_numbers}"
            )


def test_route_log_is_human_readable_and_structured(monkeypatch, caplog):
    class SuccessfulAdapter:
        async def stream(self, **kwargs):
            yield {"type": "text", "text": "ok"}
            yield {"type": "finish", "stop_reason": "end_turn"}

    class Registry:
        def get_adapter(self, _name):
            return SuccessfulAdapter()

    handler = RequestHandler()
    handler.provider_registry = Registry()
    monkeypatch.setattr(
        handler.model_router,
        "resolve_route",
        lambda _model: ["nvidia_nim/example-model"],
    )
    request = ChatCompletionRequest(
        model="claude-sonnet-5",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=10,
        stream=True,
    )

    async def collect():
        return [
            event
            async for event in handler.handle_request(
                request, request.model, request_id="req_visible"
            )
        ]

    with caplog.at_level(logging.INFO, logger="api.services"):
        asyncio.run(collect())

    route_record = next(record for record in caplog.records if record.event == "ROUTE")
    assert "provider=nvidia_nim" in route_record.getMessage()
    assert "model='example-model'" in route_record.getMessage()
    assert route_record.request_id == "req_visible"
    assert route_record.provider == "nvidia_nim"
    assert route_record.model == "example-model"


def test_settings_loaded():
    """
    Test that settings are loaded from environment.
    """
    assert isinstance(settings.NVIDIA_API_KEY, str)
    assert settings.OPENROUTER_MODEL == "openrouter/free"
    assert all(
        model == "openrouter/free" or model.endswith(":free")
        for model in settings.OPENROUTER_MODELS
    )
    # Updated routing with all configured providers
    assert settings.ROUTER_OPUS == [
        "nvidia_nim", "groq", "gemini", "open_router", "cloudflare", "cerebras", "ollama"
    ]


def test_model_router_expansion():
    """
    Test that the model router expands the route correctly.
    """
    from api.model_router import ModelRouter

    router = ModelRouter()
    candidates = router.resolve_route("opus")
    # Expect: nvidia_nim/<each model>, groq/<model>, gemini/<model>, open_router/<model>, cloudflare/<model>, cerebras/<model>, ollama/<model>
    expected_prefixes = [
        "nvidia_nim/", "groq/", "gemini/", "open_router/",
        "cloudflare/", "cerebras/", "ollama/"
    ]
    for candidate in candidates:
        assert any(candidate.startswith(prefix) for prefix in expected_prefixes), (
            f"Candidate {candidate} does not start with expected prefix"
        )
    # 3 nvidia models + 2 groq + 1 gemini + 1 openrouter + 1 cloudflare + 0 cerebras (empty) + 1 ollama = 9
    assert len(candidates) == 9


if __name__ == "__main__":
    # Allow running the test directly for debugging
    pytest.main([__file__, "-v"])
