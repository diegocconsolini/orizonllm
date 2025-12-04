"""Tests for Orizon structured logging.

Tests JSON formatting, redaction, and request ID tracking.
"""

import json
import logging
import pytest
from unittest.mock import patch

from orizon.logging import (
    redact_sensitive,
    OrizonJsonFormatter,
    OrizonTextFormatter,
    set_request_id,
    get_request_id,
    LogContext,
    TimedOperation,
)


class TestRedactSensitive:
    """Test sensitive data redaction."""

    def test_redacts_password(self):
        """Should redact password fields."""
        data = {"username": "test", "password": "secret123"}
        result = redact_sensitive(data)

        assert result["username"] == "test"
        assert result["password"] == "secr***"

    def test_redacts_api_key(self):
        """Should redact API key fields."""
        data = {"api_key": "sk-1234567890abcdef"}
        result = redact_sensitive(data)

        assert result["api_key"] == "sk-1***"

    def test_redacts_nested_secrets(self):
        """Should redact secrets in nested structures."""
        data = {
            "config": {
                "database": {
                    "password": "db-password-123"
                }
            }
        }
        result = redact_sensitive(data)

        assert result["config"]["database"]["password"] == "db-p***"

    def test_redacts_in_lists(self):
        """Should redact secrets in lists."""
        data = {
            "users": [
                {"name": "Alice", "token": "token-12345"},
                {"name": "Bob", "token": "token-67890"},
            ]
        }
        result = redact_sensitive(data)

        assert result["users"][0]["name"] == "Alice"
        assert result["users"][0]["token"] == "toke***"
        assert result["users"][1]["token"] == "toke***"

    def test_handles_short_values(self):
        """Should handle short secret values."""
        data = {"password": "abc"}
        result = redact_sensitive(data)

        assert result["password"] == "***"

    def test_preserves_non_sensitive(self):
        """Should preserve non-sensitive data."""
        data = {"email": "test@example.com", "name": "Test User"}
        result = redact_sensitive(data)

        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"


class TestRequestIdTracking:
    """Test request ID context variable."""

    def test_set_and_get_request_id(self):
        """Should set and retrieve request ID."""
        set_request_id("req-12345")
        assert get_request_id() == "req-12345"

    def test_request_id_defaults_to_none(self):
        """Should return None when not set."""
        # Reset by setting to None manually (or new thread)
        from orizon.logging import request_id_var
        request_id_var.set(None)

        assert get_request_id() is None


class TestLogContext:
    """Test log context manager."""

    def test_adds_context_fields(self):
        """Should add fields to context."""
        with LogContext(user_id="123", action="login"):
            context = LogContext.get_context()
            assert context["user_id"] == "123"
            assert context["action"] == "login"

    def test_restores_context_on_exit(self):
        """Should restore context after exit."""
        with LogContext(temp_field="temporary"):
            assert LogContext.get_context()["temp_field"] == "temporary"

        # After exit, should not have the field
        assert "temp_field" not in LogContext.get_context()

    def test_nested_contexts(self):
        """Should handle nested contexts."""
        with LogContext(outer="value1"):
            assert LogContext.get_context()["outer"] == "value1"

            with LogContext(inner="value2"):
                context = LogContext.get_context()
                assert context["outer"] == "value1"
                assert context["inner"] == "value2"

            # Inner should be gone
            assert "inner" not in LogContext.get_context()
            assert LogContext.get_context()["outer"] == "value1"


class TestTimedOperation:
    """Test timed operation context manager."""

    def test_records_duration(self):
        """Should record operation duration."""
        with TimedOperation("test_op") as op:
            import time
            time.sleep(0.01)  # 10ms

        assert op.extra_fields["duration_seconds"] >= 0.01
        assert op.extra_fields["status"] == "success"

    def test_records_error_status(self):
        """Should record error status on exception."""
        op = TimedOperation("test_op")
        try:
            with op:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert op.extra_fields["status"] == "error"
        assert "Test error" in op.extra_fields["error"]

    def test_allows_adding_fields(self):
        """Should allow adding custom fields."""
        with TimedOperation("query_op") as op:
            op.add_field("rows", 100)
            op.add_field("table", "users")

        assert op.extra_fields["rows"] == 100
        assert op.extra_fields["table"] == "users"


class TestOrizonJsonFormatter:
    """Test JSON log formatter."""

    def test_formats_as_json(self):
        """Should format log record as JSON."""
        formatter = OrizonJsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["source"]["line"] == 42

    def test_includes_request_id(self):
        """Should include request ID when set."""
        set_request_id("req-json-test")

        formatter = OrizonJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["request_id"] == "req-json-test"


class TestOrizonTextFormatter:
    """Test human-readable log formatter."""

    def test_formats_basic_message(self):
        """Should format basic log message."""
        formatter = OrizonTextFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "INFO" in result
        assert "test.logger" in result
        assert "Test message" in result
