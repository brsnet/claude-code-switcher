"""
LM Studio provider adapter.
"""

from providers.openai_compat import OpenAICompatibleAdapter


class LMStudioAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("lmstudio")
