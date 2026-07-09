"""Tests for protocol detail action context builder."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import LaboratoryStaff, Veterinarian
from protocols.models import (
    Protocol,
    ProtocolStatusHistory,
    Report,
    ReportImage,
)
from protocols.protocol_detail_context import (
    build_protocol_detail_action_context,
    build_protocol_report_action_context,
    build_staff_status_history,
    build_status_history_for_user,
    build_veterinarian_status_history,
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
        self.laboratory_staff = LaboratoryStaff.objects.create(
            user=self.staff_user,
            first_name="Staff",
            last_name="Test",
            license_number="LAB-CTX-001",
            can_create_reports=True,
            is_active=True,
            signature_image=SimpleUploadedFile(
                "sig.png", b"fake-image", content_type="image/png"
            ),
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

    def test_staff_draft_protocol_can_manage(self):
        """Lab staff see edit/submit actions on draft protocols."""
        self.protocol.status = Protocol.Status.DRAFT
        self.protocol.created_by = self.staff_user
        self.protocol.save(update_fields=["status", "created_by"])

        context = build_protocol_detail_action_context(
            self.staff_user, self.protocol
        )

        self.assertTrue(context["can_lab_manage_draft"])
        self.assertTrue(context["lab_created_protocol"])

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

    def test_protocol_detail_includes_report_images_context(self):
        """Staff with images on draft report can preview and open gallery."""
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image as PILImage

        report = Report.objects.create(
            protocol=self.protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            diagnosis="OK",
            status=Report.Status.DRAFT,
        )
        buffer = BytesIO()
        PILImage.new("RGB", (40, 40), "red").save(buffer, format="JPEG")
        buffer.seek(0)
        image_file = SimpleUploadedFile(
            "micro.jpg", buffer.read(), content_type="image/jpeg"
        )
        ReportImage.objects.create(report=report, image=image_file)

        context = build_protocol_detail_action_context(
            self.staff_user, self.protocol
        )

        self.assertTrue(context["can_view_report_images"])
        self.assertEqual(context["report_image_count"], 1)
        self.assertEqual(len(context["report_images_preview"]), 1)
        self.assertIn(
            "/informe/imagenes/", context["report_images_gallery_url"]
        )

    def test_veterinarian_cannot_preview_draft_report_images(self):
        """Veterinarian does not see draft report images on protocol detail."""
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            diagnosis="OK",
            status=Report.Status.DRAFT,
        )
        from django.core.files.uploadedfile import SimpleUploadedFile

        ReportImage.objects.create(
            report=report,
            image=SimpleUploadedFile(
                "x.jpg", b"fake", content_type="image/jpeg"
            ),
        )

        context = build_protocol_detail_action_context(
            self.vet_user, self.protocol
        )

        self.assertFalse(context["can_view_report_images"])
        self.assertEqual(len(context["report_images_preview"]), 0)


class VeterinarianStatusHistoryTest(TestCase):
    """Tests for veterinarian-facing collapsed status timeline."""

    def setUp(self):
        """Create protocol with full lab status history."""
        self.staff_user = User.objects.create_user(
            email="staff-hist@example.com",
            username="staffhist",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
            is_staff=True,
        )
        self.vet_user = User.objects.create_user(
            email="vet-hist@example.com",
            username="vethist",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="Ana",
            last_name="García",
            license_number="MP-HIST",
            email="vet-hist@example.com",
        )
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Luna",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.READY,
            protocol_number="HP 26/099",
        )
        ProtocolStatusHistory.log_status_change(
            self.protocol,
            Protocol.Status.SUBMITTED,
            changed_by=self.vet_user,
            description="Enviado",
        )
        ProtocolStatusHistory.log_status_change(
            self.protocol,
            Protocol.Status.RECEIVED,
            changed_by=self.staff_user,
            description="Recibido en lab",
        )
        ProtocolStatusHistory.log_status_change(
            self.protocol,
            Protocol.Status.PROCESSING,
            changed_by=self.staff_user,
            description="Inicio procesamiento",
        )
        ProtocolStatusHistory.log_status_change(
            self.protocol,
            Protocol.Status.READY,
            changed_by=self.staff_user,
            description="Muestra lista para diagnóstico",
        )

    def test_veterinarian_history_collapses_lab_milestones(self):
        """Processing and ready become a single En laboratorio row."""
        history = build_veterinarian_status_history(self.protocol)
        labels = [row.label for row in history]

        self.assertEqual(labels.count("En laboratorio"), 1)
        self.assertNotIn("En procesamiento", labels)
        self.assertNotIn("Listo", labels)
        self.assertIn("Enviado", labels)
        self.assertIn("Recibido", labels)

        lab_row = next(row for row in history if row.label == "En laboratorio")
        self.assertEqual(lab_row.description, "")
        self.assertIsNone(lab_row.changed_by)

    def test_staff_history_keeps_internal_milestones(self):
        """Lab staff still see processing and ready separately."""
        history = build_staff_status_history(self.protocol)
        labels = [row.label for row in history]

        self.assertIn("En procesamiento", labels)
        self.assertIn("Listo", labels)
        self.assertGreaterEqual(len(history), 4)

    def test_status_history_for_user_routes_by_role(self):
        """Owner gets collapsed history; staff gets full history."""
        vet_history = build_status_history_for_user(
            self.vet_user, self.protocol
        )
        staff_history = build_status_history_for_user(
            self.staff_user, self.protocol
        )

        self.assertEqual(len(vet_history), 3)
        self.assertEqual(len(staff_history), 4)
