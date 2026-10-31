"""
Structured logging module for Veritas.

Provides JSON-like formatted logging with automated redaction of sensitive credentials and tokens.
"""

import logging
import re
import sys
from typing import Any, Dict


SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]+"), r"\1[REDACTED_JWT]"),
    (re.compile(r"(password['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", re.IGNORECASE), r"\1[REDACTED_PASSWORD]\2"),
    (re.compile(r"(secret_key['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", re.IGNORECASE), r"\1[REDACTED_SECRET]\2"),
    (re.compile(r"(access_key['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", re.IGNORECASE), r"\1[REDACTED_KEY]\2"),
]


class RedactingFormatter(logging.Formatter):
    """Custom log formatter that masks sensitive tokens and credentials."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern, replacement in SENSITIVE_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures root logger with redaction formatter."""
    logger = logging.getLogger("veritas")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = RedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()

