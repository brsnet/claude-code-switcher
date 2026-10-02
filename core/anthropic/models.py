"""
Shared Anthropic message models.
"""

from typing import Any, List, Optional, Union

from pydantic import BaseModel


class ToolChoice(BaseModel):
    type: str
    name: Optional[str] = None
    function: Optional[dict] = None


class Tool(BaseModel):
    type: str
    function: dict


class Message(BaseModel):
    role: str
    content: Union[str, List[Union[str, dict]]]


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    system: Optional[Union[str, List[dict]]] = None
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    tools: Optional[List[Any]] = None
    tool_choice: Optional[Union[str, ToolChoice]] = None
    # Thinking mode (not standard Anthropic, but we'll keep for compatibility)
    thinking: Optional[dict] = None

    # Keep tools in Anthropic format until provider-specific serialization.


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: Optional[dict] = None


class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[dict]
