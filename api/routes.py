"""
FastAPI routes for the Claude Code Switcher.
"""

import json
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from api.services import RequestHandler
from core.anthropic.models import ChatCompletionRequest
from core.anthropic.stream_response import normalize_to_anthropic_json, normalize_to_anthropic_sse

logger = logging.getLogger(__name__)

app = FastAPI()
request_handler = RequestHandler()


@app.get("/api/hello")
@app.head("/api/hello")
async def hello_endpoint():
    """
    Simple endpoint for health checks.
    Returns 200 OK for GET and HEAD requests.
    """
    return Response(status_code=200)


@app.post("/v1/messages")
async def handle_messages(request: Request):
    """
    Handle Anthropic Messages API requests.
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    try:
        body = await request.json()
        # Validate the request with our Pydantic model
        chat_request = ChatCompletionRequest(**body)
    except Exception as e:
        logger.error(f"Failed to parse request: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")

    # The model field in the request is the logical model (opus, sonnet, haiku) or a specific model with prefix.
    logical_model = chat_request.model
    tool_count = len(chat_request.tools or [])
    logger.info(
        "API_REQUEST: request_id=%s model=%r messages=%s tools=%s stream=%s",
        request_id,
        logical_model,
        len(chat_request.messages),
        tool_count,
        chat_request.stream,
        extra={
            "event": "API_REQUEST",
            "request_id": request_id,
            "logical_model": logical_model,
            "message_count": len(chat_request.messages),
            "tool_count": tool_count,
            "stream": chat_request.stream,
        },
    )

    # Handle streaming vs non-streaming requests
    if chat_request.stream:
        # Streaming response
        async def event_generator():
            try:
                normalized_events = request_handler.handle_request(
                    chat_request, logical_model, request_id=request_id
                )
                async for sse_event in normalize_to_anthropic_sse(normalized_events):
                    yield sse_event
            except Exception as e:
                logger.error(
                    "STREAM_ERROR: request_id=%s error=%r",
                    request_id,
                    str(e),
                    extra={"event": "STREAM_ERROR", "request_id": request_id},
                )
                # If we haven't started streaming, we can return an error response.
                # But if we have started streaming, we must send an error event.
                # For simplicity, we'll yield an error event and then break.
                # We'll create an error event in the Anthropic format.
                error_event = {
                    "type": "error",
                    "error": {"type": "internal_server_error", "message": str(e)},
                }
                yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        # Non-streaming response
        try:
            # Collect all normalized events
            normalized_events = []
            async for event in request_handler.handle_request(
                chat_request, logical_model, request_id=request_id
            ):
                normalized_events.append(event)

            # Convert to Anthropic JSON format
            response_json = normalize_to_anthropic_json(normalized_events)

            # Add the model to the response (we don't have it in the normalization function)
            # For now, we'll use the logical model, though ideally it should be the actual model used
            response_json["model"] = logical_model

            return JSONResponse(content=response_json)
        except Exception as e:
            logger.error(
                "REQUEST_ERROR: request_id=%s error=%r",
                request_id,
                str(e),
                extra={"event": "REQUEST_ERROR", "request_id": request_id},
            )
            raise HTTPException(status_code=500, detail=str(e))
