"""
Tests for roadmap items 8, 9 and 10.
"""

from datetime import date
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image as PILImage

from accounts.models import LaboratoryStaff, User, Veterinarian
from protocols.forms import HistopathologyProtocolForm
from protocols.models import (
    Cassette,
    HistopathologySample,
    ProcessingLog,
    Protocol,
    Report,
    ReportImage,
    Slide,
)
from protocols.services.pdf_service import PDFGenerationService
from protocols.services.report_pdf_builder import _build_animal_line


def _make_test_image(name="test.jpg"):
    """Create a small in-memory JPEG for upload tests."""
    buffer = BytesIO()
    PILImage.new("RGB", (100, 100), "red").save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name,
        buffer.read(),
        content_type="image/jpeg",
    )


class AnimalCategoryTests(TestCase):
    """Tests for Protocol.animal_category (item 8)."""

    def setUp(self):
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            last_name="García",
            first_name="Carlos",
            license_number="VET-001",
            email="vet@example.com",
        )

    def test_animal_category_saved_via_histopathology_form(self):
        """Histopathology form persists animal_category on the protocol."""
        form = HistopathologyProtocolForm(
            data={
                "species": "Canino",
                "breed": "Labrador Retriever",
                "animal_category": "Mascota",
                "animal_identification": "Rex",
                "presumptive_diagnosis": "Masa cutánea",
                "submission_date": date.today(),
                "material_submitted": "Biopsia cutánea",
                "number_of_containers": 1,
                "preservation": "Formol 10%",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

        protocol = form.save(veterinarian=self.veterinarian)

        self.assertEqual(protocol.animal_category, "Mascota")

    def test_animal_category_included_in_pdf_line(self):
        """PDF animal line includes category when present."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            breed="Labrador",
            animal_category="Mascota",
            age="3 años",
            animal_identification="Rex",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
        )

        line = _build_animal_line(protocol)

        self.assertIn("Canino", line)
        self.assertIn("Labrador", line)
        self.assertIn("Mascota", line)


class HistopathologySlideEditDeleteTests(TestCase):
    """Tests for HP slide edit/delete (item 9)."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
            email_verified=True,
        )
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            last_name="García",
            first_name="Carlos",
            license_number="VET-001",
            email="vet@example.com",
        )
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Felino",
            animal_identification="Luna",
            presumptive_diagnosis="Tumor",
            submission_date=date.today(),
        )
        self.protocol.submit()
        self.protocol.receive(
            received_by=self.staff_user,
            sample_condition=Protocol.SampleCondition.OPTIMAL,
        )
        self.sample = HistopathologySample.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            material_submitted="Masa",
            number_of_containers=1,
            preservation="Formol 10%",
        )
        self.cassette = Cassette.objects.create(
            histopathology_sample=self.sample,
            material_incluido="Tejido mamario",
        )
        self.slide = Slide.objects.create(
            protocol=self.protocol,
            tecnica_coloracion="Hematoxilina-Eosina",
            observaciones="Original",
        )
        self.slide.cassette_slides.create(
            cassette=self.cassette,
            coloracion="Hematoxilina-Eosina",
        )
        self.client = Client()

    def test_update_existing_slide(self):
        """Staff can update slide coloration, observations and cassettes."""
        self.client.login(email="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse(
                "protocols:sample_register",
                kwargs={"protocol_pk": self.protocol.pk},
            ),
            data={
                "cassette_count": "0",
                "slide_count": "0",
                "existing_slide_ids": [str(self.slide.pk)],
                f"existing_slide_{self.slide.pk}_cassettes": [
                    f"existing_{self.cassette.pk}"
                ],
                f"existing_slide_{self.slide.pk}_coloracion": "PAS",
                f"existing_slide_{self.slide.pk}_observaciones": "Corregido",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.slide.refresh_from_db()
        self.assertEqual(self.slide.tecnica_coloracion, "PAS")
        self.assertEqual(self.slide.observaciones, "Corregido")
        self.assertTrue(
            ProcessingLog.objects.filter(
                protocol=self.protocol,
                slide=self.slide,
                observaciones__contains="actualizado",
            ).exists()
        )

    def test_delete_existing_slide(self):
        """Staff can delete a slide that is not in a finalized report."""
        self.client.login(email="staff@example.com", password="testpass123")
        slide_pk = self.slide.pk

        response = self.client.post(
            reverse("protocols:slide_delete", kwargs={"slide_pk": slide_pk}),
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Slide.objects.filter(pk=slide_pk).exists())
        self.assertTrue(
            ProcessingLog.objects.filter(
                protocol=self.protocol,
                observaciones__contains="eliminado",
            ).exists()
        )

    def test_delete_slide_blocked_when_in_finalized_report(self):
        """Cannot delete slide referenced by a finalized report image."""
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            diagnosis="Diagnóstico",
            status=Report.Status.FINALIZED,
        )
        ReportImage.objects.create(
            report=report,
            slide=self.slide,
            image=_make_test_image(),
        )
        self.client.login(email="staff@example.com", password="testpass123")

        response = self.client.post(
            reverse(
                "protocols:slide_delete", kwargs={"slide_pk": self.slide.pk}
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Slide.objects.filter(pk=self.slide.pk).exists())


@override_settings(
    MEDIA_ROOT="/tmp/adlab_test_roadmap_pdf_images",
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class ReportImageIncludeInPdfTests(TestCase):
    """Tests for ReportImage.include_in_pdf (item 10)."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
            email_verified=True,
        )
        self.laboratory_staff = LaboratoryStaff.objects.create(
            user=self.staff_user,
            last_name="Pérez",
            first_name="Ana",
            license_number="MP-12345",
            can_create_reports=True,
        )
        self.laboratory_staff.signature_image.save(
            "sig.png", _make_test_image("sig.png"), save=True
        )
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            last_name="García",
            first_name="Carlos",
            license_number="VET-001",
            email="vet@example.com",
        )
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Rex",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
            status=Protocol.Status.READY,
            protocol_number="HP 24/100",
        )
        self.report = Report.objects.create(
            protocol=self.protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            diagnosis="Diagnóstico final",
            status=Report.Status.FINALIZED,
        )

    def test_existing_images_default_include_in_pdf(self):
        """Migration default keeps existing images included in PDF."""
        image = ReportImage.objects.create(
            report=self.report,
            image=_make_test_image("one.jpg"),
        )
        self.assertTrue(image.include_in_pdf)

    def test_pdf_excludes_images_not_marked_for_print(self):
        """PDF generation skips images with include_in_pdf=False."""
        ReportImage.objects.create(
            report=self.report,
            image=_make_test_image("included.jpg"),
            description="Incluida",
            include_in_pdf=True,
        )
        ReportImage.objects.create(
            report=self.report,
            image=_make_test_image("excluded.jpg"),
            description="Excluida",
            include_in_pdf=False,
        )

        pdf_buffer, _pdf_hash = PDFGenerationService().generate_report_pdf(
            self.report
        )
        pdf_bytes = pdf_buffer.getvalue()

        self.assertGreater(len(pdf_bytes), 500)
        self.assertEqual(
            self.report.images.filter(include_in_pdf=True).count(), 1
        )
