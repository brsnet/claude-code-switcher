"""Manual smoke request for a user-managed local server."""

import httpx

URL = "http://localhost:8083/v1/messages"
PAYLOAD = {
    "model": "claude-opus-5-5",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "tools": [
        {
            "name": "Read",
            "description": "Read a file from the local filesystem",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The absolute path to the file to read",
                    }
                },
                "required": ["file_path"],
            },
        }
    ],
}


def main() -> None:
    """Call the local endpoint only when explicitly executed by the user."""
    try:
        response = httpx.post(URL, json=PAYLOAD, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
    except httpx.RequestError as exc:
        print(f"Request failed: {exc}")


if __name__ == "__main__":
    main()
