"""
Tests for veterinarian approval gate, admin panel, and soft delete (roadmap 11).
"""

from datetime import date
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import (
    AuthAuditLog,
    User,
    VeterinarianPendingApprovalSettings,
)
from accounts.services.veterinarian_approval_service import (
    VeterinarianApprovalService,
    can_delete,
)
from accounts.services.veterinarian_pending_settings_service import (
    get_cached_pending_settings,
    warm_pending_settings_cache,
)
from accounts.test_helpers import create_complete_veterinarian_user
from protocols.models import EmailLog, Protocol


class VeterinarianApprovedMixinTest(TestCase):
    """Protocol creation requires admin approval."""

    def setUp(self):
        """Create pending and approved veterinarians."""
        self.pending_user, self.pending_vet = (
            create_complete_veterinarian_user(
                email="pending@example.com",
                username="pending",
                is_verified=False,
                vet_kwargs={"license_number": "MP-PENDING"},
            )
        )
        self.approved_user, self.approved_vet = (
            create_complete_veterinarian_user(
                email="approved@example.com",
                username="approved",
                is_verified=True,
                vet_kwargs={"license_number": "MP-APPROVED"},
            )
        )
        self.client = Client()

    def test_pending_veterinarian_redirected_from_protocol_create(self):
        """Unapproved vet is redirected to pending-approval screen."""
        self.client.login(email="pending@example.com", password="testpass123")
        response = self.client.get(reverse("protocols:protocol_select_type"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("accounts:veterinarian_pending_approval"),
        )

    def test_approved_veterinarian_can_access_protocol_create(self):
        """Approved vet can open protocol type selection."""
        self.client.login(email="approved@example.com", password="testpass123")
        response = self.client.get(reverse("protocols:protocol_select_type"))

        self.assertEqual(response.status_code, 200)


class LabSearchVerifiedFilterTest(TestCase):
    """Lab search only lists admin-approved veterinarians."""

    def setUp(self):
        """Create vets with different approval states."""
        self.lab_user = User.objects.create_user(
            email="lab@example.com",
            username="lab",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
        )
        _, self.approved_vet = create_complete_veterinarian_user(
            email="approved@example.com",
            username="approved",
            is_verified=True,
            vet_kwargs={
                "first_name": "Ana",
                "last_name": "Aprobada",
                "license_number": "MP-APPROVED-LAB",
            },
        )
        _, self.unapproved_vet = create_complete_veterinarian_user(
            email="unapproved@example.com",
            username="unapproved",
            is_verified=False,
            vet_kwargs={
                "first_name": "Bob",
                "last_name": "Pendiente",
                "license_number": "MP-PENDING-LAB",
            },
        )
        self.client = Client()
        self.client.login(email="lab@example.com", password="testpass123")

    def test_lab_search_only_shows_approved_veterinarians(self):
        """Only is_verified=True veterinarians appear in lab search."""
        response = self.client.get(reverse("protocols:lab_protocol_search"))

        self.assertEqual(response.status_code, 200)
        vet_pks = {vet.pk for vet in response.context["veterinarians"]}
        self.assertIn(self.approved_vet.pk, vet_pks)
        self.assertNotIn(self.unapproved_vet.pk, vet_pks)


class VeterinarianApprovalServiceTest(TestCase):
    """Service methods for approve, delete, and reactivate."""

    def setUp(self):
        """Create admin and veterinarian test data."""
        self.admin = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
            email_verified=True,
        )
        self.vet_user, self.veterinarian = create_complete_veterinarian_user(
            email="vet@example.com",
            username="vet",
            is_verified=False,
        )
        self.service = VeterinarianApprovalService()
        self.client = Client()

    def _request(self):
        """Build a minimal request object for service calls."""
        self.client.login(email="admin@example.com", password="testpass123")
        return self.client.get("/").wsgi_request

    @patch("accounts.services.veterinarian_approval_service.send_mail")
    def test_approve_marks_verified_and_logs(self, mock_send_mail):
        """Approve sets is_verified and creates audit log."""
        mock_send_mail.return_value = 1
        result = self.service.approve(
            self.veterinarian,
            self.admin,
            self._request(),
        )

        self.veterinarian.refresh_from_db()
        self.assertTrue(result.success)
        self.assertTrue(result.email_sent)
        self.assertTrue(self.veterinarian.is_verified)
        self.assertTrue(
            AuthAuditLog.objects.filter(
                action=AuthAuditLog.Action.VETERINARIAN_APPROVED,
                email="vet@example.com",
            ).exists()
        )
        self.assertTrue(
            EmailLog.objects.filter(
                email_type=EmailLog.EmailType.VETERINARIAN_APPROVED,
            ).exists()
        )

    @patch("accounts.services.veterinarian_approval_service.send_mail")
    def test_delete_without_protocols_anonymizes_email(self, mock_send_mail):
        """Delete without protocols frees email for re-registration."""
        mock_send_mail.return_value = 1
        original_email = self.veterinarian.email
        result = self.service.delete_account(
            self.veterinarian,
            self.admin,
            self._request(),
        )

        self.veterinarian.refresh_from_db()
        self.vet_user.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(result.mode, "anonymize")
        self.assertFalse(self.vet_user.is_active)
        self.assertNotEqual(self.vet_user.email, original_email)
        self.assertTrue(self.vet_user.email.endswith("@invalid.local"))
        self.assertFalse(User.objects.filter(email=original_email).exists())

    @patch("accounts.services.veterinarian_approval_service.send_mail")
    def test_delete_with_protocols_only_deactivates(self, mock_send_mail):
        """Delete with protocols keeps email but deactivates account."""
        mock_send_mail.return_value = 1
        Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        original_email = self.veterinarian.email
        allowed, mode, _reason = can_delete(self.veterinarian)
        self.assertTrue(allowed)
        self.assertEqual(mode, "deactivate_only")

        result = self.service.delete_account(
            self.veterinarian,
            self.admin,
            self._request(),
        )

        self.vet_user.refresh_from_db()
        self.assertTrue(result.success)
        self.assertEqual(result.mode, "deactivate_only")
        self.assertFalse(self.vet_user.is_active)
        self.assertEqual(self.vet_user.email, original_email)

    def test_reactivate_inactive_account(self):
        """Reactivate restores access for non-anonymized accounts."""
        self.vet_user.is_active = False
        self.vet_user.save(update_fields=["is_active"])

        result = self.service.reactivate(
            self.veterinarian,
            self.admin,
            self._request(),
        )

        self.vet_user.refresh_from_db()
        self.assertTrue(result.success)
        self.assertTrue(self.vet_user.is_active)


class PendingApprovalScreenTest(TestCase):
    """Pending-approval singleton and screen rendering."""

    def setUp(self):
        """Create veterinarian and admin users."""
        self.vet_user, self.veterinarian = create_complete_veterinarian_user(
            email="vet@example.com",
            username="vet",
            is_verified=False,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
            email_verified=True,
        )
        self.client = Client()

    def test_pending_screen_shows_cached_content(self):
        """Screen renders title and message from singleton settings."""
        VeterinarianPendingApprovalSettings.update_settings(
            title="Espere la habilitación",
            message="Envíe su matrícula por email.",
            contact_phone="341-1234567",
            contact_email="lab@example.com",
            is_active=True,
            user=self.admin,
        )
        warm_pending_settings_cache()

        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(
            reverse("accounts:veterinarian_pending_approval")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Espere la habilitación")
        self.assertContains(response, "341-1234567")
        self.assertContains(response, "lab@example.com")

    def test_get_cached_pending_settings_returns_defaults(self):
        """Cache service returns sensible defaults when empty."""
        payload = get_cached_pending_settings()
        self.assertIn("title", payload)
        self.assertIn("message_html", payload)


class AdminVeterinarianManagementViewTest(TestCase):
    """Admin panel permissions and approve action."""

    def setUp(self):
        """Create admin and pending veterinarian."""
        self.admin = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
            email_verified=True,
        )
        self.vet_user, self.veterinarian = create_complete_veterinarian_user(
            email="vet@example.com",
            username="vet",
            is_verified=False,
            vet_kwargs={"first_name": "Carlos", "last_name": "Vet"},
        )
        self.client = Client()

    def test_non_admin_denied(self):
        """Non-admin users cannot access veterinarian management."""
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(
            reverse("pages:admin_veterinarian_management")
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_sees_pending_veterinarian(self):
        """Admin list shows pending veterinarians by default."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            reverse("pages:admin_veterinarian_management")
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context["total_count"], 1)

    @patch("accounts.services.veterinarian_approval_service.send_mail")
    def test_admin_can_approve_veterinarian(self, mock_send_mail):
        """POST approve action enables veterinarian."""
        mock_send_mail.return_value = 1
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.post(
            reverse("pages:admin_veterinarian_management"),
            {
                "veterinarian_id": self.veterinarian.pk,
                "action": "approve",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.veterinarian.refresh_from_db()
        self.assertTrue(self.veterinarian.is_verified)
