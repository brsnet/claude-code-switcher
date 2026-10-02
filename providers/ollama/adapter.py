"""
Ollama provider adapter.
"""

from providers.openai_compat import OpenAICompatibleAdapter


class OllamaAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("ollama")
