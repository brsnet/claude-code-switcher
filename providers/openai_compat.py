"""
OpenAI-compatible provider adapter base class.
"""

import json
from typing import Any, AsyncIterator, Dict, List

import httpx

from config import settings
from core.anthropic.models import ChatCompletionRequest
from providers.base import ProviderAdapter, ProviderError


class OpenAICompatibleAdapter(ProviderAdapter):
    _ACTION_WORDS = (
        "adjust",
        "apply",
        "commit",
        "create",
        "delete",
        "edit",
        "execute",
        "fix",
        "implement",
        "move",
        "perform",
        "remove",
        "rename",
        "run",
        "write",
        "ajust",
        "apliqu",
        "corrij",
        "cri",
        "edit",
        "execut",
        "implement",
        "mov",
        "remov",
        "renome",
        "rode",
    )
    _TOOL_INSTRUCTION = (
        "When a request requires reading or changing files, running commands, or checking "
        "repository state, use the supplied function tools. Emit native structured tool_calls. "
        "Never print simulated commands, fabricated terminal output, or claim that an action "
        "succeeded unless its tool result confirms it."
    )

    def __init__(self, name: str):
        super().__init__(name)

    def _anthropic_messages_to_openai(self, request: ChatCompletionRequest) -> List[Dict[str, Any]]:
        """Preserve system, text, tool calls, and tool results."""
        openai_messages: List[Dict[str, Any]] = []
        if isinstance(request.system, str) and request.system:
            openai_messages.append({"role": "system", "content": request.system})
        elif isinstance(request.system, list):
            system_text = "".join(
                str(block.get("text", ""))
                for block in request.system
                if isinstance(block, dict) and block.get("type") == "text"
            )
            if system_text:
                openai_messages.append({"role": "system", "content": system_text})

        if request.tools:
            if openai_messages and openai_messages[0]["role"] == "system":
                openai_messages[0]["content"] += f"\n\n{self._TOOL_INSTRUCTION}"
            else:
                openai_messages.insert(0, {"role": "system", "content": self._TOOL_INSTRUCTION})

        for message in request.messages:
            if isinstance(message.content, str):
                openai_messages.append({"role": message.role, "content": message.content})
                continue

            text_parts: List[str] = []
            tool_calls: List[Dict[str, Any]] = []
            tool_results: List[Dict[str, Any]] = []
            for part in message.content:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(str(part.get("text", "")))
                elif isinstance(part, dict) and part.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "id": part.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": part.get("name", ""),
                                "arguments": json.dumps(part.get("input", {}), ensure_ascii=False),
                            },
                        }
                    )
                elif isinstance(part, dict) and part.get("type") == "tool_result":
                    content = part.get("content", "")
                    if isinstance(content, list):
                        content = "".join(
                            str(block.get("text", ""))
                            for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                        )
                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": part.get("tool_use_id", ""),
                            "content": str(content),
                        }
                    )

            if message.role == "assistant":
                payload: Dict[str, Any] = {
                    "role": "assistant",
                    "content": "".join(text_parts) or None,
                }
                if tool_calls:
                    payload["tool_calls"] = tool_calls
                openai_messages.append(payload)
            else:
                if text_parts:
                    openai_messages.append({"role": message.role, "content": "".join(text_parts)})
                openai_messages.extend(tool_results)
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
                    openai_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool.get("name", ""),
                                "description": tool.get("description", ""),
                                "parameters": tool.get("input_schema", tool.get("parameters", {})),
                            },
                        }
                    )
                else:
                    # Keep as-is if we don't recognize the format
                    openai_tools.append(tool)
            else:
                # Keep as-is if not a dict
                openai_tools.append(tool)
        return openai_tools

    @staticmethod
    def _tool_choice_to_openai(choice: Any) -> Any:
        if hasattr(choice, "model_dump"):
            choice = choice.model_dump(exclude_none=True)
        if not isinstance(choice, dict):
            return choice
        choice_type = choice.get("type")
        if choice_type in {"auto", "none"}:
            return choice_type
        if choice_type == "any":
            return "required"
        if choice_type == "tool" and choice.get("name"):
            return {"type": "function", "function": {"name": choice["name"]}}
        return choice

    @staticmethod
    def _merge_tool_deltas(
        pending: Dict[int, Dict[str, Any]], deltas: List[Dict[str, Any]]
    ) -> None:
        for position, delta in enumerate(deltas):
            index = delta.get("index", position)
            if not isinstance(index, int):
                index = position
            item = pending.setdefault(
                index,
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                },
            )
            if delta.get("id"):
                item["id"] = delta["id"]
            function = delta.get("function")
            if isinstance(function, dict):
                if function.get("name"):
                    item["function"]["name"] = function["name"]
                if isinstance(function.get("arguments"), str):
                    item["function"]["arguments"] += function["arguments"]

    def _complete_tool_calls(self, pending: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
        completed = []
        for index in sorted(pending):
            item = pending[index]
            arguments = item["function"]["arguments"] or "{}"
            if not item["id"] or not item["function"]["name"]:
                raise ProviderError(
                    self.name,
                    "Provider returned an incomplete tool call",
                    status_code=502,
                    category="invalid_tool_call",
                )
            try:
                json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ProviderError(
                    self.name,
                    "Provider returned invalid tool arguments",
                    status_code=502,
                    category="invalid_tool_call",
                ) from exc
            completed.append(item)
        return completed

    @staticmethod
    def _stop_reason(reason: str | None, has_tools: bool) -> str:
        if has_tools or reason == "tool_calls":
            return "tool_use"
        if reason == "length":
            return "max_tokens"
        return "end_turn"

    @classmethod
    def _request_requires_action(cls, request: ChatCompletionRequest) -> bool:
        for message in reversed(request.messages):
            if message.role != "user":
                continue
            if isinstance(message.content, str):
                text = message.content
            else:
                text = " ".join(
                    str(block.get("text", ""))
                    for block in message.content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            normalized = text.casefold()
            return any(word in normalized for word in cls._ACTION_WORDS)
        return False

    def _request_body(self, request: ChatCompletionRequest, model: str) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": model,
            "messages": self._anthropic_messages_to_openai(request),
            "stream": request.stream,
        }
        if request.tools:
            body["tools"] = self._anthropic_tools_to_openai(request.tools)

        choice = request.tool_choice
        converted_choice = self._tool_choice_to_openai(choice) if choice is not None else None
        if (
            request.tools
            and self._request_requires_action(request)
            and (converted_choice is None or converted_choice == "auto")
        ):
            converted_choice = "required"
        if converted_choice is not None:
            body["tool_choice"] = converted_choice

        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.stop is not None:
            body["stop"] = request.stop
        return body

    def _ensure_required_tool_call(self, body: Dict[str, Any], tools: List[Dict[str, Any]]) -> None:
        if body.get("tool_choice") == "required" and not tools:
            raise ProviderError(
                self.name,
                "Provider returned text without the required structured tool call",
                status_code=502,
                category="missing_tool_call",
            )

    async def stream(
        self, request: ChatCompletionRequest, model: str, api_key: str, base_url: str, **kwargs
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

        openai_request = self._request_body(request, model)

        if not base_url:
            raise ProviderError(
                self.name,
                f"Provider {self.name} has no configured base URL",
                category="configuration",
            )
        url = f"{base_url.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_READ_TIMEOUT) as client:
                if request.stream:
                    async with client.stream(
                        "POST", url, headers=headers, json=openai_request
                    ) as response:
                        if response.status_code >= 400:
                            raw = (await response.aread()).decode(errors="replace")[:500]
                            raise ProviderError(
                                self.name,
                                f"Provider {self.name} returned {response.status_code}: {raw}",
                                status_code=response.status_code,
                                category="http_error",
                            )

                        pending: Dict[int, Dict[str, Any]] = {}
                        buffered_text: List[str] = []
                        requires_tool = openai_request.get("tool_choice") == "required"
                        finished = False
                        async for line in response.aiter_lines():
                            if not line.startswith("data:"):
                                continue
                            data = line[5:].lstrip()
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                            except json.JSONDecodeError as exc:
                                raise ProviderError(
                                    self.name,
                                    "Provider returned malformed streaming JSON",
                                    status_code=502,
                                    category="invalid_response",
                                ) from exc
                            choices = chunk.get("choices") or []
                            if not choices:
                                continue
                            choice = choices[0]
                            delta = choice.get("delta") or {}
                            content = delta.get("content")
                            if isinstance(content, str) and content:
                                if requires_tool:
                                    buffered_text.append(content)
                                else:
                                    yield {"type": "text", "text": content}
                            tool_deltas = delta.get("tool_calls")
                            if isinstance(tool_deltas, list):
                                self._merge_tool_deltas(pending, tool_deltas)
                            finish_reason = choice.get("finish_reason")
                            if finish_reason is not None:
                                tools = self._complete_tool_calls(pending)
                                self._ensure_required_tool_call(openai_request, tools)
                                for text in buffered_text:
                                    yield {"type": "text", "text": text}
                                if tools:
                                    yield {"type": "tool_calls", "tool_calls": tools}
                                yield {
                                    "type": "finish",
                                    "stop_reason": self._stop_reason(finish_reason, bool(tools)),
                                }
                                finished = True
                        if not finished:
                            tools = self._complete_tool_calls(pending)
                            self._ensure_required_tool_call(openai_request, tools)
                            for text in buffered_text:
                                yield {"type": "text", "text": text}
                            if tools:
                                yield {"type": "tool_calls", "tool_calls": tools}
                            yield {
                                "type": "finish",
                                "stop_reason": self._stop_reason(None, bool(tools)),
                            }
                    return

                response = await client.post(url, headers=headers, json=openai_request)
                if response.status_code >= 400:
                    raise ProviderError(
                        self.name,
                        f"Provider {self.name} returned {response.status_code}: {response.text[:500]}",
                        status_code=response.status_code,
                        category="http_error",
                    )
                try:
                    chunk = response.json()
                    choice = chunk["choices"][0]
                    message = choice.get("message") or {}
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    raise ProviderError(
                        self.name,
                        "Provider returned an invalid completion response",
                        status_code=502,
                        category="invalid_response",
                    ) from exc
                content = message.get("content")
                tools = message.get("tool_calls") or []
                if tools:
                    tools = self._complete_tool_calls(
                        {index: item for index, item in enumerate(tools)}
                    )
                self._ensure_required_tool_call(openai_request, tools)
                if isinstance(content, str) and content:
                    yield {"type": "text", "text": content}
                if tools:
                    yield {"type": "tool_calls", "tool_calls": tools}
                yield {
                    "type": "finish",
                    "stop_reason": self._stop_reason(choice.get("finish_reason"), bool(tools)),
                }
        except ProviderError:
            raise
        except httpx.RequestError as exc:
            raise ProviderError(
                self.name,
                f"Failed to connect to provider {self.name}",
                status_code=503,
                category="connection",
            ) from exc
