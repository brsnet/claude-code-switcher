"""Cerebras Inference provider adapter."""

from providers.openai_compat import OpenAICompatibleAdapter


class CerebrasAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("cerebras")
