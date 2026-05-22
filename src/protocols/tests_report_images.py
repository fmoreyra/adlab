"""
Tests for report microscopy image uploads and PDF embedding.
"""

from datetime import date
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image as PILImage

from accounts.models import LaboratoryStaff, User, Veterinarian
from protocols.models import (
    Cassette,
    HistopathologySample,
    Protocol,
    Report,
    ReportImage,
)
from protocols.services.pdf_service import PDFGenerationService
from protocols.services.report_image_service import (
    MAX_REPORT_IMAGE_SIZE_BYTES,
    ReportImageService,
)


def _make_test_image(name="test.jpg", size=(100, 100), color="red"):
    """Create a small in-memory JPEG for upload tests."""
    buffer = BytesIO()
    PILImage.new("RGB", size, color).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name,
        buffer.read(),
        content_type="image/jpeg",
    )


@override_settings(
    MEDIA_ROOT="/tmp/adlab_test_report_images",
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class ReportImageServiceTests(TestCase):
    """Unit tests for report image validation and storage."""

    def test_validate_upload_rejects_oversized_file(self):
        """Files larger than 10 MB are rejected."""
        large = SimpleUploadedFile(
            "big.jpg",
            b"x" * (MAX_REPORT_IMAGE_SIZE_BYTES + 1),
            content_type="image/jpeg",
        )
        with self.assertRaises(ValidationError):
            ReportImageService.validate_upload(large)

    def test_validate_upload_accepts_jpeg(self):
        """Valid JPEG uploads pass validation."""
        ReportImageService.validate_upload(_make_test_image())


class ReportImageUploadViewTests(TestCase):
    """Integration tests for uploading images on report edit."""

    def setUp(self):
        self.client = Client()
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
        sig = _make_test_image("sig.png")
        self.laboratory_staff.signature_image.save("sig.png", sig, save=True)

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
            presumptive_diagnosis="Masa cutánea",
            submission_date=date.today(),
            status=Protocol.Status.READY,
            protocol_number="HP 24/099",
        )
        self.histopathology_sample = HistopathologySample.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            material_submitted="Biopsia",
            number_of_containers=1,
            preservation="Formol",
        )
        self.cassette = Cassette.objects.create(
            histopathology_sample=self.histopathology_sample,
            codigo_cassette="HP 24/099-A1",
            material_incluido="Masa",
        )
        self.report = Report.objects.create(
            protocol=self.protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            diagnosis="Dermatitis",
            status=Report.Status.DRAFT,
        )

        self.client.login(email="staff@example.com", password="testpass123")

    def test_upload_image_via_report_edit(self):
        """POST on report edit saves image to storage and database."""
        image_file = _make_test_image()
        response = self.client.post(
            reverse("protocols:report_edit", kwargs={"pk": self.report.pk}),
            data={
                "laboratory_staff": self.laboratory_staff.pk,
                "macroscopic_observations": "",
                "microscopic_observations": "",
                "diagnosis": "Dermatitis",
                "comments": "",
                "recommendations": "",
                "form-TOTAL_FORMS": "0",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "images-TOTAL_FORMS": "1",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "20",
                "images-0-cassette": self.cassette.pk,
                "images-0-slide": "",
                "images-0-image": image_file,
                "images-0-description": "Infiltrado inflamatorio",
                "images-0-magnification": "400x",
                "images-0-technique": "H&E",
                "images-0-order": "0",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.report.images.count(), 1)
        report_image = self.report.images.first()
        self.assertTrue(report_image.image.name)
        self.assertEqual(report_image.magnification, "400x")
        self.assertEqual(report_image.cassette_id, self.cassette.pk)

    def test_delete_image_via_report_edit(self):
        """Deleting an image removes the database row and stored file."""
        report_image = ReportImage.objects.create(
            report=self.report,
            cassette=self.cassette,
            image=_make_test_image("stored.jpg"),
            magnification="100x",
        )
        storage_name = report_image.image.name

        response = self.client.post(
            reverse("protocols:report_edit", kwargs={"pk": self.report.pk}),
            data={
                "laboratory_staff": self.laboratory_staff.pk,
                "macroscopic_observations": "",
                "microscopic_observations": "",
                "diagnosis": "Dermatitis",
                "comments": "",
                "recommendations": "",
                "form-TOTAL_FORMS": "0",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "images-TOTAL_FORMS": "1",
                "images-INITIAL_FORMS": "1",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "20",
                "images-0-id": report_image.pk,
                "images-0-cassette": self.cassette.pk,
                "images-0-slide": "",
                "images-0-description": "",
                "images-0-magnification": "100x",
                "images-0-technique": "",
                "images-0-order": "0",
                "images-0-DELETE": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ReportImage.objects.filter(pk=report_image.pk).exists()
        )
        self.assertFalse(default_storage.exists(storage_name))

    def test_pdf_includes_uploaded_image(self):
        """Generated PDF is produced when the report has microscopy images."""
        ReportImage.objects.create(
            report=self.report,
            image=_make_test_image("micro.jpg"),
            description="Hallazgo principal",
            magnification="400x",
        )
        self.report.status = Report.Status.FINALIZED
        self.report.save()

        pdf_buffer, pdf_hash = PDFGenerationService().generate_report_pdf(
            self.report
        )

        self.assertGreater(len(pdf_buffer.getvalue()), 500)
        self.assertEqual(len(pdf_hash), 64)


class ProtocolReportImagesViewTests(TestCase):
    """Tests for protocol-scoped image gallery and detail views."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            email="gallery@example.com",
            username="gallery",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
            email_verified=True,
        )
        self.laboratory_staff = LaboratoryStaff.objects.create(
            user=self.staff_user,
            last_name="López",
            first_name="Ana",
            license_number="MP-GAL-01",
            can_create_reports=True,
        )
        self.laboratory_staff.signature_image.save(
            "sig.png", _make_test_image("sig.png"), save=True
        )

        self.veterinarian_user = User.objects.create_user(
            email="vetgal@example.com",
            username="vetgal",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        from accounts.models import Address

        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            last_name="Vet",
            first_name="Test",
            license_number="VET-GAL",
            cuil_cuit="20-11111111-1",
            phone="+54 341 5550000",
            email="vetgal@example.com",
        )
        Address.objects.create(
            veterinarian=self.veterinarian,
            province="Santa Fe",
            locality="Rosario",
            street="San Martín",
            number="1",
        )
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Rex",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
            status=Protocol.Status.REPORT_SENT,
            protocol_number="HP 24/200",
        )
        self.report = Report.objects.create(
            protocol=self.protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            diagnosis="OK",
            status=Report.Status.FINALIZED,
        )
        self.report_image = ReportImage.objects.create(
            report=self.report,
            image=_make_test_image("gal.jpg"),
            magnification="400x",
        )

    def test_gallery_accessible_by_lab_staff(self):
        """Lab staff can open the protocol image gallery."""
        self.client.login(email="gallery@example.com", password="testpass123")
        url = reverse(
            "protocols:protocol_report_images",
            kwargs={"pk": self.protocol.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Imágenes microscópicas")
        self.assertContains(response, "400x")

    def test_image_detail_accessible_by_veterinarian(self):
        """Veterinarian owner can open a single image detail view."""
        self.client.login(email="vetgal@example.com", password="testpass123")
        url = reverse(
            "protocols:protocol_report_image_detail",
            kwargs={"pk": self.protocol.pk, "image_pk": self.report_image.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detalle de imagen")


class ReportFinalizePdfTests(TestCase):
    """Finalize persists PDF with microscopy images to storage."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            email="fin@example.com",
            username="fin",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
            email_verified=True,
        )
        self.laboratory_staff = LaboratoryStaff.objects.create(
            user=self.staff_user,
            last_name="Fin",
            first_name="Test",
            license_number="MP-FIN-01",
            can_create_reports=True,
        )
        self.laboratory_staff.signature_image.save(
            "sig.png", _make_test_image("sig.png"), save=True
        )
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email="vfin@example.com",
                username="vfin",
                password="testpass123",
                role=User.Role.VETERINARIO,
                email_verified=True,
            ),
            last_name="V",
            first_name="T",
            license_number="V-FIN",
            email="vfin@example.com",
        )
        self.protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Masa",
            submission_date=date.today(),
            status=Protocol.Status.READY,
            protocol_number="HP 24/201",
        )
        self.report = Report.objects.create(
            protocol=self.protocol,
            laboratory_staff=self.laboratory_staff,
            veterinarian=self.veterinarian,
            diagnosis="Diagnóstico final",
            status=Report.Status.DRAFT,
        )
        ReportImage.objects.create(
            report=self.report,
            image=_make_test_image("fin.jpg"),
            magnification="100x",
        )
        self.client.login(email="fin@example.com", password="testpass123")

    def test_finalize_persists_pdf_path(self):
        """Finalizing generates and stores the PDF path on the report."""
        response = self.client.post(
            reverse("protocols:report_finalize", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, Report.Status.FINALIZED)
        self.assertTrue(self.report.pdf_path)
        self.assertEqual(len(self.report.pdf_hash), 64)
