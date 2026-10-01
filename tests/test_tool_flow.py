import asyncio
import json

import pytest

from api.services import RequestHandler
from config import settings
from config.settings import Settings
from core.anthropic.models import ChatCompletionRequest
from core.anthropic.stream_response import normalize_to_anthropic_sse
from providers.base import ProviderError
from providers.openai_compat import OpenAICompatibleAdapter


def make_request(**overrides):
    payload = {
        "model": "claude-sonnet-4-5",
        "messages": [{"role": "user", "content": "Leia README.md"}],
        "stream": True,
        "tools": [
            {
                "name": "Read",
                "description": "Read a file",
                "input_schema": {
                    "type": "object",
                    "properties": {"file_path": {"type": "string"}},
                    "required": ["file_path"],
                },
            }
        ],
    }
    payload.update(overrides)
    return ChatCompletionRequest(**payload)


def test_anthropic_tools_are_preserved_until_provider_conversion():
    request = make_request()

    assert request.tools[0]["name"] == "Read"
    assert "function" not in request.tools[0]


def test_filter_keeps_allowed_tools_without_mutating_original(monkeypatch):
    monkeypatch.setattr(settings, "TOOL_ALLOWLIST", ["Read"])
    request = make_request(
        tools=[
            {"name": "Read", "input_schema": {"type": "object"}},
            {"name": "WebSearch", "input_schema": {"type": "object"}},
        ]
    )

    filtered = RequestHandler()._filter_tools(request)

    assert [tool["name"] for tool in filtered.tools] == ["Read"]
    assert [tool["name"] for tool in request.tools] == ["Read", "WebSearch"]


def test_forced_tool_is_kept_even_outside_allowlist(monkeypatch):
    monkeypatch.setattr(settings, "TOOL_ALLOWLIST", ["Read"])
    request = make_request(
        tools=[{"name": "WebSearch", "input_schema": {"type": "object"}}],
        tool_choice={"type": "tool", "name": "WebSearch"},
    )

    filtered = RequestHandler()._filter_tools(request)

    assert filtered.tools[0]["name"] == "WebSearch"
    assert filtered.tool_choice.name == "WebSearch"


def test_missing_forced_tool_is_rejected():
    request = make_request(tool_choice={"type": "tool", "name": "Write"})

    with pytest.raises(Exception) as error:
        RequestHandler()._filter_tools(request)

    assert getattr(error.value, "status_code", None) == 400


def test_openai_conversion_preserves_system_tool_use_and_tool_result():
    request = make_request(
        system="Use tools.",
        messages=[
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "Read",
                        "input": {"file_path": "README.md"},
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "conteúdo",
                    }
                ],
            },
        ],
    )
    adapter = OpenAICompatibleAdapter("test")

    messages = adapter._anthropic_messages_to_openai(request)

    assert messages[0]["role"] == "system"
    assert messages[0]["content"].startswith("Use tools.")
    assert messages[1]["tool_calls"][0]["id"] == "toolu_1"
    assert messages[2] == {
        "role": "tool",
        "tool_call_id": "toolu_1",
        "content": "conteúdo",
    }


def test_fragmented_tool_call_is_reassembled():
    adapter = OpenAICompatibleAdapter("test")
    pending = {}
    adapter._merge_tool_deltas(
        pending,
        [
            {
                "index": 0,
                "id": "call_1",
                "function": {"name": "Read", "arguments": '{"file_'},
            }
        ],
    )
    adapter._merge_tool_deltas(
        pending,
        [{"index": 0, "function": {"arguments": 'path":"README.md"}'}}],
    )

    completed = adapter._complete_tool_calls(pending)

    assert completed[0]["id"] == "call_1"
    assert completed[0]["function"]["name"] == "Read"
    assert json.loads(completed[0]["function"]["arguments"]) == {"file_path": "README.md"}


def test_action_request_requires_native_tool_call_and_blocks_simulation():
    adapter = OpenAICompatibleAdapter("test")
    request = make_request(
        messages=[
            {
                "role": "user",
                "content": "Try again to create the ADR files and commit the adjustments",
            }
        ],
        tool_choice={"type": "auto"},
    )

    body = adapter._request_body(request, "test-model")

    assert body["tool_choice"] == "required"
    assert "native structured tool_calls" in body["messages"][0]["content"]
    assert "Never print simulated commands" in body["messages"][0]["content"]


def test_informational_request_keeps_auto_tool_choice():
    adapter = OpenAICompatibleAdapter("test")
    request = make_request(
        messages=[{"role": "user", "content": "What is an ADR?"}],
        tool_choice={"type": "auto"},
    )

    body = adapter._request_body(request, "test-model")

    assert body["tool_choice"] == "auto"


def test_required_action_rejects_text_only_provider_response():
    adapter = OpenAICompatibleAdapter("test")

    with pytest.raises(ProviderError) as error:
        adapter._ensure_required_tool_call({"tool_choice": "required"}, [])

    assert error.value.status_code == 502
    assert error.value.category == "missing_tool_call"


def test_anthropic_sse_uses_unique_indexes_and_tool_use_stop_reason():
    async def events():
        yield {"type": "text", "text": "Vou ler."}
        yield {
            "type": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "arguments": '{"file_path":"README.md"}',
                    },
                }
            ],
        }
        yield {"type": "finish", "stop_reason": "tool_use"}

    async def collect():
        return [event async for event in normalize_to_anthropic_sse(events())]

    output = "".join(asyncio.run(collect()))

    assert '"type": "tool_use"' in output
    assert '"index": 0, "content_block": {"type": "text"' in output
    assert '"index": 1, "content_block": {"type": "tool_use"' in output
    assert '"stop_reason": "tool_use"' in output


def test_numbered_nvidia_models_allow_gaps_and_remove_duplicates(monkeypatch):
    for key in list(__import__("os").environ):
        if key.startswith("NVIDIA_NIM_MODEL"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("NVIDIA_NIM_MODEL1", "model-a")
    monkeypatch.setenv("NVIDIA_NIM_MODEL3", "model-b")
    monkeypatch.setenv("NVIDIA_NIM_MODEL10", "model-a")

    configured = Settings()

    assert configured.NVIDIA_NIM_MODELS == ["model-a", "model-b"]


def test_404_before_content_fails_over_to_next_provider(monkeypatch):
    attempts = []

    class FailingAdapter:
        async def stream(self, **kwargs):
            attempts.append("nvidia_nim")
            raise ProviderError(
                "nvidia_nim", "model not found", status_code=404, category="http_error"
            )
            yield

    class SuccessfulAdapter:
        async def stream(self, **kwargs):
            attempts.append("open_router")
            yield {
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "Read",
                            "arguments": '{"file_path":"README.md"}',
                        },
                    }
                ],
            }
            yield {"type": "finish", "stop_reason": "tool_use"}

    class Registry:
        adapters = {
            "nvidia_nim": FailingAdapter(),
            "open_router": SuccessfulAdapter(),
        }

        def get_adapter(self, name):
            return self.adapters[name]

    handler = RequestHandler()
    handler.provider_registry = Registry()
    monkeypatch.setattr(
        handler.model_router,
        "resolve_route",
        lambda _model: ["nvidia_nim/bad-model", "open_router/good-model"],
    )
    monkeypatch.setattr(settings, "PROVIDER_MAX_RETRIES", 1)

    async def collect():
        return [event async for event in handler.handle_request(make_request(), "sonnet")]

    events = asyncio.run(collect())

    assert attempts == ["nvidia_nim", "open_router"]
    assert events[0]["tool_calls"][0]["function"]["name"] == "Read"
    assert events[-1]["stop_reason"] == "tool_use"
