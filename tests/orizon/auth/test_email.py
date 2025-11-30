"""Tests for orizon.auth.email module."""

import pytest
from unittest.mock import patch, MagicMock

from orizon.auth.email import (
    EmailService,
    get_email_service,
    send_magic_link_email,
)


class TestEmailService:
    """Tests for EmailService class."""

    def test_creates_message_with_html(self):
        """Should create a MIME message with HTML content."""
        service = EmailService()

        message = service._create_message(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="<p>Hello</p>",
        )

        assert message["Subject"] == "Test Subject"
        assert message["To"] == "user@example.com"
        assert "Orizon" in message["From"]

    def test_creates_message_with_text_fallback(self):
        """Should include plain text fallback."""
        service = EmailService()

        message = service._create_message(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="<p>Hello</p>",
            text_body="Hello",
        )

        # Should have both parts
        payload = message.get_payload()
        assert len(payload) == 2  # text and html parts

    def test_send_email_success(self):
        """Should send email successfully."""
        service = EmailService(
            host="localhost",
            port=1025,
            use_tls=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            result = service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            assert result is True
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()

    def test_send_email_with_tls(self):
        """Should use STARTTLS when enabled."""
        service = EmailService(
            host="smtp.example.com",
            port=587,
            use_tls=True,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            mock_server.starttls.assert_called_once()

    def test_send_email_with_auth(self):
        """Should authenticate when credentials provided."""
        service = EmailService(
            host="smtp.example.com",
            port=587,
            user="user",
            password="pass",
            use_tls=False,
        )

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            mock_server.login.assert_called_once_with("user", "pass")

    def test_send_email_handles_smtp_error(self):
        """Should handle SMTP errors gracefully."""
        service = EmailService(use_tls=False)

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("Connection refused")

            result = service.send_email(
                to_email="user@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

            assert result is False


class TestGetEmailService:
    """Tests for get_email_service function."""

    def test_returns_singleton(self):
        """Should return the same instance."""
        # Reset singleton
        import orizon.auth.email as email_module
        email_module._email_service = None

        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2


class TestSendMagicLinkEmail:
    """Tests for send_magic_link_email function."""

    @pytest.mark.asyncio
    async def test_sends_signup_email(self):
        """Should send signup magic link email."""
        with patch.object(EmailService, "send_email", return_value=True) as mock_send:
            result = await send_magic_link_email(
                to_email="new@example.com",
                token="test-token-123",
                name="Test User",
                is_signup=True,
            )

            assert result is True
            mock_send.assert_called_once()

            # Check email content (positional args)
            args, kwargs = mock_send.call_args
            to_email, subject, html_body = args[0], args[1], args[2]
            assert to_email == "new@example.com"
            assert "signup" in subject.lower()
            assert "test-token-123" in html_body

    @pytest.mark.asyncio
    async def test_sends_login_email(self):
        """Should send login magic link email."""
        with patch.object(EmailService, "send_email", return_value=True) as mock_send:
            result = await send_magic_link_email(
                to_email="existing@example.com",
                token="login-token-456",
                is_signup=False,
            )

            assert result is True
            mock_send.assert_called_once()

            # Check email content (positional args)
            args, kwargs = mock_send.call_args
            to_email, subject, html_body = args[0], args[1], args[2]
            assert "log in" in subject.lower()
            assert "login-token-456" in html_body

    @pytest.mark.asyncio
    async def test_includes_magic_link_url(self):
        """Should include full magic link URL."""
        with patch.object(EmailService, "send_email", return_value=True) as mock_send:
            with patch("orizon.auth.email.APP_URL", "https://app.orizon.io"):
                await send_magic_link_email(
                    to_email="user@example.com",
                    token="my-token",
                    is_signup=True,
                )

                args, kwargs = mock_send.call_args
                html_body = args[2]

                assert "https://app.orizon.io/api/auth/verify?token=my-token" in html_body

    @pytest.mark.asyncio
    async def test_returns_false_on_failure(self):
        """Should return False when email fails to send."""
        with patch.object(EmailService, "send_email", return_value=False):
            result = await send_magic_link_email(
                to_email="fail@example.com",
                token="token",
                is_signup=True,
            )

            assert result is False
