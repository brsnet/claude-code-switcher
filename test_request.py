import json
import requests

# Test the fixed server with a Claude Code-like request
url = "http://localhost:8083/v1/messages"

# Sample request similar to what Claude Code sends
payload = {
    "model": "claude-opus-5-5",  # This should now be mapped to "opus"
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

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
except Exception as e:
    print(f"Error: {e}")
