"""
Tests for authentication services.
"""

from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import AuthAuditLog, PasswordResetToken, Veterinarian
from accounts.services.auth_service import AuthenticationService

User = get_user_model()


class AuthenticationServiceTest(TestCase):
    """Test cases for AuthenticationService."""

    def setUp(self):
        """Set up test data."""
        self.service = AuthenticationService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            license_number="12345",
            email="test@example.com",
        )
        self.request = Mock()
        self.request.META = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "Test Browser",
        }

    def test_get_client_ip_direct(self):
        """Test getting client IP directly."""
        ip = self.service._get_client_ip(self.request)
        self.assertEqual(ip, "127.0.0.1")

    def test_get_client_ip_forwarded(self):
        """Test getting client IP from forwarded header."""
        self.request.META["HTTP_X_FORWARDED_FOR"] = "192.168.1.1, 127.0.0.1"

        ip = self.service._get_client_ip(self.request)
        self.assertEqual(ip, "192.168.1.1")

    def test_get_user_agent(self):
        """Test getting user agent."""
        user_agent = self.service._get_user_agent(self.request)
        self.assertEqual(user_agent, "Test Browser")

    def test_get_user_agent_missing(self):
        """Test getting user agent when missing."""
        self.request.META = {"REMOTE_ADDR": "127.0.0.1"}

        user_agent = self.service._get_user_agent(self.request)
        self.assertEqual(user_agent, "")

    @patch("accounts.services.auth_service.login")
    def test_process_login_success_veterinarian(self, mock_login):
        """Test successful login for veterinarian."""
        form = Mock()
        form.get_user.return_value = self.user

        success, redirect_url, error = self.service.process_login(
            form, self.request
        )

        self.assertTrue(success)
        self.assertEqual(redirect_url, "protocols:protocol_select_type")
        self.assertEqual(error, "")
        mock_login.assert_called_once_with(self.request, self.user)

    @patch("accounts.services.auth_service.login")
    def test_process_login_success_staff(self, mock_login):
        """Test successful login for staff user."""
        staff_user = User.objects.create_user(
            email="staff@example.com",
            password="testpass123",
            role=User.Role.STAFF,
        )

        form = Mock()
        form.get_user.return_value = staff_user

        success, redirect_url, error = self.service.process_login(
            form, self.request
        )

        self.assertTrue(success)
        self.assertEqual(redirect_url, "/")
        self.assertEqual(error, "")

    def test_process_login_account_locked(self):
        """Test login attempt on locked account."""
        self.user.failed_login_attempts = 5
        self.user.last_failed_login = timezone.now()
        self.user.save()

        form = Mock()
        form.get_user.return_value = self.user

        success, redirect_url, error = self.service.process_login(
            form, self.request
        )

        self.assertFalse(success)
        self.assertEqual(redirect_url, "")
        self.assertIn("bloqueada", error)

    def test_process_login_email_not_verified(self):
        """Test login attempt with unverified email."""
        self.user.email_verified = False
        self.user.save()

        form = Mock()
        form.get_user.return_value = self.user

        success, redirect_url, error = self.service.process_login(
            form, self.request
        )

        self.assertFalse(success)
        self.assertEqual(redirect_url, "")
        self.assertIn("verificar su email", error)

    def test_handle_failed_login_existing_user(self):
        """Test handling failed login for existing user."""
        initial_attempts = self.user.failed_login_attempts

        self.service.handle_failed_login("test@example.com", self.request)

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, initial_attempts + 1)

    def test_handle_failed_login_nonexistent_user(self):
        """Test handling failed login for nonexistent user."""
        # Should not raise exception
        self.service.handle_failed_login(
            "nonexistent@example.com", self.request
        )

    @patch("accounts.services.auth_service.send_mail")
    def test_send_verification_email_success(self, mock_send_mail):
        """Test successful verification email sending."""
        self.request.build_absolute_uri.return_value = (
            "http://test.com/verify/token/"
        )

        result = self.service.send_verification_email(self.user, self.request)

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

        # Check audit log was created
        self.assertTrue(
            AuthAuditLog.objects.filter(
                user=self.user,
                action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
            ).exists()
        )

    @patch("accounts.services.auth_service.send_mail")
    def test_send_verification_email_failure(self, mock_send_mail):
        """Test verification email sending failure."""
        mock_send_mail.side_effect = Exception("SMTP Error")

        result = self.service.send_verification_email(self.user, self.request)

        self.assertFalse(result)

    @patch("accounts.services.auth_service.send_mail")
    def test_process_password_reset_request_existing_user(
        self, mock_send_mail
    ):
        """Test password reset request for existing user."""
        self.request.build_absolute_uri.return_value = (
            "http://test.com/reset/token/"
        )

        result = self.service.process_password_reset_request(
            "test@example.com", self.request
        )

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

        # Check token was created
        self.assertTrue(
            PasswordResetToken.objects.filter(user=self.user).exists()
        )

    @patch("accounts.services.auth_service.send_mail")
    def test_process_password_reset_request_nonexistent_user(
        self, mock_send_mail
    ):
        """Test password reset request for nonexistent user."""
        result = self.service.process_password_reset_request(
            "nonexistent@example.com", self.request
        )

        # Should still return True for security (don't reveal if email exists)
        self.assertTrue(result)
        mock_send_mail.assert_not_called()

    def test_process_password_reset_confirm_success(self):
        """Test successful password reset confirmation."""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token="test-token",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        success, error = self.service.process_password_reset_confirm(
            "test-token", "newpassword123"
        )

        self.assertTrue(success)
        self.assertEqual(error, "")

        # Check token was marked as used
        token.refresh_from_db()
        self.assertIsNotNone(token.used_at)

        # Check password was updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_process_password_reset_confirm_invalid_token(self):
        """Test password reset confirmation with invalid token."""
        success, error = self.service.process_password_reset_confirm(
            "invalid-token", "newpassword123"
        )

        self.assertFalse(success)
        self.assertIn("inválido", error)

    def test_process_password_reset_confirm_expired_token(self):
        """Test password reset confirmation with expired token."""
        PasswordResetToken.objects.create(
            user=self.user,
            token="expired-token",
            expires_at=timezone.now() - timedelta(hours=1),
        )

        success, error = self.service.process_password_reset_confirm(
            "expired-token", "newpassword123"
        )

        self.assertFalse(success)
        self.assertIn("inválido", error)

    def test_process_password_reset_confirm_used_token(self):
        """Test password reset confirmation with already used token."""
        PasswordResetToken.objects.create(
            user=self.user,
            token="used-token",
            expires_at=timezone.now() + timedelta(hours=1),
            used_at=timezone.now(),
        )

        success, error = self.service.process_password_reset_confirm(
            "used-token", "newpassword123"
        )

        self.assertFalse(success)
        self.assertIn("inválido", error)

    def test_verify_email_token_success(self):
        """Test successful email verification."""
        self.user.email_verification_token = "test-token"
        self.user.email_verification_token_created = timezone.now()
        self.user.is_active = False
        self.user.save()

        success, redirect_url, error = self.service.verify_email_token(
            "test-token", self.request
        )

        self.assertTrue(success)
        self.assertEqual(redirect_url, "accounts:login")
        self.assertEqual(error, "")

        # Check user was activated and verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.email_verified)

        # Check audit log was created
        self.assertTrue(
            AuthAuditLog.objects.filter(
                user=self.user, action=AuthAuditLog.Action.EMAIL_VERIFIED
            ).exists()
        )

    def test_verify_email_token_expired(self):
        """Test email verification with expired token."""
        self.user.email_verification_token = "expired-token"
        self.user.email_verification_token_created = (
            timezone.now() - timedelta(days=2)
        )
        self.user.save()

        success, redirect_url, error = self.service.verify_email_token(
            "expired-token", self.request
        )

        self.assertFalse(success)
        self.assertEqual(redirect_url, "accounts:resend_verification")
        self.assertIn("expirado", error)

    def test_verify_email_token_invalid(self):
        """Test email verification with invalid token."""
        success, redirect_url, error = self.service.verify_email_token(
            "invalid-token", self.request
        )

        self.assertFalse(success)
        self.assertEqual(redirect_url, "accounts:login")
        self.assertIn("inválido", error)
