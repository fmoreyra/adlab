"""Tests for protocol detail action context builder."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import LaboratoryStaff, Veterinarian
from protocols.models import Protocol, Report
from protocols.protocol_detail_context import (
    build_protocol_detail_action_context,
    build_protocol_report_action_context,
)

User = get_user_model()


class BuildProtocolDetailActionContextTest(TestCase):
    """Unit tests for build_protocol_detail_action_context."""

    def setUp(self):
        """Create users and a sample protocol."""
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
            is_staff=True,
        )
        LaboratoryStaff.objects.create(
            user=self.staff_user,
            first_name="Staff",
            last_name="Test",
            license_number="LAB-CTX-001",
            can_create_reports=True,
            is_active=True,
        )
        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="Ana",
            last_name="García",
            license_number="MP-999",
            cuil_cuit="20-98765432-1",
            phone="+54 341 5551234",
            email="vet@example.com",
        )
        from accounts.models import Address

        Address.objects.create(
            veterinarian=self.veterinarian,
            province="Santa Fe",
            locality="Rosario",
            street="San Martín",
            number="100",
        )
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Luna",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.SUBMITTED,
            temporary_code="TMP-HP-20260101-001",
        )

    def test_staff_submitted_protocol_can_receive(self):
        """Lab staff may receive a submitted protocol."""
        context = build_protocol_detail_action_context(
            self.staff_user, self.protocol
        )

        self.assertTrue(context["can_receive_protocol"])
        self.assertTrue(context["show_lab_actions"])
        self.assertFalse(context["show_vet_actions"])

    def test_veterinarian_owner_hides_vet_card(self):
        """Owning veterinarian hides redundant vet info card."""
        context = build_protocol_detail_action_context(
            self.vet_user, self.protocol
        )

        self.assertTrue(context["hide_veterinarian_card"])
        self.assertTrue(context["show_vet_actions"])

    def test_report_workflow_primary_create_when_ready(self):
        """Ready protocol shows primary action to create report."""
        self.protocol.status = Protocol.Status.READY
        self.protocol.save(update_fields=["status"])

        context = build_protocol_report_action_context(
            self.staff_user, self.protocol
        )

        self.assertTrue(context["show_report_workflow"])
        self.assertTrue(context["can_create_report"])
        self.assertIn("/reports/create/", context["report_primary_url"])

    def test_report_workflow_primary_edit_when_draft(self):
        """Draft report shows continue editing as primary action."""
        self.protocol.status = Protocol.Status.READY
        self.protocol.save(update_fields=["status"])
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            diagnosis="En curso",
            status=Report.Status.DRAFT,
        )

        context = build_protocol_report_action_context(
            self.staff_user, self.protocol
        )

        self.assertTrue(context["can_edit_report"])
        self.assertIn("/reports/", context["report_primary_url"])
        self.assertIn("/edit/", context["report_primary_url"])
        self.assertEqual(context["latest_report"].pk, report.pk)

    def test_veterinarian_can_view_finalized_report_flags(self):
        """Owner sees report actions when a finalized report exists."""
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            diagnosis="OK",
            status=Report.Status.FINALIZED,
            pdf_path="reports/test.pdf",
        )
        self.protocol.status = Protocol.Status.REPORT_SENT
        self.protocol.save(update_fields=["status"])

        context = build_protocol_detail_action_context(
            self.vet_user, self.protocol
        )

        self.assertEqual(context["latest_report"].pk, report.pk)
        self.assertTrue(context["can_view_report_detail"])
        self.assertTrue(context["can_download_report_pdf"])
