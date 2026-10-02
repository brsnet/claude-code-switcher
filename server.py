#!/usr/bin/env python
"""
Claude Code Switcher - Main server entry point.
"""

import uvicorn

from api.routes import app
from config.logging_config import configure_application_logging

configure_application_logging()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083, log_level="info")
