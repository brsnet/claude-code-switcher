"""
FastAPI routes for the Claude Code Switcher.
"""
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from core.anthropic.models import ChatCompletionRequest
from api.services import RequestHandler
from core.anthropic.stream_response import normalize_to_anthropic_sse, normalize_to_anthropic_json
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
request_handler = RequestHandler()

@app.post("/v1/messages")
async def handle_messages(request: Request):
    """
    Handle Anthropic Messages API requests.
    """
    try:
        body = await request.json()
        # Validate the request with our Pydantic model
        chat_request = ChatCompletionRequest(**body)
    except Exception as e:
        logger.error(f"Failed to parse request: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")

    # The model field in the request is the logical model (opus, sonnet, haiku) or a specific model with prefix.
    logical_model = chat_request.model

    # Handle streaming vs non-streaming requests
    if chat_request.stream:
        # Streaming response
        async def event_generator():
            try:
                normalized_events = request_handler.handle_request(chat_request, logical_model)
                async for sse_event in normalize_to_anthropic_sse(normalized_events):
                    yield sse_event
            except Exception as e:
                logger.error(f"Error handling streaming request: {e}")
                # If we haven't started streaming, we can return an error response.
                # But if we have started streaming, we must send an error event.
                # For simplicity, we'll yield an error event and then break.
                # We'll create an error event in the Anthropic format.
                error_event = {
                    "type": "error",
                    "error": {
                        "type": "internal_server_error",
                        "message": str(e)
                    }
                }
                yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        # Non-streaming response
        try:
            # Collect all normalized events
            normalized_events = []
            async for event in request_handler.handle_request(chat_request, logical_model):
                normalized_events.append(event)

            # Convert to Anthropic JSON format
            response_json = normalize_to_anthropic_json(normalized_events)

            # Add the model to the response (we don't have it in the normalization function)
            # For now, we'll use the logical model, though ideally it should be the actual model used
            response_json["model"] = logical_model

            return JSONResponse(content=response_json)
        except Exception as e:
            logger.error(f"Error handling non-streaming request: {e}")
            raise HTTPException(status_code=500, detail=str(e))