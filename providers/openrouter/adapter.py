"""
OpenRouter provider adapter.
"""

from providers.openai_compat import OpenAICompatibleAdapter


class OpenRouterAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("open_router")
