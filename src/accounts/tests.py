from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import (
    Address,
    AuthAuditLog,
    PasswordResetToken,
    Veterinarian,
    VeterinarianChangeLog,
)

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role=User.Role.VETERINARIO,
        )

    def test_create_user(self):
        """Test creating a user."""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertEqual(self.user.role, User.Role.VETERINARIO)

    def test_user_role_properties(self):
        """Test user role property methods."""
        self.assertTrue(self.user.is_veterinarian)
        self.assertFalse(self.user.is_lab_staff)
        self.assertFalse(self.user.is_histopathologist)
        self.assertFalse(self.user.is_admin_user)

    def test_failed_login_attempts(self):
        """Test failed login attempt tracking."""
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertFalse(self.user.is_locked_out())

        # Increment attempts
        for i in range(5):
            self.user.increment_failed_login_attempts()

        self.assertEqual(self.user.failed_login_attempts, 5)
        self.assertTrue(self.user.is_locked_out())

        # Reset attempts
        self.user.reset_failed_login_attempts()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertFalse(self.user.is_locked_out())

    def test_get_full_name(self):
        """Test get_full_name method."""
        self.assertEqual(self.user.get_full_name(), "Test User")

        # Test with no name
        user_no_name = User.objects.create_user(
            email="noname@example.com",
            username="noname",
            password="testpass123",
        )
        self.assertEqual(user_no_name.get_full_name(), "noname@example.com")


class LoginViewTest(TestCase):
    """Tests for the login view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        # Veterinarians need email verification to login
        self.user.email_verified = True
        self.user.save()

    def test_login_page_loads(self):
        """Test login page loads correctly."""
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar Sesión")

    def test_login_successful(self):
        """Test successful login."""
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)  # Redirect after login

        # Check audit log
        log = AuthAuditLog.objects.filter(
            action=AuthAuditLog.Action.LOGIN_SUCCESS,
            email="test@example.com",
        ).first()
        self.assertIsNotNone(log)

    def test_login_failed(self):
        """Test failed login with wrong password."""
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrectos")

        # Check audit log
        log = AuthAuditLog.objects.filter(
            action=AuthAuditLog.Action.LOGIN_FAILED,
            email="test@example.com",
        ).first()
        self.assertIsNotNone(log)

        # Check failed attempts incremented
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_account_lockout(self):
        """Test account lockout after 5 failed attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            self.client.post(
                reverse("accounts:login"),
                {"username": "test@example.com", "password": "wrongpass"},
            )

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked_out())

        # Try to login with correct password
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bloqueada")

        # Check lockout logged
        log = AuthAuditLog.objects.filter(
            action=AuthAuditLog.Action.ACCOUNT_LOCKED,
            email="test@example.com",
        ).first()
        self.assertIsNotNone(log)

    def test_inactive_user_cannot_login(self):
        """Test inactive user cannot login."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "desactivada")


class RegistrationViewTest(TestCase):
    """Tests for the registration view."""

    def setUp(self):
        self.client = Client()

    def test_register_page_loads(self):
        """Test registration page loads correctly."""
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registro")

    def test_register_successful(self):
        """Test successful registration."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "newvet@example.com",
                "first_name": "New",
                "last_name": "Vet",
                "password1": "secure123pass",
                "password2": "secure123pass",
            },
        )
        self.assertEqual(
            response.status_code, 302
        )  # Redirect after registration

        # Check user was created
        user = User.objects.filter(email="newvet@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, User.Role.VETERINARIO)
        self.assertTrue(user.check_password("secure123pass"))

    def test_register_duplicate_email(self):
        """Test registration with duplicate email fails."""
        User.objects.create_user(
            email="existing@example.com",
            username="existing@example.com",
            password="testpass123",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "existing@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "secure123pass",
                "password2": "secure123pass",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya está registrado")

    def test_register_password_mismatch(self):
        """Test registration with password mismatch fails."""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "secure123pass",
                "password2": "different123pass",
            },
        )
        self.assertEqual(response.status_code, 200)
        # Django's built-in password mismatch error
        self.assertContains(response, "password")


class PasswordResetTest(TestCase):
    """Tests for password reset functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="test@example.com",
            password="testpass123",
        )

    def test_password_reset_request_page(self):
        """Test password reset request page loads."""
        response = self.client.get(reverse("accounts:password_reset_request"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Restablecer")

    def test_password_reset_token_creation(self):
        """Test password reset token is created."""
        expires_at = timezone.now() + timedelta(hours=1)
        token = PasswordResetToken.objects.create(
            user=self.user,
            token="test-token-123",
            expires_at=expires_at,
        )

        self.assertTrue(token.is_valid())
        self.assertIsNone(token.used_at)

    def test_password_reset_token_expiry(self):
        """Test expired tokens are invalid."""
        expires_at = timezone.now() - timedelta(hours=1)  # Expired
        token = PasswordResetToken.objects.create(
            user=self.user,
            token="test-token-123",
            expires_at=expires_at,
        )

        self.assertFalse(token.is_valid())

    def test_password_reset_token_used(self):
        """Test used tokens are invalid."""
        expires_at = timezone.now() + timedelta(hours=1)
        token = PasswordResetToken.objects.create(
            user=self.user,
            token="test-token-123",
            expires_at=expires_at,
        )

        token.mark_as_used()
        self.assertFalse(token.is_valid())
        self.assertIsNotNone(token.used_at)


class AuditLogTest(TestCase):
    """Tests for authentication audit logging."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="test@example.com",
            password="testpass123",
        )

    def test_audit_log_creation(self):
        """Test creating audit log entries."""
        log = AuthAuditLog.log(
            action=AuthAuditLog.Action.LOGIN_SUCCESS,
            email="test@example.com",
            user=self.user,
            ip_address="127.0.0.1",
            user_agent="Test Browser",
        )

        self.assertEqual(log.email, "test@example.com")
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, AuthAuditLog.Action.LOGIN_SUCCESS)
        self.assertEqual(log.ip_address, "127.0.0.1")

    def test_audit_log_without_user(self):
        """Test audit log can be created without user object."""
        log = AuthAuditLog.log(
            action=AuthAuditLog.Action.LOGIN_FAILED,
            email="nonexistent@example.com",
            ip_address="127.0.0.1",
        )

        self.assertEqual(log.email, "nonexistent@example.com")
        self.assertIsNone(log.user)
        self.assertEqual(log.action, AuthAuditLog.Action.LOGIN_FAILED)


class LogoutViewTest(TestCase):
    """Tests for the logout view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="test@example.com",
            password="testpass123",
        )

    def test_logout(self):
        """Test user can logout."""
        # Login first
        self.client.login(username="test@example.com", password="testpass123")

        # Logout
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)  # Redirect after logout

        # Check audit log
        log = AuthAuditLog.objects.filter(
            action=AuthAuditLog.Action.LOGOUT,
            email="test@example.com",
        ).first()
        self.assertIsNotNone(log)


class EmailVerificationTest(TestCase):
    """Tests for email verification functionality."""

    def setUp(self):
        self.client = Client()
        # Create unverified veterinarian
        self.vet = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="password123",
            first_name="Test",
            last_name="Vet",
            role=User.Role.VETERINARIO,
        )
        # Veterinarians start unverified
        self.vet.email_verified = False
        self.vet.save()

        # Create verified lab staff (internal user)
        self.lab_staff = User.objects.create_user(
            email="lab@example.com",
            username="lab",
            password="password123",
            role=User.Role.PERSONAL_LAB,
        )

    def test_new_user_starts_unverified(self):
        """Test that new veterinarians start with email_verified=False."""
        self.assertFalse(self.vet.email_verified)
        self.assertIsNone(self.vet.email_verification_token)
        self.assertIsNone(self.vet.email_verification_sent_at)

    def test_can_login_veterinarian_unverified(self):
        """Test that unverified veterinarians cannot login."""
        self.assertFalse(self.vet.can_login())

        # Verify email
        self.vet.email_verified = True
        self.vet.save()
        self.assertTrue(self.vet.can_login())

    def test_can_login_internal_user_no_verification(self):
        """Test that internal users don't need email verification."""
        # Lab staff don't need verification
        self.assertTrue(self.lab_staff.can_login())
        self.assertFalse(self.lab_staff.email_verified)  # Not even set

    def test_generate_verification_token(self):
        """Test generating verification token."""
        token = self.vet.generate_email_verification_token()

        self.assertIsNotNone(token)
        self.assertEqual(len(token), 43)  # urlsafe_b64 of 32 bytes
        self.assertEqual(self.vet.email_verification_token, token)
        self.assertIsNotNone(self.vet.email_verification_sent_at)

    def test_verify_email_method(self):
        """Test verify_email method."""
        self.vet.generate_email_verification_token()
        self.assertFalse(self.vet.email_verified)
        self.assertIsNotNone(self.vet.email_verification_token)

        # Verify
        self.vet.verify_email()

        self.assertTrue(self.vet.email_verified)
        self.assertIsNone(self.vet.email_verification_token)

    def test_token_expiration(self):
        """Test that tokens expire after 24 hours."""
        self.vet.generate_email_verification_token()

        # Token is fresh
        self.assertFalse(self.vet.is_verification_token_expired())

        # Set sent_at to 25 hours ago
        self.vet.email_verification_sent_at = timezone.now() - timedelta(
            hours=25
        )
        self.vet.save()

        # Token is expired
        self.assertTrue(self.vet.is_verification_token_expired())

    def test_registration_sends_verification_email(self):
        """Test that registration sends verification email."""
        from unittest.mock import patch

        with patch(
            "accounts.services.auth_service.send_mail"
        ) as mock_send_mail:
            self.client.post(
                reverse("accounts:register"),
                {
                    "first_name": "New",
                    "last_name": "Vet",
                    "email": "newvet@example.com",
                    "username": "newvet",
                    "password1": "SecurePass123!",
                    "password2": "SecurePass123!",
                },
            )

            # Check email was sent
            mock_send_mail.assert_called_once()

            # Check user was created
            user = User.objects.get(email="newvet@example.com")
            self.assertFalse(user.email_verified)
            self.assertIsNotNone(user.email_verification_token)

            # Check audit log
            log = AuthAuditLog.objects.filter(
                action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                email="newvet@example.com",
            ).first()
            self.assertIsNotNone(log)

    def test_login_blocked_for_unverified_vet(self):
        """Test that unverified veterinarians cannot login."""
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "vet@example.com",
                "password": "password123",
            },
        )

        # Should not be logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "verificar su email")

        # Check audit log
        log = AuthAuditLog.objects.filter(
            action=AuthAuditLog.Action.LOGIN_FAILED,
            email="vet@example.com",
            details="Email not verified",
        ).first()
        self.assertIsNotNone(log)

    def test_login_success_for_verified_vet(self):
        """Test that verified veterinarians can login."""
        self.vet.email_verified = True
        self.vet.save()

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "vet@example.com",
                "password": "password123",
            },
            follow=True,
        )

        # Should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_verify_email_view_success(self):
        """Test successful email verification via URL."""
        token = self.vet.generate_email_verification_token()

        response = self.client.get(
            reverse("accounts:verify_email", args=[token]), follow=True
        )

        # Check success message
        self.assertContains(response, "Email verificado exitosamente")

        # Check user is verified
        self.vet.refresh_from_db()
        self.assertTrue(self.vet.email_verified)
        self.assertIsNone(self.vet.email_verification_token)

        # Check audit log
        log = AuthAuditLog.objects.filter(
            action=AuthAuditLog.Action.EMAIL_VERIFIED,
            email="vet@example.com",
        ).first()
        self.assertIsNotNone(log)

    def test_verify_email_view_invalid_token(self):
        """Test verification with invalid token."""
        response = self.client.get(
            reverse("accounts:verify_email", args=["invalid-token"]),
            follow=True,
        )

        # Should show error
        self.assertContains(response, "Enlace de verificación inválido")

        # User should still be unverified
        self.vet.refresh_from_db()
        self.assertFalse(self.vet.email_verified)

    def test_verify_email_view_expired_token(self):
        """Test verification with expired token."""
        token = self.vet.generate_email_verification_token()

        # Set sent_at to 25 hours ago
        self.vet.email_verification_sent_at = timezone.now() - timedelta(
            hours=25
        )
        self.vet.save()

        response = self.client.get(
            reverse("accounts:verify_email", args=[token]), follow=True
        )

        # Should show expiration error
        self.assertContains(response, "expirado")

        # User should still be unverified
        self.vet.refresh_from_db()
        self.assertFalse(self.vet.email_verified)

    def test_resend_verification_email(self):
        """Test resending verification email."""
        from unittest.mock import patch

        # Generate initial token
        old_token = self.vet.generate_email_verification_token()

        with patch(
            "accounts.services.auth_service.send_mail"
        ) as mock_send_mail:
            response = self.client.post(
                reverse("accounts:resend_verification"),
                {"email": "vet@example.com"},
                follow=True,
            )

            # Check email was sent
            mock_send_mail.assert_called_once()

            # Check success message
            self.assertContains(response, "reenviado")

            # Check new token was generated
            self.vet.refresh_from_db()
            self.assertIsNotNone(self.vet.email_verification_token)
            self.assertNotEqual(self.vet.email_verification_token, old_token)

            # Check audit log
            log = AuthAuditLog.objects.filter(
                action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                email="vet@example.com",
                details="Verification email resent",
            ).first()
            self.assertIsNotNone(log)

    def test_resend_verification_nonexistent_email(self):
        """Test resending verification for nonexistent email."""
        from unittest.mock import patch

        with patch("accounts.views.send_mail") as mock_send_mail:
            response = self.client.post(
                reverse("accounts:resend_verification"),
                {"email": "nonexistent@example.com"},
                follow=True,
            )

            # Should not send email
            mock_send_mail.assert_not_called()

            # Should show generic success message (don't reveal if email exists)
            self.assertContains(response, "Si el email existe")

    def test_resend_verification_already_verified(self):
        """Test resending verification for already verified email."""
        from unittest.mock import patch

        self.vet.email_verified = True
        self.vet.save()

        with patch("accounts.views.send_mail") as mock_send_mail:
            response = self.client.post(
                reverse("accounts:resend_verification"),
                {"email": "vet@example.com"},
                follow=True,
            )

            # Should not send email (user is already verified)
            mock_send_mail.assert_not_called()

            # Should show generic success message
            self.assertContains(response, "Si el email existe")

    def test_admin_mark_verified_action(self):
        """Test admin action to mark users as verified."""
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        from accounts.admin import UserAdmin

        # Create admin user
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin123",
        )

        # Create mock request with messages support
        factory = RequestFactory()
        request = factory.get("/")
        request.user = admin_user
        # Add message storage
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Create UserAdmin instance
        user_admin = UserAdmin(User, AdminSite())

        # Execute action
        queryset = User.objects.filter(email="vet@example.com")
        user_admin.mark_email_verified(request, queryset)

        # Check user is verified
        self.vet.refresh_from_db()
        self.assertTrue(self.vet.email_verified)
        self.assertIsNone(self.vet.email_verification_token)

    def test_admin_resend_verification_action(self):
        """Test admin action to resend verification email."""
        from unittest.mock import patch

        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        from accounts.admin import UserAdmin

        # Create admin user
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="admin123",
        )

        # Create mock request with messages support
        factory = RequestFactory()
        request = factory.get("/")
        request.user = admin_user
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        # Add build_absolute_uri method
        def build_absolute_uri(path):
            return f"http://localhost:8000{path}"

        request.build_absolute_uri = build_absolute_uri

        # Create UserAdmin instance
        user_admin = UserAdmin(User, AdminSite())

        # Execute action
        queryset = User.objects.filter(email="vet@example.com")

        # Patch send_mail where admin.py imports it (module level)
        with patch("accounts.admin.send_mail") as mock_send_mail:
            user_admin.resend_verification_email(request, queryset)

            # Check email was sent
            mock_send_mail.assert_called_once()

            # Check new token was generated
            self.vet.refresh_from_db()
            self.assertIsNotNone(self.vet.email_verification_token)


# ============================================================================
# VETERINARIAN PROFILE TESTS (STEP 02)
# ============================================================================


class VeterinarianModelTest(TestCase):
    """Tests for the Veterinarian model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.user.email_verified = True
        self.user.save()

        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        self.address = Address.objects.create(
            veterinarian=self.veterinarian,
            province="Santa Fe",
            locality="Esperanza",
            street="San Martín",
            number="1234",
            postal_code="3080",
        )

    def test_create_veterinarian(self):
        """Test creating a veterinarian."""
        self.assertEqual(self.veterinarian.first_name, "Juan")
        self.assertEqual(self.veterinarian.last_name, "Pérez")
        self.assertEqual(
            self.veterinarian.license_number, "MP-12345-ACCOUNTS-TESTS"
        )
        self.assertFalse(self.veterinarian.is_verified)

    def test_veterinarian_str(self):
        """Test veterinarian string representation."""
        expected = "Pérez, Juan (MP: MP-12345-ACCOUNTS-TESTS)"
        self.assertEqual(str(self.veterinarian), expected)

    def test_get_full_name(self):
        """Test get_full_name method."""
        self.assertEqual(self.veterinarian.get_full_name(), "Juan Pérez")

    def test_verify_method(self):
        """Test verify method."""
        admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="admin123",
            role=User.Role.ADMIN,
        )

        self.veterinarian.verify(verified_by_user=admin_user, notes="Verified")

        self.assertTrue(self.veterinarian.is_verified)
        self.assertEqual(self.veterinarian.verified_by, admin_user)
        self.assertIsNotNone(self.veterinarian.verified_at)
        self.assertEqual(self.veterinarian.verification_notes, "Verified")

    def test_profile_completeness_full(self):
        """Test profile completeness with all fields."""
        self.assertEqual(self.veterinarian.profile_completeness, 100)

    def test_profile_completeness_no_address(self):
        """Test profile completeness without address."""
        self.address.delete()
        # Refresh the veterinarian to clear cached relations
        self.veterinarian.refresh_from_db()
        # 5 veterinarian fields filled, 4 address fields missing
        # 5/9 = 55%
        self.assertEqual(self.veterinarian.profile_completeness, 55)

    def test_license_number_unique(self):
        """Test license number uniqueness constraint."""
        from django.db import IntegrityError

        user2 = User.objects.create_user(
            email="vet2@example.com",
            username="vetuser2",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        with self.assertRaises(IntegrityError):
            Veterinarian.objects.create(
                user=user2,
                first_name="María",
                last_name="González",
                license_number="MP-12345-ACCOUNTS-TESTS",  # Duplicate
                phone="+54 342 9999999",
                email="vet2@example.com",
            )


class AddressModelTest(TestCase):
    """Tests for the Address model."""

    def setUp(self):
        """Set up test data."""
        user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.veterinarian = Veterinarian.objects.create(
            user=user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        self.address = Address.objects.create(
            veterinarian=self.veterinarian,
            province="Santa Fe",
            locality="Esperanza",
            street="San Martín",
            number="1234",
            floor="2",
            apartment="A",
            postal_code="3080",
        )

    def test_create_address(self):
        """Test creating an address."""
        self.assertEqual(self.address.province, "Santa Fe")
        self.assertEqual(self.address.street, "San Martín")

    def test_address_str(self):
        """Test address string representation."""
        expected = (
            "San Martín 1234, Floor 2, Apt A, Esperanza, Santa Fe (3080)"
        )
        self.assertEqual(str(self.address), expected)

    def test_get_full_address(self):
        """Test get_full_address method."""
        full_address = self.address.get_full_address()
        self.assertIn("San Martín", full_address)
        self.assertIn("Esperanza", full_address)
        self.assertIn("Santa Fe", full_address)


class VeterinarianChangeLogTest(TestCase):
    """Tests for the VeterinarianChangeLog model."""

    def setUp(self):
        """Set up test data."""
        user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.veterinarian = Veterinarian.objects.create(
            user=user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

    def test_log_change(self):
        """Test logging a change."""
        log = VeterinarianChangeLog.log_change(
            veterinarian=self.veterinarian,
            changed_by=self.veterinarian.user,
            field_name="phone",
            old_value="+54 342 1234567",
            new_value="+54 342 9999999",
            ip_address="127.0.0.1",
        )

        self.assertEqual(log.veterinarian, self.veterinarian)
        self.assertEqual(log.changed_by, self.veterinarian.user)
        self.assertEqual(log.field_name, "phone")
        self.assertEqual(log.old_value, "+54 342 1234567")
        self.assertEqual(log.new_value, "+54 342 9999999")
        self.assertEqual(log.ip_address, "127.0.0.1")


class VeterinarianFormTest(TestCase):
    """Tests for veterinarian profile forms."""

    def test_valid_license_number(self):
        """Test valid license number format."""
        from accounts.forms import VeterinarianProfileForm

        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "license_number": "MP-99999",
            "phone": "+54 342 1234567",
            "email": "vet@example.com",
        }
        form = VeterinarianProfileForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_license_number_format(self):
        """Test invalid license number format."""
        from accounts.forms import VeterinarianProfileForm

        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "license_number": "12345",  # Invalid format
            "phone": "+54 342 1234567",
            "email": "vet@example.com",
        }
        form = VeterinarianProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("license_number", form.errors)

    def test_invalid_phone_format(self):
        """Test invalid phone number format."""
        from accounts.forms import VeterinarianProfileForm

        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "license_number": "MP-99998",
            "phone": "123456",  # Invalid format
            "email": "vet@example.com",
        }
        form = VeterinarianProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_duplicate_license_number(self):
        """Test duplicate license number validation."""
        from accounts.forms import VeterinarianProfileForm

        # Create existing veterinarian
        user = User.objects.create_user(
            email="existing@example.com",
            username="existing",
            password="pass123",
            role=User.Role.VETERINARIO,
        )
        Veterinarian.objects.create(
            user=user,
            first_name="Existing",
            last_name="User",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1111111",
            email="existing@example.com",
        )

        # Try to create with same license number
        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "license_number": "MP-12345-ACCOUNTS-TESTS-2",  # Duplicate
            "phone": "+54 342 1234567",
            "email": "vet@example.com",
        }
        form = VeterinarianProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("license_number", form.errors)


class CompleteProfileViewTest(TestCase):
    """Tests for complete_profile_view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.user.email_verified = True
        self.user.save()

        self.url = reverse("accounts:complete_profile")

    def test_complete_profile_get(self):
        """Test GET request to complete profile."""
        self.client.login(username="vet@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Complete su Perfil")

    def test_complete_profile_post_valid(self):
        """Test POST request with valid data."""
        self.client.login(username="vet@example.com", password="testpass123")

        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "license_number": "MP-88888",
            "phone": "+54 342 1234567",
            "province": "Santa Fe",
            "locality": "Esperanza",
            "street": "San Martín",
            "number": "1234",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Check veterinarian was created
        self.assertTrue(hasattr(self.user, "veterinarian_profile"))
        self.assertEqual(
            self.user.veterinarian_profile.license_number,
            "MP-88888",
        )

        # Check address was created
        self.assertTrue(hasattr(self.user.veterinarian_profile, "address"))

    def test_complete_profile_non_veterinarian(self):
        """Test that non-veterinarians cannot access."""
        User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="admin123",
            role=User.Role.ADMIN,
        )
        self.client.login(username="admin@example.com", password="admin123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_complete_profile_already_complete(self):
        """Test redirect if profile already complete."""
        Veterinarian.objects.create(
            user=self.user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        self.client.login(username="vet@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect


class VeterinarianProfileDetailViewTest(TestCase):
    """Tests for veterinarian_profile_detail_view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.user.email_verified = True
        self.user.save()

        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        self.address = Address.objects.create(
            veterinarian=self.veterinarian,
            province="Santa Fe",
            locality="Esperanza",
            street="San Martín",
            number="1234",
        )

        self.url = reverse("accounts:veterinarian_profile_detail")

    def test_profile_detail_get(self):
        """Test GET request to profile detail."""
        self.client.login(username="vet@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MP-12345-ACCOUNTS-TESTS")
        self.assertContains(response, "Juan")

    def test_profile_detail_without_profile(self):
        """Test redirect if profile doesn't exist."""
        user2 = User.objects.create_user(
            email="vet2@example.com",
            username="vetuser2",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        user2.email_verified = True
        user2.save()

        self.client.login(username="vet2@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code, 302
        )  # Redirect to complete_profile


class VeterinarianProfileEditViewTest(TestCase):
    """Tests for veterinarian_profile_edit_view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.user.email_verified = True
        self.user.save()

        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-77777",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        self.address = Address.objects.create(
            veterinarian=self.veterinarian,
            province="Santa Fe",
            locality="Esperanza",
            street="San Martín",
            number="1234",
        )

        self.url = reverse("accounts:veterinarian_profile_edit")

    def test_profile_edit_get(self):
        """Test GET request to edit profile."""
        self.client.login(username="vet@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar Perfil")

    def test_profile_edit_post_valid(self):
        """Test POST request with valid data."""
        self.client.login(username="vet@example.com", password="testpass123")

        data = {
            "first_name": "Juan Carlos",  # Changed
            "last_name": "Pérez",
            "license_number": "MP-77777",  # Keep same license number (editing)
            "phone": "+54 342 9999999",  # Changed
            "email": "vet@example.com",
            "province": "Santa Fe",
            "locality": "Esperanza",
            "street": "San Martín",
            "number": "1234",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Check changes were saved
        self.veterinarian.refresh_from_db()
        self.assertEqual(self.veterinarian.first_name, "Juan Carlos")
        self.assertEqual(self.veterinarian.phone, "+54 342 9999999")

        # Check change log was created
        logs = VeterinarianChangeLog.objects.filter(
            veterinarian=self.veterinarian
        )
        self.assertTrue(logs.exists())

    def test_profile_edit_invalid_data(self):
        """Test POST request with invalid data."""
        self.client.login(username="vet@example.com", password="testpass123")

        data = {
            "first_name": "Juan",
            "last_name": "Pérez",
            "license_number": "INVALID",  # Invalid format
            "phone": "+54 342 1234567",
            "email": "vet@example.com",
            "province": "Santa Fe",
            "locality": "Esperanza",
            "street": "San Martín",
            "number": "1234",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)  # Form redisplay
        self.assertContains(response, "Invalid license number")


class VeterinarianProfileHistoryViewTest(TestCase):
    """Tests for veterinarian_profile_history_view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.user.email_verified = True
        self.user.save()

        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="Juan",
            last_name="Pérez",
            license_number="MP-12345-ACCOUNTS-TESTS",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        # Create some change logs
        VeterinarianChangeLog.objects.create(
            veterinarian=self.veterinarian,
            changed_by=self.user,
            field_name="phone",
            old_value="+54 342 1111111",
            new_value="+54 342 1234567",
        )

        self.url = reverse("accounts:veterinarian_profile_history")

    def test_profile_history_get(self):
        """Test GET request to profile history."""
        self.client.login(username="vet@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historial de Cambios")
        self.assertContains(response, "Phone")  # Capitalized by title filter
