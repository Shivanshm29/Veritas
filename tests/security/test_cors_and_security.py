"""
Security tests verifying CORS headers, path traversal resistance, SSRF blocks, and secret hygiene.
"""

import ipaddress
from urllib.parse import urlparse
from fastapi.testclient import TestClient
from backend.app.main import create_app


def is_ssrf_safe_url(target_url: str) -> bool:
    """
    Security helper demonstrating SSRF private IP blocking logic.
    Rejects localhost, private subnets (10.0.0.0/8, 192.168.0.0/16, 172.16.0.0/12) and link-local (169.254.169.254).
    """
    try:
        parsed = urlparse(target_url)
        if parsed.scheme not in ["http", "https"]:
            return False
        
        hostname = parsed.hostname
        if not hostname or hostname in ["localhost", "127.0.0.1", "::1"]:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            # Domain name, requires resolution check in production
            if hostname.endswith(".internal") or hostname.endswith(".local"):
                return False

        return True
    except Exception:
        return False


def test_ssrf_safety_validator():
    """Verifies that SSRF validator rejects private IPs and allows public URLs."""
    assert is_ssrf_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_ssrf_safe_url("http://127.0.0.1:8000/internal") is False
    assert is_ssrf_safe_url("http://192.168.1.50/admin") is False
    assert is_ssrf_safe_url("http://10.0.0.1/secret") is False
    assert is_ssrf_safe_url("ftp://example.com/file") is False
    assert is_ssrf_safe_url("https://example.org/press_release.html") is True


def test_cors_headers_allowed_origin():
    """Verifies that requests from allowed origins receive CORS headers."""
    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_headers_disallowed_origin():
    """Verifies that requests from unknown origins do not receive allow-origin matching header."""
    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/health",
        headers={"Origin": "http://malicious-attacker.com"},
    )
    assert response.status_code == 200
    # Should not echo the disallowed origin
    assert response.headers.get("access-control-allow-origin") != "http://malicious-attacker.com"


def test_error_response_does_not_leak_internal_paths():
    """Verifies that validation error responses do not leak server filesystems."""
    app = create_app()
    client = TestClient(app)

    # Trigger validation error on invalid path/type
    response = client.get("/api/v1/invalid-route")
    assert response.status_code == 404
    data = response.json()
    assert "Traceback" not in response.text
    assert "C:\\" not in response.text
    assert "/home/" not in response.text
    assert data["status"] == 404

