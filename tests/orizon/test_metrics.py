"""Tests for Orizon Prometheus metrics.

Tests metric recording and initialization.
"""

import pytest
from unittest.mock import MagicMock, patch

from orizon.metrics import (
    record_auth_request,
    record_auth_latency,
    record_rate_limit_hit,
    record_oauth_flow,
    record_magic_link,
    track_auth_endpoint,
    MetricsTimer,
)


class TestMetricRecording:
    """Test basic metric recording functions."""

    @patch("orizon.metrics._init_metrics", return_value=False)
    def test_graceful_noop_when_disabled(self, mock_init):
        """Should be a no-op when metrics disabled."""
        # These should not raise
        record_auth_request("login", "POST", "success")
        record_auth_latency("login", 0.5)
        record_rate_limit_hit("/api/auth/login", "login")
        record_oauth_flow("github", "success")
        record_magic_link("signup", "sent")


class TestMetricsTimer:
    """Test MetricsTimer context manager."""

    @patch("orizon.metrics.record_auth_latency")
    def test_records_latency_on_success(self, mock_record):
        """Should record latency on successful completion."""
        with MetricsTimer("test_endpoint"):
            pass  # Simulate some work

        # Should have recorded latency
        mock_record.assert_called_once()
        args = mock_record.call_args[0]
        assert args[0] == "test_endpoint"
        assert args[1] >= 0  # Latency should be non-negative

    @patch("orizon.metrics.record_auth_latency")
    def test_records_latency_on_exception(self, mock_record):
        """Should record latency even on exception."""
        with pytest.raises(ValueError):
            with MetricsTimer("error_endpoint"):
                raise ValueError("Test error")

        # Should still have recorded latency
        mock_record.assert_called_once()

    def test_status_success_on_normal_exit(self):
        """Should set status to success on normal exit."""
        timer = MetricsTimer("test")
        with timer:
            pass

        assert timer.status == "success"

    def test_status_error_on_exception(self):
        """Should set status to error on exception."""
        timer = MetricsTimer("test")
        with pytest.raises(ValueError):
            with timer:
                raise ValueError("Test")

        assert timer.status == "error"


class TestTrackAuthEndpointDecorator:
    """Test track_auth_endpoint decorator."""

    @pytest.mark.asyncio
    @patch("orizon.metrics.record_auth_request")
    @patch("orizon.metrics.record_auth_latency")
    async def test_tracks_successful_request(self, mock_latency, mock_request):
        """Should track successful request."""

        @track_auth_endpoint("login")
        async def login_handler():
            return {"success": True}

        result = await login_handler()

        assert result == {"success": True}
        mock_request.assert_called_once_with("login", "POST", "success")
        mock_latency.assert_called_once()

    @pytest.mark.asyncio
    @patch("orizon.metrics.record_auth_request")
    @patch("orizon.metrics.record_auth_latency")
    async def test_tracks_failed_request(self, mock_latency, mock_request):
        """Should track failed request."""

        @track_auth_endpoint("login")
        async def login_handler():
            raise Exception("Login failed")

        with pytest.raises(Exception):
            await login_handler()

        mock_request.assert_called_once_with("login", "POST", "error")
        mock_latency.assert_called_once()


class TestRateLimitMetric:
    """Test rate limit metric recording."""

    @patch("orizon.metrics._init_metrics", return_value=True)
    @patch("orizon.metrics._rate_limit_hits")
    def test_increments_rate_limit_counter(self, mock_counter, mock_init):
        """Should increment rate limit counter with correct labels."""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        record_rate_limit_hit("/api/auth/login", "login")

        mock_counter.labels.assert_called_once_with(
            endpoint="/api/auth/login",
            action="login"
        )
        mock_labels.inc.assert_called_once()


class TestOAuthMetric:
    """Test OAuth flow metric recording."""

    @patch("orizon.metrics._init_metrics", return_value=True)
    @patch("orizon.metrics._oauth_flows")
    def test_records_oauth_started(self, mock_counter, mock_init):
        """Should record OAuth flow start."""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        record_oauth_flow("github", "started")

        mock_counter.labels.assert_called_once_with(
            provider="github",
            status="started"
        )
        mock_labels.inc.assert_called_once()

    @patch("orizon.metrics._init_metrics", return_value=True)
    @patch("orizon.metrics._oauth_flows")
    def test_records_oauth_success(self, mock_counter, mock_init):
        """Should record OAuth success."""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        record_oauth_flow("github", "success")

        mock_counter.labels.assert_called_once_with(
            provider="github",
            status="success"
        )


class TestMagicLinkMetric:
    """Test magic link metric recording."""

    @patch("orizon.metrics._init_metrics", return_value=True)
    @patch("orizon.metrics._magic_link_requests")
    def test_records_magic_link_sent(self, mock_counter, mock_init):
        """Should record magic link sent."""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        record_magic_link("signup", "sent")

        mock_counter.labels.assert_called_once_with(
            type="signup",
            status="sent"
        )

    @patch("orizon.metrics._init_metrics", return_value=True)
    @patch("orizon.metrics._magic_link_requests")
    def test_records_magic_link_verified(self, mock_counter, mock_init):
        """Should record magic link verified."""
        mock_labels = MagicMock()
        mock_counter.labels.return_value = mock_labels

        record_magic_link("login", "verified")

        mock_counter.labels.assert_called_once_with(
            type="login",
            status="verified"
        )
