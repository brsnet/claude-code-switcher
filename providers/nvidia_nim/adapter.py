"""
NVIDIA NIM provider adapter.
"""

from providers.openai_compat import OpenAICompatibleAdapter


class NVIDIANimAdapter(OpenAICompatibleAdapter):
    def __init__(self):
        super().__init__("nvidia_nim")
