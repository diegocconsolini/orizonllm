"""
Orizon Structured Logging

Provides structured JSON logging for production environments.
Compatible with log aggregators like Elasticsearch, Datadog, etc.

Features:
- JSON-formatted logs for production
- Human-readable logs for development
- Request ID tracking
- Sensitive data redaction
- Performance timing
"""

import json
import logging
import os
import sys
import time
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Environment configuration
LOG_FORMAT = os.getenv("ORIZON_LOG_FORMAT", "json")  # json or text
LOG_LEVEL = os.getenv("ORIZON_LOG_LEVEL", "INFO").upper()
REDACT_SECRETS = os.getenv("ORIZON_REDACT_SECRETS", "true").lower() == "true"

# Fields that should be redacted in logs
SENSITIVE_FIELDS = {
    "password",
    "api_key",
    "secret",
    "token",
    "authorization",
    "cookie",
    "x-api-key",
    "virtual_key",
    "master_key",
    "salt_key",
}


def redact_sensitive(data: Any, depth: int = 0) -> Any:
    """Recursively redact sensitive data from logs.

    Args:
        data: Data to redact (dict, list, or scalar)
        depth: Current recursion depth (prevents infinite loops)

    Returns:
        Data with sensitive fields redacted
    """
    if not REDACT_SECRETS or depth > 10:
        return data

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key_lower = key.lower().replace("-", "_").replace(" ", "_")
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                if isinstance(value, str) and len(value) > 4:
                    result[key] = f"{value[:4]}***"
                else:
                    result[key] = "***"
            else:
                result[key] = redact_sensitive(value, depth + 1)
        return result

    elif isinstance(data, list):
        return [redact_sensitive(item, depth + 1) for item in data]

    return data


class OrizonJsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            extra = redact_sensitive(record.extra_fields)
            log_data.update(extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        return json.dumps(log_data)


class OrizonTextFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        # Get request ID
        request_id = request_id_var.get()
        req_id_str = f"[{request_id[:8]}]" if request_id else ""

        # Base format
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        base = f"{timestamp} {record.levelname:8} {req_id_str} {record.name}: {record.getMessage()}"

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            extra = redact_sensitive(record.extra_fields)
            if extra:
                extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
                base = f"{base} | {extra_str}"

        # Add exception info
        if record.exc_info:
            base += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return base


class OrizonLogger(logging.Logger):
    """Custom logger with extra fields support."""

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        *args,
        extra_fields: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Log with additional structured fields."""
        if extra_fields:
            # Store extra fields on the record
            old_factory = logging.getLogRecordFactory()

            def record_factory(*args, **kwargs):
                record = old_factory(*args, **kwargs)
                record.extra_fields = extra_fields
                return record

            logging.setLogRecordFactory(record_factory)
            super()._log(level, msg, args, **kwargs)
            logging.setLogRecordFactory(old_factory)
        else:
            super()._log(level, msg, args, **kwargs)

    def info_with_fields(self, msg: str, **fields):
        """Log info message with extra fields."""
        self._log_with_extra(logging.INFO, msg, extra_fields=fields)

    def warning_with_fields(self, msg: str, **fields):
        """Log warning message with extra fields."""
        self._log_with_extra(logging.WARNING, msg, extra_fields=fields)

    def error_with_fields(self, msg: str, **fields):
        """Log error message with extra fields."""
        self._log_with_extra(logging.ERROR, msg, extra_fields=fields)

    def debug_with_fields(self, msg: str, **fields):
        """Log debug message with extra fields."""
        self._log_with_extra(logging.DEBUG, msg, extra_fields=fields)


def setup_logging(
    log_format: Optional[str] = None,
    log_level: Optional[str] = None,
) -> None:
    """Configure Orizon logging.

    Args:
        log_format: Log format (json or text). Default from ORIZON_LOG_FORMAT env.
        log_level: Log level (DEBUG, INFO, WARNING, ERROR). Default from ORIZON_LOG_LEVEL env.
    """
    format_type = log_format or LOG_FORMAT
    level = log_level or LOG_LEVEL

    # Set custom logger class
    logging.setLoggerClass(OrizonLogger)

    # Get the formatter
    if format_type.lower() == "json":
        formatter = OrizonJsonFormatter()
    else:
        formatter = OrizonTextFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handler with our formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Configure Orizon loggers
    orizon_logger = logging.getLogger("orizon")
    orizon_logger.setLevel(level)


def get_logger(name: str) -> OrizonLogger:
    """Get an Orizon logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        OrizonLogger instance
    """
    return logging.getLogger(name)  # type: ignore


# --- Context Managers and Decorators ---


class LogContext:
    """Context manager for adding fields to all logs within scope.

    Usage:
        with LogContext(user_id="123", action="login"):
            logger.info("User logged in")  # Includes user_id and action
    """

    _context: ContextVar[Dict[str, Any]] = ContextVar("log_context", default={})

    def __init__(self, **fields):
        self.fields = fields
        self.token = None

    def __enter__(self):
        current = self._context.get().copy()
        current.update(self.fields)
        self.token = self._context.set(current)
        return self

    def __exit__(self, *args):
        if self.token:
            self._context.reset(self.token)

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Get current log context."""
        return cls._context.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context.

    Args:
        request_id: Unique request identifier
    """
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return request_id_var.get()


# --- Performance Logging ---


class TimedOperation:
    """Context manager for timing operations and logging duration.

    Usage:
        with TimedOperation("database_query", logger) as op:
            result = db.query(...)
            op.add_field("rows", len(result))
        # Logs: "database_query completed in 0.123s | rows=100"
    """

    def __init__(
        self,
        operation_name: str,
        logger: Optional[logging.Logger] = None,
        level: int = logging.DEBUG,
    ):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger("orizon.timing")
        self.level = level
        self.start_time: Optional[float] = None
        self.extra_fields: Dict[str, Any] = {}

    def add_field(self, key: str, value: Any) -> None:
        """Add a field to include in the completion log."""
        self.extra_fields[key] = value

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - (self.start_time or time.time())
        self.extra_fields["duration_seconds"] = round(duration, 4)
        self.extra_fields["operation"] = self.operation_name

        if exc_type:
            self.extra_fields["status"] = "error"
            self.extra_fields["error"] = str(exc_val)
            self.logger.log(
                logging.ERROR,
                f"{self.operation_name} failed after {duration:.3f}s",
            )
        else:
            self.extra_fields["status"] = "success"
            self.logger.log(
                self.level,
                f"{self.operation_name} completed in {duration:.3f}s",
            )

        return False  # Don't suppress exceptions
