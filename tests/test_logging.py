"""
Test logging implementation in RequestHandler.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from api.services import RequestHandler
from config import settings
from core.anthropic.models import ChatCompletionRequest
from providers.base import ProviderError


def test_request_handler_logs_external_call():
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
    with patch('api.services.provider_registry') as mock_registry:
        mock_registry.get_adapter.return_value = mock_adapter

        # Create a request handler
        handler = RequestHandler()

        # Create a simple request
        request = ChatCompletionRequest(
            model="opus",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10,
            stream=False
        )

        # Capture logs
        with patch('api.services.logger') as mock_logger:
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

            # Check that the info call had the expected extra fields
            # We'll look for a call with extra containing provider, model, url
            found = False
            for call in mock_logger.info.call_args_list:
                args, kwargs = call
                if 'extra' in kwargs:
                    extra = kwargs['extra']
                    if extra.get('provider') == 'nvidia_nim' and \
                       extra.get('model') == 'nvidia/nemotron-3-super-120b-a12b' and \
                       extra.get('url') == settings.NVIDIA_NIM_BASE_URL:
                        found = True
                        break
            assert found, "Expected info log with provider, model, and URL not found"


def test_request_handler_logs_retry_and_failover():
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

    with patch('api.services.provider_registry') as mock_registry:
        mock_registry.get_adapter.return_value = mock_adapter

        handler = RequestHandler()
        request = ChatCompletionRequest(
            model="opus",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10,
            stream=False
        )

        with patch('api.services.logger') as mock_logger:
            async def run_test():
                events = []
                async for event in handler.handle_request(request, "opus"):
                    events.append(event)
                return events

            events = asyncio.run(run_test())

            assert len(events) == 1
            assert events[0]["type"] == "test_event"

            # We expect multiple info calls (for each attempt) and error calls for the failures
            # Check that we have at least one error log (for the first two attempts)
            assert mock_logger.error.call_count >= 2

            # Check that we have info logs for each attempt (including the successful one)
            # We expect at least 3 info calls (one for each attempt)
            assert mock_logger.info.call_count >= 3

            # Check that the info logs have the attempt number increasing
            # We'll just check that we see attempts 1, 2, and 3 in the logs
            attempt_numbers = []
            for call in mock_logger.info.call_args_list:
                args, kwargs = call
                if 'extra' in kwargs:
                    extra = kwargs['extra']
                    if 'attempt' in extra:
                        attempt_numbers.append(extra['attempt'])
            assert set([1, 2, 3]).issubset(set(attempt_numbers)), f"Expected attempts 1,2,3 in logs, got {attempt_numbers}"


def test_settings_loaded():
    """
    Test that settings are loaded from environment.
    """
    assert isinstance(settings.NVIDIA_API_KEY, str)
    assert settings.OPENROUTER_MODEL == "deepseek/deepseek-chat"
    assert settings.ROUTER_OPUS == ["nvidia_nim", "open_router", "ollama"]


def test_model_router_expansion():
    """
    Test that the model router expands the route correctly.
    """
    from api.model_router import ModelRouter
    router = ModelRouter()
    candidates = router.resolve_route("opus")
    # Expect: nvidia_nim/<each model>, open_router/<model>, ollama/<model>
    expected_prefixes = ["nvidia_nim/", "open_router/", "ollama/"]
    for candidate in candidates:
        assert any(candidate.startswith(prefix) for prefix in expected_prefixes), f"Candidate {candidate} does not start with expected prefix"
    # We should have 3 (nvidia) + 1 (openrouter) + 1 (ollama) = 5 candidates
    assert len(candidates) == 5


if __name__ == "__main__":
    # Allow running the test directly for debugging
    pytest.main([__file__, "-v"])
