import asyncio
import logging

import pytest

from api.model_router import ModelRouter
from api.services import RequestHandler
from config.settings import Settings
from core.anthropic.models import ChatCompletionRequest
from providers import registry

FREE_PROVIDERS = ("groq", "gemini", "cerebras", "cloudflare")


@pytest.mark.parametrize("provider", FREE_PROVIDERS)
def test_free_provider_is_registered(provider):
    assert registry.has_adapter(provider)
    assert registry.get_adapter(provider).name == provider


def test_numbered_models_are_discovered_for_each_free_provider(monkeypatch):
    prefixes = ("GROQ", "GEMINI", "CEREBRAS", "CLOUDFLARE")
    for prefix in prefixes:
        monkeypatch.delenv(f"{prefix}_MODEL", raising=False)
        for index in range(1, 11):
            monkeypatch.setenv(f"{prefix}_MODEL{index}", "")
        monkeypatch.setenv(f"{prefix}_MODEL1", f"{prefix.lower()}-a")
        monkeypatch.setenv(f"{prefix}_MODEL3", f"{prefix.lower()}-b")

    configured = Settings()

    assert configured.GROQ_MODELS == ["groq-a", "groq-b"]
    assert configured.GEMINI_MODELS == ["gemini-a", "gemini-b"]
    assert configured.CEREBRAS_MODELS == ["cerebras-a", "cerebras-b"]
    assert configured.CLOUDFLARE_MODELS == ["cloudflare-a", "cloudflare-b"]


def test_openrouter_discards_paid_models_and_falls_back_to_free_router(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "paid/model")
    monkeypatch.setenv("OPENROUTER_MODEL1", "another/paid-model")

    configured = Settings()

    assert configured.OPENROUTER_MODELS == ["openrouter/free"]
    assert configured.OPENROUTER_MODEL == "openrouter/free"


def test_openrouter_accepts_only_explicit_free_variants(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setenv("OPENROUTER_MODEL1", "example/coder:free")
    monkeypatch.setenv("OPENROUTER_MODEL2", "example/paid")

    configured = Settings()

    assert configured.OPENROUTER_MODELS == ["openrouter/free", "example/coder:free"]


def test_explicit_paid_openrouter_candidate_is_rejected(monkeypatch):
    router = ModelRouter()
    monkeypatch.setattr(router.settings, "ROUTER_SONNET", ["open_router/example/paid"])

    with pytest.raises(ValueError, match="must use openrouter/free"):
        router.resolve_route("sonnet")


def test_cloudflare_base_url_is_derived_from_account_id(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_BASE_URL", raising=False)
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account-123")

    configured = Settings()

    assert configured.CLOUDFLARE_BASE_URL == (
        "https://api.cloudflare.com/client/v4/accounts/account-123/ai/v1"
    )


@pytest.mark.parametrize("provider", FREE_PROVIDERS)
def test_route_log_shows_free_provider_and_concrete_model(provider, monkeypatch, caplog):
    class SuccessfulAdapter:
        async def stream(self, **kwargs):
            yield {"type": "text", "text": "ok"}
            yield {"type": "finish", "stop_reason": "end_turn"}

    class Registry:
        def get_adapter(self, _name):
            return SuccessfulAdapter()

    handler = RequestHandler()
    handler.provider_registry = Registry()
    candidate = f"{provider}/test-free-model"
    monkeypatch.setattr(handler.model_router, "resolve_route", lambda _model: [candidate])
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
                request, request.model, request_id=f"req_{provider}"
            )
        ]

    with caplog.at_level(logging.INFO, logger="api.services"):
        asyncio.run(collect())

    route_record = next(record for record in caplog.records if record.event == "ROUTE")
    assert f"provider={provider}" in route_record.getMessage()
    assert "model='test-free-model'" in route_record.getMessage()
    assert route_record.provider == provider
    assert route_record.model == "test-free-model"
