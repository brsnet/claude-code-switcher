"""Cloudflare Workers AI provider adapter."""

from providers.openai_compat import OpenAICompatibleAdapter


class CloudflareAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("cloudflare")
