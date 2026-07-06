"""Tests for reset_business_data management command and service."""

from datetime import date, timedelta
from io import StringIO

from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, Veterinarian
from accounts.test_helpers import create_complete_veterinarian_user
from protocols.models import (
    NotificationPreference,
    Protocol,
    ProtocolCounter,
    TemporaryCodeCounter,
)
from protocols.services.reset_business_data_service import (
    count_business_rows,
    reset_business_data,
)


class ResetBusinessDataServiceTest(TestCase):
    """Service-layer reset preserves users and removes protocol data."""

    def setUp(self):
        self.user, self.veterinarian = create_complete_veterinarian_user(
            email="reset-vet@example.com",
            username="resetvet",
        )
        NotificationPreference.objects.get_or_create(
            veterinarian=self.veterinarian,
        )
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            species="Canino",
            animal_identification="Firulais",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            temporary_code="TMP-HP-TEST-001",
        )
        ProtocolCounter.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            year=date.today().year,
            last_number=3,
        )
        TemporaryCodeCounter.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            date=date.today(),
            last_number=5,
        )

    def test_count_business_rows_includes_protocol(self):
        counts = count_business_rows(include_pricing=True)
        self.assertGreaterEqual(counts["protocols"], 1)

    def test_reset_removes_protocols_keeps_users(self):
        deleted = reset_business_data(keep_pricing=True, clear_media=False)

        self.assertGreaterEqual(deleted["protocols"], 1)
        self.assertEqual(Protocol.objects.count(), 0)
        self.assertEqual(ProtocolCounter.objects.count(), 0)
        self.assertEqual(TemporaryCodeCounter.objects.count(), 0)
        self.assertEqual(
            User.objects.filter(email="reset-vet@example.com").count(),
            1,
        )
        self.assertEqual(
            Veterinarian.objects.filter(pk=self.veterinarian.pk).count(),
            1,
        )
        self.assertTrue(
            NotificationPreference.objects.filter(
                veterinarian=self.veterinarian
            ).exists()
        )

    def test_reset_dry_run_command_does_not_delete(self):
        out = StringIO()
        call_command("reset_business_data", "--dry-run", stdout=out)

        self.assertEqual(Protocol.objects.count(), 1)
        self.assertIn("Dry-run", out.getvalue())

    def test_reset_command_with_no_input(self):
        out = StringIO()
        call_command("reset_business_data", "--no-input", stdout=out)

        self.assertEqual(Protocol.objects.count(), 0)
        self.assertIn("Reset completado", out.getvalue())

    def test_reset_clears_sessions(self):
        Session.objects.create(
            session_key="testsession1234567890123456789012",
            session_data="e30=",
            expire_date=timezone.now() + timedelta(days=1),
        )
        reset_business_data(keep_pricing=True, clear_media=False)
        self.assertEqual(Session.objects.count(), 0)
