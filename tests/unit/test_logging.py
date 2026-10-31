"""
Unit tests for structured logging and sensitive credential masking.
"""

import logging
from backend.app.core.logging import RedactingFormatter


def test_redacting_formatter_masks_bearer_jwt():
    """Verifies that Bearer JWT tokens are redacted from log messages."""
    formatter = RedactingFormatter(fmt="%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="User authenticated with header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secretpayload.signature",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "Bearer [REDACTED_JWT]" in output
    assert "secretpayload" not in output


def test_redacting_formatter_masks_passwords():
    """Verifies that password values in logs are masked."""
    formatter = RedactingFormatter(fmt="%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Connecting with config: password='super_secret_db_password'",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "[REDACTED_PASSWORD]" in output
    assert "super_secret_db_password" not in output

