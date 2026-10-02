"""Google Gemini OpenAI-compatible provider adapter."""

from providers.openai_compat import OpenAICompatibleAdapter


class GeminiAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("gemini")
