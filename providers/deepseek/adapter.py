"""
DeepSeek provider adapter.
"""
from providers.openai_compat import OpenAICompatibleAdapter

class DeepSeekAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("deepseek")