"""Groq provider adapter."""

from providers.openai_compat import OpenAICompatibleAdapter


class GroqAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("groq")
