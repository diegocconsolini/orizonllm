"""Tests for Orizon security middleware.

Tests security headers and CSP configuration.
"""

import pytest
from unittest.mock import MagicMock, patch

from orizon.security import (
    build_csp_header,
    get_security_headers,
    CSP_RELAXED_PATHS,
)


class TestBuildCSPHeader:
    """Test CSP header building."""

    def test_build_strict_csp(self):
        """Should build strict CSP for web pages."""
        csp = build_csp_header(strict=True)

        # Should contain key directives
        assert "default-src" in csp
        assert "script-src" in csp
        assert "frame-ancestors" in csp

    def test_build_relaxed_csp(self):
        """Should build minimal CSP for API endpoints."""
        csp = build_csp_header(strict=False)

        # Should be minimal
        assert csp == "default-src 'none'; frame-ancestors 'none'"


class TestGetSecurityHeaders:
    """Test security header generation."""

    def test_includes_basic_headers(self):
        """Should include all basic security headers."""
        headers = get_security_headers("/", is_https=True)

        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers

    def test_includes_hsts_for_https(self):
        """Should include HSTS for HTTPS requests."""
        headers = get_security_headers("/", is_https=True)

        assert "Strict-Transport-Security" in headers
        assert "max-age=" in headers["Strict-Transport-Security"]

    def test_no_hsts_for_http(self):
        """Should not include HSTS for HTTP requests."""
        with patch("orizon.security.HSTS_ENABLED", True):
            headers = get_security_headers("/", is_https=False)

            # HSTS should not be present for HTTP
            assert "Strict-Transport-Security" not in headers

    def test_x_frame_options_deny(self):
        """Should deny framing by default."""
        headers = get_security_headers("/")

        assert headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_nosniff(self):
        """Should prevent MIME sniffing."""
        headers = get_security_headers("/")

        assert headers["X-Content-Type-Options"] == "nosniff"


class TestAPIPathCSP:
    """Test CSP relaxation for API paths."""

    @pytest.mark.parametrize("path", ["/v1/models", "/v1/chat/completions", "/health", "/metrics"])
    def test_relaxed_csp_for_api_paths(self, path):
        """Should use relaxed CSP for API endpoints."""
        headers = get_security_headers(path)
        csp = headers["Content-Security-Policy"]

        # API paths should have minimal CSP
        assert csp == "default-src 'none'; frame-ancestors 'none'"

    @pytest.mark.parametrize("path", ["/", "/signup", "/login", "/profile"])
    def test_strict_csp_for_web_paths(self, path):
        """Should use strict CSP for web pages."""
        headers = get_security_headers(path)
        csp = headers["Content-Security-Policy"]

        # Web paths should have full CSP
        assert "script-src" in csp
        assert "style-src" in csp


class TestSecurityHeadersDisabled:
    """Test when security headers are disabled."""

    @patch("orizon.security.SECURITY_HEADERS_ENABLED", False)
    def test_returns_empty_when_disabled(self):
        """Should return empty dict when disabled."""
        headers = get_security_headers("/")

        assert headers == {}
