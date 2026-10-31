"""
Tests for centralized configuration and settings parsing.
"""

from backend.app.core.config import Settings


def test_cors_origins_parsing_list():
    """Verifies that CORS origins correctly parses lists."""
    settings = Settings(CORS_ORIGINS=["http://example.com", "http://app.local"])
    assert settings.CORS_ORIGINS == ["http://example.com", "http://app.local"]


def test_cors_origins_parsing_comma_separated_string():
    """Verifies that comma-separated strings are parsed into lists."""
    settings = Settings(CORS_ORIGINS="http://site1.org, http://site2.org")
    assert settings.CORS_ORIGINS == ["http://site1.org", "http://site2.org"]


def test_cors_origins_wildcard():
    """Verifies wildcard origin parsing."""
    settings = Settings(CORS_ORIGINS="*")
    assert settings.CORS_ORIGINS == ["*"]


def test_upload_limit_default():
    """Verifies default upload limit is 500 MB."""
    settings = Settings()
    assert settings.MAX_UPLOAD_SIZE_BYTES == 524_288_000

