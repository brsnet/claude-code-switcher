#!/usr/bin/env python
"""
Claude Code Switcher - Main server entry point.
"""
import uvicorn
from api.routes import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8082,
        log_level="info"
    )