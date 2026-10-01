"""
OpenAI-compatible provider adapter base class.
"""
import json
from typing import AsyncIterator, Dict, Any, List, Union
import httpx
from providers.base import ProviderAdapter, ProviderHTTPError
from core.anthropic.models import ChatCompletionRequest, Message
from config import settings


class OpenAICompatibleAdapter(ProviderAdapter):
    def __init__(self, name: str):
        super().__init__(name)

    def _anthropic_messages_to_openai(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Anthropic messages to OpenAI format."""
        openai_messages = []
        for message in messages:
            # We assume the content is a string for simplicity.
            # If it's a list, we'll take the first text part? We'll just convert to string.
            if isinstance(message.content, str):
                content = message.content
            else:
                # It's a list; we'll extract text parts.
                text_parts = []
                for part in message.content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                content = "".join(text_parts)
            openai_messages.append({
                "role": message.role,
                "content": content,
            })
        return openai_messages

    def _anthropic_tools_to_openai(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert Anthropic tools format to OpenAI tools format."""
        if not tools:
            return []

        openai_tools = []
        for tool in tools:
            if isinstance(tool, dict):
                # Check if it's already in OpenAI format
                if tool.get("type") == "function" and "function" in tool:
                    openai_tools.append(tool)
                # Check if it's in Anthropic format
                elif "name" in tool:
                    # Convert Anthropic tool to OpenAI format
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.get("name", ""),
                            "description": tool.get("description", ""),
                            "parameters": tool.get("input_schema", tool.get("parameters", {}))
                        }
                    })
                else:
                    # Keep as-is if we don't recognize the format
                    openai_tools.append(tool)
            else:
                # Keep as-is if not a dict
                openai_tools.append(tool)
        return openai_tools

    async def stream(
        self,
        request: ChatCompletionRequest,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream a request to an OpenAI-compatible provider.

        :param request: The normalized Anthropic request.
        :param model: The model identifier to use.
        :param api_key: The API key for authentication.
        :param base_url: The base URL of the provider's API.
        :param kwargs: Additional provider-specific arguments.
        :return: An async iterator of normalized events (to be converted to SSE by the core).
        """
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Prepare the request body in OpenAI format
        openai_request = {
            "model": model,
            "messages": self._anthropic_messages_to_openai(request.messages),
            "stream": request.stream,
        }

        # Add tools if present
        if request.tools:
            openai_request["tools"] = self._anthropic_tools_to_openai(request.tools)

        # Add tool_choice if present
        if request.tool_choice:
            # Convert Anthropic tool_choice to OpenAI format if needed
            if isinstance(request.tool_choice, dict) and "type" in request.tool_choice:
                # Already in OpenAI-like format or Anthropic format
                if request.tool_choice.get("type") == "function" and "function" in request.tool_choice:
                    openai_request["tool_choice"] = request.tool_choice
                else:
                    # Might be Anthropic format, convert if needed
                    openai_request["tool_choice"] = request.tool_choice
            else:
                # String value like "auto", "none", etc.
                openai_request["tool_choice"] = request.tool_choice

        if request.temperature is not None:
            openai_request["temperature"] = request.temperature
        if request.top_p is not None:
            openai_request["top_p"] = request.top_p
        if request.max_tokens is not None:
            openai_request["max_tokens"] = request.max_tokens
        if request.stop is not None:
            openai_request["stop"] = request.stop

        # Make the HTTP request
        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_READ_TIMEOUT) as client:
                # Validate base_url
                if not base_url:
                    raise Exception(f"Provider {self.name} has no configured base URL")

                # Construct the endpoint URL
                url = f"{base_url.rstrip('/')}/chat/completions"

                if request.stream:
                    # Handle streaming response
                    try:
                        async with client.stream(
                            "POST",
                            url,
                            headers=headers,
                            json=openai_request,
                        ) as response:
                            if response.status_code >= 400:
                                # Raise ProviderHTTPError with the status code
                                text = await response.aread()
                                raise ProviderHTTPError(
                                    f"Provider {self.name} returned {response.status_code}: {text.decode()}",
                                    status_code=response.status_code
                                )

                            # Process the streaming response
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    data = line[6:]
                                    if data.strip() == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(data)
                                        # Convert OpenAI chunk to our normalized event format.
                                        # We'll define a normalized event as a dict with a 'type' key.
                                        # For now, we only handle text delta.
                                        if 'choices' in chunk and len(chunk['choices']) > 0:
                                            delta = chunk['choices'][0].get('delta', {})
                                            content = delta.get('content')
                                            if content is not None:
                                                yield {
                                                    "type": "text",
                                                    "text": content,
                                                }
                                            # Handle tool calls
                                            if 'tool_calls' in delta:
                                                yield {
                                                    "type": "tool_calls",
                                                    "tool_calls": delta['tool_calls']
                                                }
                                    except json.JSONDecodeError:
                                        # Ignore invalid JSON
                                        pass
                    except httpx.RequestError as e:
                        raise Exception(f"Failed to connect to {self.name} at {url}: {str(e)}")
                else:
                    # Handle non-streaming response
                    try:
                        response = await client.post(
                            url,
                            headers=headers,
                            json=openai_request,
                        )
                        if response.status_code >= 400:
                            # Raise ProviderHTTPError with the status code
                            text = await response.aread()
                            raise ProviderHTTPError(
                                f"Provider {self.name} returned {response.status_code}: {text.decode()}",
                                status_code=response.status_code
                            )

                        # Process the non-streaming response
                        try:
                            chunk = response.json()
                            # Convert OpenAI response to our normalized event format.
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                choice = chunk['choices'][0]
                                # Extract message content
                                message = choice.get('message', {})
                                content = message.get('content')
                                if content is not None:
                                    yield {
                                        "type": "text",
                                        "text": content,
                                    }
                                # Handle tool calls
                                tool_calls = message.get('tool_calls', [])
                                if tool_calls:
                                    yield {
                                        "type": "tool_calls",
                                        "tool_calls": tool_calls
                                    }
                                # Add finish event
                                yield {
                                    "type": "finish",
                                    "stop_reason": choice.get('finish_reason', 'stop')
                                }
                        except Exception as e:
                            # Catch any exception during response processing and wrap it with context
                            raise Exception(f"Failed to process response from {self.name}: {str(e)}")
                    except httpx.RequestError as e:
                        raise Exception(f"Failed to connect to {self.name} at {url}: {str(e)}")
        except Exception as e:
            # Catch any exception during client initialization or request setup
            # Re-raise ProviderHTTPError as-is, wrap others
            if isinstance(e, ProviderHTTPError):
                raise
            raise Exception(f"Failed to initialize HTTP client for {self.name}: {str(e)}")