"""
Logging configuration.

Provides a single `get_logger(name)` entrypoint that returns a logger
configured once at import time. Keeps output predictable in dev and
suitable for forwarding to a structured sink in prod.
"""
import logging
import sys
from logging import Logger

from app.core.config import get_settings

_configured = False


def _configure_once() -> None:
    global _configured
    if _configured:
        return

    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # Quiet down noisy third-party libs unless we're in DEBUG.
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "anthropic"):
        logging.getLogger(noisy).setLevel(
            logging.DEBUG if settings.log_level.upper() == "DEBUG" else logging.WARNING
        )

    _configured = True


def get_logger(name: str) -> Logger:
    _configure_once()
    return logging.getLogger(name)
