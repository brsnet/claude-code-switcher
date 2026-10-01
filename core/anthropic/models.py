"""
Shared Anthropic message models.
"""
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator

class ToolChoice(BaseModel):
    type: str
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
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    tools: Optional[List[Any]] = None
    tool_choice: Optional[Union[str, ToolChoice]] = None
    # Thinking mode (not standard Anthropic, but we'll keep for compatibility)
    thinking: Optional[dict] = None

    @model_validator(mode='before')
    @classmethod
    def convert_tools_format(cls, data: dict) -> dict:
        """Convert Anthropic tool format to OpenAI format if needed."""
        if 'tools' in data and data['tools']:
            converted_tools = []
            for tool in data['tools']:
                if isinstance(tool, dict):
                    # Check if it's already in OpenAI format
                    if 'type' in tool and 'function' in tool:
                        converted_tools.append(tool)
                    # Check if it's in Anthropic format
                    elif 'name' in tool:
                        # Convert Anthropic tool to OpenAI format
                        converted_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.get("name", ""),
                                "description": tool.get("description", ""),
                                "parameters": tool.get("input_schema", tool.get("parameters", {}))
                            }
                        })
                    else:
                        converted_tools.append(tool)
                else:
                    converted_tools.append(tool)
            data['tools'] = converted_tools
        return data

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