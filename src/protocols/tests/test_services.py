"""
Tests for protocol services.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase

from accounts.models import User, Veterinarian
from protocols.models import (
    Cassette,
    Protocol,
    Slide,
)
from protocols.services.email_service import EmailNotificationService
from protocols.services.protocol_service import (
    ProtocolProcessingService,
    ProtocolReceptionService,
)
from protocols.services.workorder_service import (
    WorkOrderCalculationService,
    WorkOrderCreationService,
)


class EmailNotificationServiceTest(TestCase):
    """Test cases for EmailNotificationService."""

    def setUp(self):
        """Set up test data."""
        self.service = EmailNotificationService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            license_number="12345",
            email="test@example.com",
        )
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
        )

    @patch(
        "protocols.services.email_service.send_sample_reception_notification"
    )
    def test_send_reception_email_success(self, mock_send):
        """Test successful reception email sending."""
        mock_email_log = Mock()
        mock_email_log.id = 1
        mock_send.return_value = mock_email_log

        result = self.service.send_reception_email(self.protocol)

        self.assertTrue(result)
        mock_send.assert_called_once_with(self.protocol)

    @patch(
        "protocols.services.email_service.send_sample_reception_notification"
    )
    def test_send_reception_email_skipped(self, mock_send):
        """Test reception email skipped due to preferences."""
        mock_send.return_value = None

        result = self.service.send_reception_email(self.protocol)

        self.assertFalse(result)
        mock_send.assert_called_once_with(self.protocol)

    @patch(
        "protocols.services.email_service.send_sample_reception_notification"
    )
    def test_send_reception_email_exception(self, mock_send):
        """Test reception email sending with exception."""
        mock_send.side_effect = Exception("Email service error")

        result = self.service.send_reception_email(self.protocol)

        self.assertFalse(result)

    @patch("protocols.services.email_service.queue_email")
    def test_send_submission_confirmation_email_success(self, mock_queue):
        """Test successful submission confirmation email."""
        mock_email_log = Mock()
        mock_email_log.id = 1
        mock_queue.return_value = mock_email_log

        result = self.service.send_submission_confirmation_email(self.protocol)

        self.assertTrue(result)
        mock_queue.assert_called_once()

    @patch("protocols.services.email_service.queue_email")
    def test_send_discrepancy_alert_email_success(self, mock_queue):
        """Test successful discrepancy alert email."""
        mock_email_log = Mock()
        mock_email_log.id = 1
        mock_queue.return_value = mock_email_log

        result = self.service.send_discrepancy_alert_email(
            self.protocol, "Sample damaged", "POOR"
        )

        self.assertTrue(result)
        mock_queue.assert_called_once()


class ProtocolReceptionServiceTest(TestCase):
    """Test cases for ProtocolReceptionService."""

    def setUp(self):
        """Set up test data."""
        self.service = ProtocolReceptionService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Role.STAFF,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email="vet@example.com",
                password="testpass123",
                role=User.Role.VETERINARIO,
            ),
            license_number="12345",
            email="vet@example.com",
        )
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.SUBMITTED,
        )

    def test_validate_protocol_for_reception_valid(self):
        """Test validation of valid protocol for reception."""
        is_valid, error = self.service.validate_protocol_for_reception(
            self.protocol
        )

        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validate_protocol_for_reception_already_processed(self):
        """Test validation of already processed protocol."""
        self.protocol.status = Protocol.Status.RECEIVED

        is_valid, error = self.service.validate_protocol_for_reception(
            self.protocol
        )

        self.assertFalse(is_valid)
        self.assertIn("ya fue procesado", error)

    @patch(
        "protocols.services.protocol_service.ProtocolStatusHistory.log_status_change"
    )
    @patch("protocols.services.protocol_service.ReceptionLog.log_action")
    def test_process_reception_success(self, mock_log_action, mock_log_status):
        """Test successful protocol reception processing."""
        form_data = {
            "sample_condition": "GOOD",
            "reception_notes": "Sample received in good condition",
            "discrepancies": "",
        }

        success, error = self.service.process_reception(
            self.protocol, form_data, self.user
        )

        self.assertTrue(success)
        self.assertEqual(error, "")
        self.protocol.refresh_from_db()
        self.assertEqual(self.protocol.status, Protocol.Status.RECEIVED)
        mock_log_action.assert_called_once()
        mock_log_status.assert_called_once()

    def test_process_reception_with_cytology_sample(self):
        """Test reception processing with cytology sample updates."""
        from protocols.models import CytologySample

        cytology_sample = CytologySample.objects.create(
            protocol=self.protocol,
            number_slides_expected=5,
        )

        form_data = {
            "sample_condition": "GOOD",
            "reception_notes": "",
            "discrepancies": "",
            "number_slides_received": 4,
        }

        success, error = self.service.process_reception(
            self.protocol, form_data, self.user
        )

        self.assertTrue(success)
        cytology_sample.refresh_from_db()
        self.assertEqual(cytology_sample.number_slides_received, 4)


class ProtocolProcessingServiceTest(TestCase):
    """Test cases for ProtocolProcessingService."""

    def setUp(self):
        """Set up test data."""
        self.service = ProtocolProcessingService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Role.STAFF,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email="vet@example.com",
                password="testpass123",
                role=User.Role.VETERINARIO,
            ),
            license_number="12345",
            email="vet@example.com",
        )
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.RECEIVED,
        )

    def test_create_cassettes_invalid_protocol_type(self):
        """Test cassette creation for non-histopathology protocol."""
        self.protocol.analysis_type = Protocol.AnalysisType.CYTOLOGY

        success, cassettes, error = self.service.create_cassettes(
            self.protocol, [], self.user
        )

        self.assertFalse(success)
        self.assertEqual(len(cassettes), 0)
        self.assertIn("histopatología", error)

    def test_create_cassettes_no_histopathology_sample(self):
        """Test cassette creation without histopathology sample."""
        success, cassettes, error = self.service.create_cassettes(
            self.protocol, [], self.user
        )

        self.assertFalse(success)
        self.assertEqual(len(cassettes), 0)
        self.assertIn("muestra de histopatología", error)

    def test_create_cassettes_success(self):
        """Test successful cassette creation."""
        from protocols.models import HistopathologySample

        HistopathologySample.objects.create(
            protocol=self.protocol,
            number_jars_expected=3,
        )

        cassette_data = [
            {
                "material": "Skin biopsy",
                "tipo": Cassette.CassetteType.NORMAL,
                "color": Cassette.CassetteColor.BLANCO,
                "observaciones": "Good quality sample",
            }
        ]

        success, cassettes, error = self.service.create_cassettes(
            self.protocol, cassette_data, self.user
        )

        self.assertTrue(success)
        self.assertEqual(len(cassettes), 1)
        self.assertEqual(error, "")
        self.assertEqual(cassettes[0].material_incluido, "Skin biopsy")

        # Check protocol status updated
        self.protocol.refresh_from_db()
        self.assertEqual(self.protocol.status, Protocol.Status.PROCESSING)

    def test_register_slides_success(self):
        """Test successful slide registration."""
        slide_data = [
            {
                "codigo_portaobjetos": "SLIDE001",
                "campo": 1,
                "tecnica_coloracion": "H&E",
                "observaciones": "Good quality",
            }
        ]

        success, slides, error = self.service.register_slides(
            self.protocol, slide_data, self.user
        )

        self.assertTrue(success)
        self.assertEqual(len(slides), 1)
        self.assertEqual(error, "")
        self.assertEqual(slides[0].codigo_portaobjetos, "SLIDE001")

    def test_update_slide_stage_success(self):
        """Test successful slide stage update."""
        slide = Slide.objects.create(
            protocol=self.protocol,
            codigo_portaobjetos="SLIDE001",
            estado=Slide.Status.PENDIENTE,
        )

        success, error = self.service.update_slide_stage(
            slide, "montaje", self.user, "Stage updated"
        )

        self.assertTrue(success)
        self.assertEqual(error, "")
        slide.refresh_from_db()
        self.assertEqual(slide.estado, Slide.Status.MONTADO)

    def test_update_slide_stage_invalid(self):
        """Test slide stage update with invalid stage."""
        slide = Slide.objects.create(
            protocol=self.protocol,
            codigo_portaobjetos="SLIDE001",
            estado=Slide.Status.PENDIENTE,
        )

        success, error = self.service.update_slide_stage(
            slide, "invalid_stage", self.user
        )

        self.assertFalse(success)
        self.assertIn("no válida", error)


class WorkOrderCalculationServiceTest(TestCase):
    """Test cases for WorkOrderCalculationService."""

    def setUp(self):
        """Set up test data."""
        self.service = WorkOrderCalculationService()
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email="vet@example.com",
                password="testpass123",
                role=User.Role.VETERINARIO,
            ),
            license_number="12345",
            email="vet@example.com",
        )

    def test_calculate_services_cytology(self):
        """Test service calculation for cytology protocol."""
        protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
        )

        result = self.service.calculate_services([protocol])

        self.assertEqual(len(result["services"]), 1)
        self.assertEqual(result["services"][0]["service_type"], "citologia")
        self.assertEqual(result["services"][0]["quantity"], 1)
        self.assertIsInstance(result["subtotal"], Decimal)
        self.assertIsInstance(result["total"], Decimal)

    def test_calculate_services_histopathology(self):
        """Test service calculation for histopathology protocol."""
        protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST002",
            species="Felino",
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
        )

        result = self.service.calculate_services([protocol])

        self.assertEqual(len(result["services"]), 1)
        self.assertEqual(
            result["services"][0]["service_type"], "histopatologia_2a5_piezas"
        )
        self.assertEqual(result["services"][0]["quantity"], 1)

    def test_calculate_services_multiple_protocols(self):
        """Test service calculation for multiple protocols."""
        protocol1 = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
        )
        protocol2 = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST002",
            species="Felino",
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
        )

        result = self.service.calculate_services([protocol1, protocol2])

        self.assertEqual(len(result["services"]), 2)
        self.assertEqual(result["subtotal"], result["total"])


class WorkOrderCreationServiceTest(TestCase):
    """Test cases for WorkOrderCreationService."""

    def setUp(self):
        """Set up test data."""
        self.service = WorkOrderCreationService()
        self.user = User.objects.create_user(
            email="staff@example.com",
            password="testpass123",
            role=User.Role.STAFF,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email="vet@example.com",
                password="testpass123",
                role=User.Role.VETERINARIO,
            ),
            license_number="12345",
            email="vet@example.com",
        )

    def test_validate_protocols_empty(self):
        """Test validation with empty protocol list."""
        from protocols.models import Protocol

        success, error = self.service.validate_protocols_for_work_order(
            Protocol.objects.none()
        )

        self.assertFalse(success)
        self.assertIn("No se encontraron protocolos", error)

    def test_validate_protocols_different_veterinarians(self):
        """Test validation with protocols from different veterinarians."""
        vet2 = Veterinarian.objects.create(
            user=User.objects.create_user(
                email="vet2@example.com",
                password="testpass123",
                role=User.Role.VETERINARIO,
            ),
            license_number="67890",
            email="vet2@example.com",
        )

        protocol1 = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.READY,
        )
        protocol2 = Protocol.objects.create(
            veterinarian=vet2,
            animal_identification="TEST002",
            species="Felino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.READY,
        )

        success, error = self.service.validate_protocols_for_work_order(
            [protocol1, protocol2]
        )

        self.assertFalse(success)
        self.assertIn("mismo veterinario", error)

    def test_validate_protocols_not_ready(self):
        """Test validation with protocols not ready for work order."""
        protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.RECEIVED,  # Not READY
        )

        success, error = self.service.validate_protocols_for_work_order(
            [protocol]
        )

        self.assertFalse(success)
        self.assertIn("no está listo", error)

    def test_validate_protocols_already_has_work_order(self):
        """Test validation with protocol that already has work order."""
        from protocols.models import Protocol, WorkOrder

        work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            order_number="WO001",
            total_amount=Decimal("10.00"),
            created_by=self.user,
        )

        protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            animal_identification="TEST001",
            species="Canino",
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.READY,
            work_order=work_order,
        )

        success, error = self.service.validate_protocols_for_work_order(
            [protocol]
        )

        self.assertFalse(success)
        self.assertIn("ya tiene una orden", error)
