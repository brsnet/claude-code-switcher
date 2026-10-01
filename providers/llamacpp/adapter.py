"""
llama.cpp provider adapter.
"""
from providers.openai_compat import OpenAICompatibleAdapter

class LlamaCppAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("llamacpp")