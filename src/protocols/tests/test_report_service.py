"""
Tests for ReportGenerationService.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from protocols.models import Protocol, Report
from protocols.services.report_service import ReportGenerationService

User = get_user_model()


class ReportGenerationServiceTest(TestCase):
    """Test cases for ReportGenerationService."""

    def setUp(self):
        """Set up test data."""
        self.service = ReportGenerationService()

        # Create test users
        self.veterinarian_user = User.objects.create_user(
            email="vet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.histopathologist_user = User.objects.create_user(
            email="histo@test.com",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
        )

        # Create veterinarian profile
        self.veterinarian = self.veterinarian_user.veterinarian_profile
        self.veterinarian.license_number = "VET123"
        self.veterinarian.save()

        # Create histopathologist profile
        self.histopathologist = (
            self.histopathologist_user.histopathologist_profile
        )
        self.histopathologist.license_number = "HISTO123"
        self.histopathologist.save()

        # Create test protocol
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            animal_identification="Test Animal",
            species="Canine",
            status=Protocol.Status.READY,
        )

    def test_validate_protocol_for_report_success(self):
        """Test successful protocol validation for report creation."""
        is_valid, error_message = self.service.validate_protocol_for_report(
            self.protocol
        )

        self.assertTrue(is_valid)
        self.assertEqual(error_message, "")

    def test_validate_protocol_for_report_wrong_status(self):
        """Test protocol validation with wrong status."""
        self.protocol.status = Protocol.Status.DRAFT
        self.protocol.save()

        is_valid, error_message = self.service.validate_protocol_for_report(
            self.protocol
        )

        self.assertFalse(is_valid)
        self.assertIn("READY status", error_message)

    def test_validate_protocol_for_report_existing_report(self):
        """Test protocol validation when report already exists."""
        # Create existing report
        Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
        )

        is_valid, error_message = self.service.validate_protocol_for_report(
            self.protocol
        )

        self.assertFalse(is_valid)
        self.assertIn("already exists", error_message)

    def test_validate_protocol_for_report_missing_animal_id(self):
        """Test protocol validation with missing animal identification."""
        self.protocol.animal_identification = ""
        self.protocol.save()

        is_valid, error_message = self.service.validate_protocol_for_report(
            self.protocol
        )

        self.assertFalse(is_valid)
        self.assertIn("animal identification", error_message)

    def test_validate_protocol_for_report_missing_species(self):
        """Test protocol validation with missing species."""
        self.protocol.species = ""
        self.protocol.save()

        is_valid, error_message = self.service.validate_protocol_for_report(
            self.protocol
        )

        self.assertFalse(is_valid)
        self.assertIn("species information", error_message)

    def test_create_report_success(self):
        """Test successful report creation."""
        success, report, error_message = self.service.create_report(
            self.protocol, self.histopathologist_user
        )

        self.assertTrue(success)
        self.assertIsNotNone(report)
        self.assertEqual(error_message, "")
        self.assertEqual(report.protocol, self.protocol)
        self.assertEqual(report.histopathologist, self.histopathologist_user)
        self.assertEqual(report.status, Report.Status.DRAFT)
        self.assertEqual(report.version, 1)

    def test_create_report_validation_failure(self):
        """Test report creation with validation failure."""
        self.protocol.status = Protocol.Status.DRAFT
        self.protocol.save()

        success, report, error_message = self.service.create_report(
            self.protocol, self.histopathologist_user
        )

        self.assertFalse(success)
        self.assertIsNone(report)
        self.assertIn("READY status", error_message)

    def test_update_report_content_success(self):
        """Test successful report content update."""
        # Create report
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
        )

        content_data = {
            "macroscopic_observations": "Test macroscopic observations",
            "microscopic_observations": "Test microscopic observations",
            "diagnosis": "Test diagnosis",
            "comments": "Test comments",
            "recommendations": "Test recommendations",
        }

        success, error_message = self.service.update_report_content(
            report, content_data, self.histopathologist_user
        )

        self.assertTrue(success)
        self.assertEqual(error_message, "")

        # Refresh from database
        report.refresh_from_db()
        self.assertEqual(
            report.macroscopic_observations,
            content_data["macroscopic_observations"],
        )
        self.assertEqual(
            report.microscopic_observations,
            content_data["microscopic_observations"],
        )
        self.assertEqual(report.diagnosis, content_data["diagnosis"])
        self.assertEqual(report.comments, content_data["comments"])
        self.assertEqual(
            report.recommendations, content_data["recommendations"]
        )

    def test_update_report_content_wrong_status(self):
        """Test report content update with wrong status."""
        # Create finalized report
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.FINALIZED,
        )

        content_data = {"diagnosis": "Test diagnosis"}

        success, error_message = self.service.update_report_content(
            report, content_data, self.histopathologist_user
        )

        self.assertFalse(success)
        self.assertIn("DRAFT or REVIEW status", error_message)

    def test_finalize_report_success(self):
        """Test successful report finalization."""
        # Create report with diagnosis
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            diagnosis="Test diagnosis",
        )

        success, error_message = self.service.finalize_report(
            report, self.histopathologist_user
        )

        self.assertTrue(success)
        self.assertEqual(error_message, "")

        # Refresh from database
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.FINALIZED)

        # Check protocol status was updated
        self.protocol.refresh_from_db()
        self.assertEqual(self.protocol.status, Protocol.Status.REPORT_SENT)

    def test_finalize_report_wrong_status(self):
        """Test report finalization with wrong status."""
        # Create finalized report
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.FINALIZED,
        )

        success, error_message = self.service.finalize_report(
            report, self.histopathologist_user
        )

        self.assertFalse(success)
        self.assertIn("DRAFT status", error_message)

    def test_finalize_report_missing_diagnosis(self):
        """Test report finalization without diagnosis."""
        # Create report without diagnosis
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
        )

        success, error_message = self.service.finalize_report(
            report, self.histopathologist_user
        )

        self.assertFalse(success)
        self.assertIn("diagnosis", error_message)

    def test_send_report_success(self):
        """Test successful report sending."""
        # Create finalized report
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.FINALIZED,
        )

        success, error_message = self.service.send_report(
            report, self.histopathologist_user
        )

        self.assertTrue(success)
        self.assertEqual(error_message, "")

        # Refresh from database
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.SENT)

    def test_send_report_wrong_status(self):
        """Test report sending with wrong status."""
        # Create draft report
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.DRAFT,
        )

        success, error_message = self.service.send_report(
            report, self.histopathologist_user
        )

        self.assertFalse(success)
        self.assertIn("finalized", error_message)

    def test_validate_report_content_success(self):
        """Test successful report content validation."""
        content_data = {
            "diagnosis": "Test diagnosis",
            "macroscopic_observations": "Test macroscopic",
            "microscopic_observations": "Test microscopic",
            "cassette_observations": [
                {
                    "cassette_id": 1,
                    "observations": "Test obs",
                    "partial_diagnosis": "Test diag",
                }
            ],
        }

        is_valid, errors = self.service.validate_report_content(content_data)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_report_content_missing_diagnosis(self):
        """Test report content validation with missing diagnosis."""
        content_data = {
            "diagnosis": "",
            "macroscopic_observations": "Test macroscopic",
        }

        is_valid, errors = self.service.validate_report_content(content_data)

        self.assertFalse(is_valid)
        self.assertIn("Diagnosis is required", str(errors[0]))

    def test_validate_report_content_long_diagnosis(self):
        """Test report content validation with diagnosis too long."""
        content_data = {
            "diagnosis": "x" * 1001,  # Too long
            "macroscopic_observations": "Test macroscopic",
        }

        is_valid, errors = self.service.validate_report_content(content_data)

        self.assertFalse(is_valid)
        self.assertIn("too long", str(errors[0]))

    def test_validate_report_content_long_observations(self):
        """Test report content validation with observations too long."""
        content_data = {
            "diagnosis": "Test diagnosis",
            "macroscopic_observations": "x" * 2001,  # Too long
        }

        is_valid, errors = self.service.validate_report_content(content_data)

        self.assertFalse(is_valid)
        self.assertIn("too long", str(errors[0]))

    def test_validate_report_content_invalid_cassette_observations(self):
        """Test report content validation with invalid cassette observations."""
        content_data = {
            "diagnosis": "Test diagnosis",
            "cassette_observations": [
                {
                    "cassette_id": None,
                    "observations": "Test obs",
                }  # Missing cassette_id
            ],
        }

        is_valid, errors = self.service.validate_report_content(content_data)

        self.assertFalse(is_valid)
        self.assertIn("missing cassette ID", str(errors[0]))

    def test_get_report_data_success(self):
        """Test successful report data retrieval."""
        # Create report with content
        report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            diagnosis="Test diagnosis",
            macroscopic_observations="Test macroscopic",
            microscopic_observations="Test microscopic",
        )

        report_data = self.service.get_report_data(report)

        self.assertIsInstance(report_data, dict)
        self.assertEqual(report_data["id"], report.id)
        self.assertEqual(
            report_data["protocol_number"], self.protocol.protocol_number
        )
        self.assertEqual(report_data["content"]["diagnosis"], "Test diagnosis")
        self.assertEqual(
            report_data["veterinarian"]["name"],
            self.veterinarian.get_full_name(),
        )
        self.assertEqual(
            report_data["histopathologist"]["name"],
            self.histopathologist.get_formal_name(),
        )

    def test_get_reports_for_histopathologist(self):
        """Test getting reports for a specific histopathologist."""
        # Create reports
        report1 = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
        )

        # Create another histopathologist and report
        other_histo_user = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
        )
        other_histo = other_histo_user.histopathologist_profile
        other_histo.license_number = "HISTO456"
        other_histo.save()

        Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=other_histo,
        )

        # Get reports for first histopathologist
        reports = self.service.get_reports_for_histopathologist(
            self.histopathologist_user
        )

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0], report1)

    def test_get_reports_for_histopathologist_with_status_filter(self):
        """Test getting reports for histopathologist with status filter."""
        # Create reports with different statuses
        report1 = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.DRAFT,
        )

        Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.FINALIZED,
        )

        # Get only draft reports
        reports = self.service.get_reports_for_histopathologist(
            self.histopathologist_user, status_filter=Report.Status.DRAFT
        )

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0], report1)

    def test_get_reports_for_veterinarian(self):
        """Test getting reports for a specific veterinarian."""
        # Create reports
        report1 = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
        )

        # Create another veterinarian and report
        other_vet_user = User.objects.create_user(
            email="othervet@test.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        other_vet = other_vet_user.veterinarian_profile
        other_vet.license_number = "VET456"
        other_vet.save()

        other_protocol = Protocol.objects.create(
            veterinarian=other_vet,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            animal_identification="Other Animal",
            species="Feline",
            status=Protocol.Status.READY,
        )

        Report.objects.create(
            protocol=other_protocol,
            veterinarian=other_vet,
            histopathologist=self.histopathologist,
        )

        # Get reports for first veterinarian
        reports = self.service.get_reports_for_veterinarian(self.veterinarian)

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0], report1)

    def test_create_report_version_success(self):
        """Test successful report version creation."""
        # Create finalized report
        original_report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.FINALIZED,
            diagnosis="Original diagnosis",
            version=1,
        )

        success, new_report, error_message = (
            self.service.create_report_version(
                original_report, self.histopathologist_user
            )
        )

        self.assertTrue(success)
        self.assertIsNotNone(new_report)
        self.assertEqual(error_message, "")
        self.assertEqual(new_report.version, 2)
        self.assertEqual(new_report.status, Report.Status.DRAFT)
        self.assertEqual(new_report.diagnosis, "Original diagnosis")

    def test_create_report_version_wrong_status(self):
        """Test report version creation with wrong status."""
        # Create draft report
        original_report = Report.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            histopathologist=self.histopathologist,
            status=Report.Status.DRAFT,
        )

        success, new_report, error_message = (
            self.service.create_report_version(
                original_report, self.histopathologist_user
            )
        )

        self.assertFalse(success)
        self.assertIsNone(new_report)
        self.assertIn("finalized or sent", error_message)
