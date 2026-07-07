"""
Tests for laboratory staff onboarding middleware and signature enforcement.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Histopathologist, LaboratoryStaff
from accounts.report_access import user_requires_lab_staff_signature
from accounts.test_helpers import create_test_signature_file

User = get_user_model()

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class LabStaffOnboardingMiddlewareTest(TestCase):
    """Test signature middleware for all laboratory staff."""

    def setUp(self):
        self.lab_user = User.objects.create_user(
            email="lab@example.com",
            username="lab@example.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
        )
        self.lab_staff = LaboratoryStaff.objects.create(
            user=self.lab_user,
            first_name="Laura",
            last_name="Lab",
            license_number="LAB-ONB-001",
            can_create_reports=False,
            is_active=True,
        )

    def test_user_requires_lab_staff_signature_without_image(self):
        """All active lab staff without signature must complete onboarding."""
        self.assertTrue(user_requires_lab_staff_signature(self.lab_user))

    def test_user_requires_lab_staff_signature_with_image(self):
        """Lab staff with signature are not forced to upload again."""
        self.lab_staff.signature_image = create_test_signature_file()
        self.lab_staff.save()
        self.assertFalse(user_requires_lab_staff_signature(self.lab_user))

    def test_middleware_redirects_without_signature(self):
        """Dashboard access redirects to signature upload when missing."""
        self.client.login(email="lab@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard"))
        self.assertRedirects(response, reverse("accounts:lab_staff_signature"))

    def test_middleware_allows_signature_page(self):
        """Signature upload page remains accessible during onboarding."""
        self.client.login(email="lab@example.com", password="testpass123")
        response = self.client.get(reverse("accounts:lab_staff_signature"))
        self.assertEqual(response.status_code, 200)

    def test_middleware_allows_dashboard_with_signature(self):
        """Lab staff with signature can access the dashboard."""
        self.lab_staff.signature_image = create_test_signature_file()
        self.lab_staff.save()
        self.client.login(email="lab@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_legacy_histopathologist_redirected_without_signature(self):
        """Legacy histopathologist accounts are also required to upload a signature."""
        legacy_user = User.objects.create_user(
            email="legacy@example.com",
            username="legacy@example.com",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
            email_verified=True,
        )
        Histopathologist.objects.create(
            user=legacy_user,
            first_name="Legacy",
            last_name="Histo",
            license_number="HP-LEG-001",
            is_active=True,
        )

        self.assertTrue(user_requires_lab_staff_signature(legacy_user))

        self.client.login(email="legacy@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard"))
        self.assertRedirects(response, reverse("accounts:lab_staff_signature"))

    def test_legacy_histopathologist_signature_creates_unified_profile(self):
        """Uploading a signature for legacy users creates LaboratoryStaff."""
        legacy_user = User.objects.create_user(
            email="legacy2@example.com",
            username="legacy2@example.com",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
            email_verified=True,
        )
        Histopathologist.objects.create(
            user=legacy_user,
            first_name="Legacy",
            last_name="Two",
            license_number="HP-LEG-002",
            is_active=True,
        )

        image = SimpleUploadedFile(
            "sig.png", MINIMAL_PNG, content_type="image/png"
        )
        self.client.login(email="legacy2@example.com", password="testpass123")
        response = self.client.post(
            reverse("accounts:lab_staff_signature"),
            {"signature_image": image},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            LaboratoryStaff.objects.filter(user=legacy_user).exists()
        )
