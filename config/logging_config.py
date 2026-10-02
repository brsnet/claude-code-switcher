"""Terminal logging configuration for application namespaces."""

from __future__ import annotations

import logging

_HANDLER_MARKER = "claude_code_switcher_terminal"


def configure_application_logging(level: int = logging.INFO) -> None:
    """Make application INFO logs visible when the app is loaded by Uvicorn."""
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    for namespace in ("api", "providers", "config"):
        logger = logging.getLogger(namespace)
        logger.setLevel(level)
        logger.propagate = False

        if any(getattr(handler, "name", None) == _HANDLER_MARKER for handler in logger.handlers):
            continue

        handler = logging.StreamHandler()
        handler.name = _HANDLER_MARKER
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
