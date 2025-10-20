"""
Authentication service for handling login, registration, and email verification.
"""

import logging
import secrets
from datetime import timedelta
from typing import Tuple

from django.conf import settings
from django.contrib.auth import login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from accounts.models import AuthAuditLog, PasswordResetToken, User

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service class for handling authentication-related business logic.

    This service encapsulates the complex authentication flows including
    login validation, email verification, and password reset functionality.
    """

    def process_login(self, form, request) -> Tuple[bool, str, str]:
        """
        Process user login with comprehensive validation.

        Args:
            form: Validated login form
            request: HTTP request object

        Returns:
            Tuple[bool, str, str]: (success, redirect_url, error_message)
        """
        user = form.get_user()

        # Check if account is locked out
        if user.is_locked_out():
            self._log_failed_login(user, request, "Account locked")
            return (
                False,
                "",
                _(
                    "Su cuenta está bloqueada debido a múltiples intentos fallidos. Contacte al administrador."
                ),
            )

        # Check if veterinarian is verified
        if user.role == User.Role.VETERINARIO and not user.email_verified:
            self._log_failed_login(user, request, "Email not verified")
            return (
                False,
                "",
                _("Debe verificar su email antes de iniciar sesión."),
            )

        # Process successful login
        login(request, user)
        user.reset_failed_login_attempts()
        self._log_successful_login(user, request)

        # All users redirect to dashboard (which routes to role-specific dashboard)
        redirect_url = "pages:dashboard"

        return True, redirect_url, ""

    def handle_failed_login(self, email: str, request) -> None:
        """
        Handle failed login attempt.

        Args:
            email: Email address used in login attempt
            request: HTTP request object
        """
        # Try to find user and increment failed attempts
        try:
            user = User.objects.get(email=email)
            user.increment_failed_login_attempts()
        except User.DoesNotExist:
            user = None

        # Log failed login attempt
        self._log_failed_login(user, request, f"Email: {email}")

    def send_verification_email(self, user: User, request) -> bool:
        """
        Send email verification to user.

        Args:
            user: User object to send verification to
            request: HTTP request object (for building absolute URI)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            token = user.generate_email_verification_token()
            verification_url = request.build_absolute_uri(
                f"/accounts/verify-email/{token}/"
            )

            html_message = render_to_string(
                "accounts/emails/email_verification.html",
                {"user": user, "verification_url": verification_url},
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject="Verifique su email - AdLab",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            # Log email verification sent
            AuthAuditLog.objects.create(
                user=user,
                email=user.email,
                action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                ip_address=self._get_client_ip(request),
                user_agent=self._get_user_agent(request),
            )

            return True
        except Exception as e:
            logger.error(
                f"Error sending verification email to {user.email}: {e}"
            )
            return False

    def process_password_reset_request(self, email: str, request) -> bool:
        """
        Process password reset request.

        Args:
            email: Email address requesting password reset
            request: HTTP request object

        Returns:
            bool: True if request processed successfully, False otherwise
        """
        try:
            user = User.objects.get(email=email)

            # Create password reset token
            token = PasswordResetToken.objects.create(
                user=user,
                token=secrets.token_urlsafe(32),
                expires_at=timezone.now() + timedelta(hours=24),
            )

            # Send password reset email
            reset_url = request.build_absolute_uri(
                reverse(
                    "accounts:password_reset_confirm",
                    kwargs={"token": token.token},
                )
            )

            html_message = render_to_string(
                "accounts/emails/password_reset.html",
                {"user": user, "reset_url": reset_url},
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject="Restablecer contraseña - AdLab",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            return True

        except User.DoesNotExist:
            # Don't reveal if email exists - still return True for security
            return True
        except Exception as e:
            logger.error(f"Error processing password reset for {email}: {e}")
            return False

    def process_password_reset_confirm(
        self, token: str, new_password: str
    ) -> Tuple[bool, str]:
        """
        Process password reset confirmation.

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            reset_token = PasswordResetToken.objects.get(
                token=token,
                expires_at__gt=timezone.now(),
                used_at__isnull=True,
            )

            # Update password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.used_at = timezone.now()
            reset_token.save()

            return True, ""

        except PasswordResetToken.DoesNotExist:
            return False, _(
                "El enlace de restablecimiento es inválido o ha expirado."
            )
        except Exception as e:
            logger.error(f"Error processing password reset confirmation: {e}")
            return False, str(e)

    def verify_email_token(self, token: str, request) -> Tuple[bool, str, str]:
        """
        Verify email verification token.

        Args:
            token: Email verification token
            request: HTTP request object

        Returns:
            Tuple[bool, str, str]: (success, redirect_url, error_message)
        """
        try:
            user = User.objects.get(email_verification_token=token)

            if user.is_verification_token_expired():
                return (
                    False,
                    "accounts:resend_verification",
                    _("El enlace de verificación ha expirado."),
                )

            user.verify_email()
            user.is_active = True
            user.save()

            # Log successful email verification
            AuthAuditLog.objects.create(
                user=user,
                email=user.email,
                action=AuthAuditLog.Action.EMAIL_VERIFIED,
                ip_address=self._get_client_ip(request),
                user_agent=self._get_user_agent(request),
            )

            return True, "accounts:login", ""

        except User.DoesNotExist:
            return (
                False,
                "accounts:login",
                _("Enlace de verificación inválido."),
            )

    def _log_successful_login(self, user: User, request) -> None:
        """Log successful login attempt."""
        AuthAuditLog.objects.create(
            user=user,
            email=user.email,
            action=AuthAuditLog.Action.LOGIN_SUCCESS,
            ip_address=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
        )

    def _log_failed_login(self, user: User, request, details: str) -> None:
        """Log failed login attempt."""
        AuthAuditLog.objects.create(
            user=user,
            email=user.email if user else "N/A",
            action=AuthAuditLog.Action.LOGIN_FAILED,
            ip_address=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            details=details,
        )

    def _get_client_ip(self, request) -> str:
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _get_user_agent(self, request) -> str:
        """Get the user agent from the request."""
        return request.META.get("HTTP_USER_AGENT", "")
