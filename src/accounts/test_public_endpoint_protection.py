"""
Tests for rate limiting and Turnstile on public authentication endpoints.
"""

from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User

RATELIMIT_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "public-endpoint-protection-tests",
    }
}


def _registration_payload(email="newvet@example.com"):
    """Return valid registration POST data."""
    return {
        "email": email,
        "password1": "complexpassword123",
        "password2": "complexpassword123",
        "first_name": "New",
        "last_name": "Vet",
    }


@override_settings(RATELIMIT_ENABLE=True, CACHES=RATELIMIT_CACHE)
class LoginRateLimitTests(TestCase):
    """Rate limit tests for login POST."""

    def test_login_blocks_after_ten_attempts_per_ip(self):
        """Eleventh login attempt from same IP shows rate limit message."""
        url = reverse("accounts:login")
        payload = {"username": "nobody@example.com", "password": "wrongpass"}

        for _ in range(10):
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 200)

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        messages = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        self.assertTrue(
            any(
                "Demasiados intentos de inicio de sesión" in message
                for message in messages
            )
        )


@override_settings(RATELIMIT_ENABLE=True, CACHES=RATELIMIT_CACHE)
class RegisterRateLimitTests(TestCase):
    """Rate limit tests for registration POST."""

    def test_register_blocks_after_three_attempts_per_ip(self):
        """Fourth registration attempt from same IP is blocked."""
        url = reverse("accounts:register")

        for index in range(3):
            response = self.client.post(
                url,
                _registration_payload(email=f"vet{index}@example.com"),
            )
            self.assertEqual(response.status_code, 302)

        response = self.client.post(
            url,
            _registration_payload(email="vet-blocked@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        messages = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        self.assertTrue(
            any(
                "Demasiados intentos de registro" in message
                for message in messages
            )
        )
        self.assertFalse(
            User.objects.filter(email="vet-blocked@example.com").exists()
        )


@override_settings(RATELIMIT_ENABLE=True, CACHES=RATELIMIT_CACHE)
class PasswordResetRateLimitTests(TestCase):
    """Rate limit tests for password reset POST."""

    def test_password_reset_blocks_after_three_attempts_per_ip(self):
        """Fourth password reset request from same IP is blocked."""
        url = reverse("accounts:password_reset_request")

        for _ in range(3):
            response = self.client.post(url, {"email": "someone@example.com"})
            self.assertEqual(response.status_code, 302)

        response = self.client.post(url, {"email": "someone@example.com"})
        self.assertEqual(response.status_code, 200)
        messages = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        self.assertTrue(
            any(
                "Demasiados intentos de restablecimiento" in message
                for message in messages
            )
        )


@override_settings(RATELIMIT_ENABLE=True, CACHES=RATELIMIT_CACHE)
class ResendVerificationRateLimitTests(TestCase):
    """Rate limit tests for resend verification POST."""

    def setUp(self):
        """Create an unverified veterinarian for resend tests."""
        User.objects.create_user(
            email="unverified@example.com",
            username="unverified",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=False,
        )

    def test_resend_verification_blocks_after_three_attempts_per_email(self):
        """Fourth resend for the same email is blocked."""
        url = reverse("accounts:resend_verification")
        payload = {"email": "unverified@example.com"}

        for _ in range(3):
            with patch(
                "accounts.services.auth_service.AuthenticationService.send_verification_email",
                return_value=True,
            ):
                response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 302)

        with patch(
            "accounts.services.auth_service.AuthenticationService.send_verification_email",
            return_value=True,
        ) as mock_send:
            response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 200)
        mock_send.assert_not_called()
        messages = [
            str(message) for message in get_messages(response.wsgi_request)
        ]
        self.assertTrue(
            any(
                "Demasiados intentos de reenvío de verificación" in message
                for message in messages
            )
        )


@override_settings(
    TURNSTILE_SITE_KEY="test-site-key",
    TURNSTILE_SECRET_KEY="test-secret-key",
)
class TurnstileRegistrationTests(TestCase):
    """Turnstile validation tests for registration."""

    @patch("accounts.forms.verify_turnstile_token", return_value=False)
    def test_register_rejects_invalid_turnstile_token(self, _mock_verify):
        """Registration fails when Turnstile token is invalid."""
        response = self.client.post(
            reverse("accounts:register"),
            _registration_payload(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(email="newvet@example.com").exists()
        )
        self.assertContains(
            response,
            "Verificación de seguridad no completada",
        )

    @patch("accounts.forms.verify_turnstile_token", return_value=True)
    @patch(
        "accounts.services.auth_service.AuthenticationService.send_verification_email",
        return_value=True,
    )
    def test_register_accepts_valid_turnstile_token(
        self, _mock_send, _mock_verify
    ):
        """Registration succeeds when Turnstile token is valid."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                **_registration_payload(),
                "cf-turnstile-response": "valid-test-token",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(email="newvet@example.com").exists()
        )

    def test_register_template_includes_turnstile_when_configured(self):
        """Registration page renders Turnstile widget when keys are set."""
        response = self.client.get(reverse("accounts:register"))
        self.assertContains(response, "cf-turnstile")
        self.assertContains(response, "test-site-key")
        self.assertContains(
            response,
            "challenges.cloudflare.com/turnstile/v0/api.js",
        )


@override_settings(TURNSTILE_SITE_KEY="", TURNSTILE_SECRET_KEY="")
class TurnstileDisabledTests(TestCase):
    """Tests when Turnstile is not configured (local development)."""

    def test_register_works_without_turnstile_keys(self):
        """Registration bypasses Turnstile when keys are empty."""
        with patch(
            "accounts.services.auth_service.AuthenticationService.send_verification_email",
            return_value=True,
        ):
            response = self.client.post(
                reverse("accounts:register"),
                _registration_payload(),
            )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(email="newvet@example.com").exists()
        )

    def test_register_template_hides_turnstile_when_not_configured(self):
        """Registration page omits Turnstile widget without keys."""
        response = self.client.get(reverse("accounts:register"))
        self.assertNotContains(response, "cf-turnstile")
