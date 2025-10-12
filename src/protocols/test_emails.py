"""
Tests for email notification functions in protocols.emails module.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from accounts.models import User, Veterinarian
from protocols import emails
from protocols.models import (
    CytologySample,
    EmailLog,
    NotificationPreference,
    Protocol,
    WorkOrder,
    WorkOrderService,
)


class EmailNotificationTest(TestCase):
    """Test email notification system."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            is_active=True,
        )

        # Create veterinarian profile
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            first_name="Dr. Juan",
            last_name="Pérez",
            license_number="VET123",
            phone="123456789",
            email="vet@example.com",
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.SUBMITTED,
            temporary_code="C 25/001",
            protocol_number="C 25/001",
            submission_date=date.today(),
        )

        # Create cytology sample
        self.cytology_sample = CytologySample.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            technique_used="PAAF",
            sampling_site="Test site",
            number_of_slides=2,
        )

        # Create work order
        self.work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            advance_payment=Decimal("100.00"),
            billing_name="Clínica Veterinaria",
            cuit_cuil="20123456789",
            iva_condition="Responsable Inscripto",
            observations="Test work order",
            status=WorkOrder.Status.DRAFT,
        )

        # Add protocol to work order
        self.work_order.protocols.add(self.protocol)

        # Create work order service
        self.work_order_service = WorkOrderService.objects.create(
            work_order=self.work_order,
            protocol=self.protocol,
            description="Análisis citológico",
            service_type="citologia",
            unit_price=Decimal("50.00"),
            quantity=1,
        )

    @patch("protocols.emails.send_email.delay")
    def test_queue_email_basic(self, mock_send_email):
        """Test basic email queueing functionality."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_send_email.return_value = mock_task

        context = {"test": "data"}

        email_log = emails.queue_email(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="test@example.com",
            subject="Test Subject",
            context=context,
        )

        # Check EmailLog was created
        self.assertEqual(email_log.email_type, EmailLog.EmailType.CUSTOM)
        self.assertEqual(email_log.recipient_email, "test@example.com")
        self.assertEqual(email_log.subject, "Test Subject")
        self.assertEqual(email_log.status, EmailLog.Status.QUEUED)
        self.assertEqual(email_log.celery_task_id, "test-task-id")

        # Check Celery task was called
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        self.assertEqual(call_args[1]["email_type"], EmailLog.EmailType.CUSTOM)
        self.assertEqual(call_args[1]["recipient_email"], "test@example.com")
        self.assertEqual(call_args[1]["subject"], "Test Subject")
        self.assertEqual(call_args[1]["context"], context)

    @patch("protocols.emails.send_email.delay")
    def test_queue_email_with_protocol(self, mock_send_email):
        """Test email queueing with protocol context."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_send_email.return_value = mock_task

        context = {"protocol": self.protocol}

        email_log = emails.queue_email(
            email_type=EmailLog.EmailType.SAMPLE_RECEPTION,
            recipient_email="test@example.com",
            subject="Sample Received",
            context=context,
            protocol=self.protocol,
            veterinarian=self.veterinarian,
        )

        # Check EmailLog was created with protocol
        self.assertEqual(email_log.protocol, self.protocol)
        self.assertEqual(email_log.recipient, self.veterinarian)
        self.assertEqual(
            email_log.email_type, EmailLog.EmailType.SAMPLE_RECEPTION
        )

    @patch("protocols.emails.send_email.delay")
    def test_queue_email_with_work_order(self, mock_send_email):
        """Test email queueing with work order context."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_send_email.return_value = mock_task

        context = {"work_order": self.work_order}

        email_log = emails.queue_email(
            email_type=EmailLog.EmailType.WORK_ORDER,
            recipient_email="test@example.com",
            subject="Work Order",
            context=context,
            work_order=self.work_order,
            veterinarian=self.veterinarian,
        )

        # Check EmailLog was created with work order
        self.assertEqual(email_log.work_order, self.work_order)
        self.assertEqual(email_log.recipient, self.veterinarian)
        self.assertEqual(email_log.email_type, EmailLog.EmailType.WORK_ORDER)

    @patch("protocols.emails.send_email.delay")
    def test_queue_email_with_attachment(self, mock_send_email):
        """Test email queueing with PDF attachment."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_send_email.return_value = mock_task

        attachment_path = "/path/to/report.pdf"

        email_log = emails.queue_email(
            email_type=EmailLog.EmailType.REPORT_READY,
            recipient_email="test@example.com",
            subject="Report Ready",
            context={},
            attachment_path=attachment_path,
        )

        # Check EmailLog was created with attachment flag
        self.assertTrue(email_log.has_attachment)

        # Check Celery task was called with attachment
        call_args = mock_send_email.call_args
        self.assertEqual(call_args[1]["attachment_path"], attachment_path)

    @patch("protocols.emails.queue_email")
    def test_send_verification_email(self, mock_queue_email):
        """Test email verification email sending."""
        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        verification_url = "https://example.com/verify/token123"

        result = emails.send_verification_email(
            user=self.veterinarian_user,
            verification_url=verification_url,
        )

        # Check queue_email was called with correct parameters
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertEqual(
            call_args[1]["email_type"], EmailLog.EmailType.EMAIL_VERIFICATION
        )
        self.assertEqual(
            call_args[1]["recipient_email"], self.veterinarian_user.email
        )
        self.assertEqual(
            call_args[1]["subject"],
            "Verifique su correo electrónico - AdLab Veterinario",
        )
        self.assertEqual(
            call_args[1]["context"]["user"], self.veterinarian_user
        )
        self.assertEqual(
            call_args[1]["context"]["verification_url"], verification_url
        )

        self.assertEqual(result, mock_email_log)

    @patch("protocols.emails.queue_email")
    def test_send_password_reset_email(self, mock_queue_email):
        """Test password reset email sending."""
        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        reset_url = "https://example.com/reset/token123"
        expiry_hours = 2

        result = emails.send_password_reset_email(
            user=self.veterinarian_user,
            reset_url=reset_url,
            expiry_hours=expiry_hours,
        )

        # Check queue_email was called with correct parameters
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertEqual(
            call_args[1]["email_type"], EmailLog.EmailType.PASSWORD_RESET
        )
        self.assertEqual(
            call_args[1]["recipient_email"], self.veterinarian_user.email
        )
        self.assertEqual(
            call_args[1]["subject"],
            "Restablezca su contraseña - AdLab Veterinario",
        )
        self.assertEqual(
            call_args[1]["context"]["user"], self.veterinarian_user
        )
        self.assertEqual(call_args[1]["context"]["reset_url"], reset_url)
        self.assertEqual(call_args[1]["context"]["expiry_hours"], expiry_hours)

        self.assertEqual(result, mock_email_log)

    @patch("protocols.emails.queue_email")
    def test_send_sample_reception_notification_with_preferences(
        self, mock_queue_email
    ):
        """Test sample reception notification with preferences enabled."""
        # Create notification preferences
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            notify_on_reception=True,
            alternative_email="alt@example.com",
        )

        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        emails.send_sample_reception_notification(self.protocol)

        # Check queue_email was called
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertEqual(
            call_args[1]["email_type"], EmailLog.EmailType.SAMPLE_RECEPTION
        )
        self.assertEqual(
            call_args[1]["recipient_email"], "alt@example.com"
        )  # Alternative email
        self.assertEqual(
            call_args[1]["subject"],
            f"Muestra recibida - Protocolo {self.protocol.protocol_number}",
        )
        self.assertEqual(call_args[1]["protocol"], self.protocol)
        self.assertEqual(call_args[1]["veterinarian"], self.veterinarian)

    @patch("protocols.emails.queue_email")
    def test_send_sample_reception_notification_preferences_disabled(
        self, mock_queue_email
    ):
        """Test sample reception notification with preferences disabled."""
        # Create notification preferences with notify_on_reception disabled
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            notify_on_reception=False,
        )

        result = emails.send_sample_reception_notification(self.protocol)

        # Check queue_email was NOT called
        mock_queue_email.assert_not_called()
        self.assertIsNone(result)

    @patch("protocols.emails.queue_email")
    def test_send_sample_reception_notification_default_preferences(
        self, mock_queue_email
    ):
        """Test sample reception notification with default preferences (enabled)."""
        # No preferences created - should use defaults (enabled)
        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        emails.send_sample_reception_notification(self.protocol)

        # Check queue_email was called with primary email
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertEqual(
            call_args[1]["recipient_email"], self.veterinarian.email
        )

    @patch("protocols.emails.queue_email")
    def test_send_report_ready_notification_with_attachment(
        self, mock_queue_email
    ):
        """Test report ready notification with PDF attachment."""
        # Create notification preferences
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            notify_on_report_ready=True,
            include_attachments=True,
        )

        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        report_pdf_path = "/path/to/report.pdf"

        emails.send_report_ready_notification(
            protocol=self.protocol,
            report_pdf_path=report_pdf_path,
        )

        # Check queue_email was called with attachment
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertEqual(
            call_args[1]["email_type"], EmailLog.EmailType.REPORT_READY
        )
        self.assertEqual(call_args[1]["attachment_path"], report_pdf_path)
        self.assertEqual(call_args[1]["context"]["has_attachment"], True)

    @patch("protocols.emails.queue_email")
    def test_send_report_ready_notification_no_attachment(
        self, mock_queue_email
    ):
        """Test report ready notification without attachment."""
        # Create notification preferences
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            notify_on_report_ready=True,
            include_attachments=False,
        )

        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        report_pdf_path = "/path/to/report.pdf"

        emails.send_report_ready_notification(
            protocol=self.protocol,
            report_pdf_path=report_pdf_path,
        )

        # Check queue_email was called without attachment
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertIsNone(call_args[1]["attachment_path"])
        self.assertEqual(call_args[1]["context"]["has_attachment"], False)

    @patch("protocols.emails.queue_email")
    def test_send_work_order_notification_single_veterinarian(
        self, mock_queue_email
    ):
        """Test work order notification for single veterinarian."""
        # Create notification preferences
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            include_attachments=True,
        )

        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        work_order_pdf_path = "/path/to/workorder.pdf"

        result = emails.send_work_order_notification(
            work_order=self.work_order,
            work_order_pdf_path=work_order_pdf_path,
        )

        # Check queue_email was called once (one veterinarian)
        self.assertEqual(mock_queue_email.call_count, 1)
        call_args = mock_queue_email.call_args
        self.assertEqual(
            call_args[1]["email_type"], EmailLog.EmailType.WORK_ORDER
        )
        self.assertEqual(call_args[1]["work_order"], self.work_order)
        self.assertEqual(call_args[1]["veterinarian"], self.veterinarian)
        self.assertEqual(call_args[1]["attachment_path"], work_order_pdf_path)

        # Check result is a list with one email log
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_email_log)

    @patch("protocols.emails.queue_email")
    def test_send_work_order_notification_multiple_veterinarians(
        self, mock_queue_email
    ):
        """Test work order notification for multiple veterinarians."""
        # Create second veterinarian
        vet2_user = User.objects.create_user(
            email="vet2@example.com",
            username="vet2",
            password="testpass123",
            role=User.Role.VETERINARIO,
            is_active=True,
        )
        vet2 = Veterinarian.objects.create(
            user=vet2_user,
            first_name="Dr. María",
            last_name="García",
            license_number="VET456",
            phone="987654321",
            email="vet2@example.com",
        )

        # Create second protocol for second veterinarian
        protocol2 = Protocol.objects.create(
            veterinarian=vet2,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.SUBMITTED,
            temporary_code="C 25/002",
            protocol_number="C 25/002",
            submission_date=date.today(),
        )

        # Add second protocol to work order
        self.work_order.protocols.add(protocol2)

        # Create notification preferences for both veterinarians
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
        )
        NotificationPreference.objects.create(
            veterinarian=vet2,
        )

        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        result = emails.send_work_order_notification(self.work_order)

        # Check queue_email was called twice (two veterinarians)
        self.assertEqual(mock_queue_email.call_count, 2)

        # Check result is a list with two email logs
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], mock_email_log)
        self.assertEqual(result[1], mock_email_log)

    @patch("protocols.emails.queue_email")
    def test_send_custom_notification(self, mock_queue_email):
        """Test custom notification email sending."""
        mock_email_log = MagicMock()
        mock_queue_email.return_value = mock_email_log

        context = {"custom": "data"}
        template_name = "emails/custom.html"

        result = emails.send_custom_notification(
            recipient_email="custom@example.com",
            subject="Custom Subject",
            context=context,
            template_name=template_name,
            veterinarian=self.veterinarian,
        )

        # Check queue_email was called with correct parameters
        mock_queue_email.assert_called_once()
        call_args = mock_queue_email.call_args
        self.assertEqual(call_args[1]["email_type"], EmailLog.EmailType.CUSTOM)
        self.assertEqual(call_args[1]["recipient_email"], "custom@example.com")
        self.assertEqual(call_args[1]["subject"], "Custom Subject")
        self.assertEqual(call_args[1]["context"], context)
        self.assertEqual(call_args[1]["template_name"], template_name)
        self.assertEqual(call_args[1]["veterinarian"], self.veterinarian)

        self.assertEqual(result, mock_email_log)

    def test_notification_preference_get_recipient_email_primary(self):
        """Test notification preference returns primary email when no alternative."""
        prefs = NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
        )

        recipient_email = prefs.get_recipient_email()
        self.assertEqual(recipient_email, self.veterinarian.email)

    def test_notification_preference_get_recipient_email_alternative(self):
        """Test notification preference returns alternative email when set."""
        prefs = NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            alternative_email="alt@example.com",
        )

        recipient_email = prefs.get_recipient_email()
        self.assertEqual(recipient_email, "alt@example.com")

    def test_notification_preference_should_send_defaults(self):
        """Test notification preference defaults to enabled."""
        prefs = NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
        )

        # All notification types should be enabled by default
        self.assertTrue(prefs.should_send("sample_reception"))
        self.assertTrue(prefs.should_send("report_ready"))
        self.assertTrue(prefs.should_send("work_order"))

    def test_notification_preference_should_send_disabled(self):
        """Test notification preference can be disabled."""
        prefs = NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            notify_on_reception=False,
            notify_on_report_ready=False,
        )

        # Notification types should be disabled where specified
        self.assertFalse(prefs.should_send("sample_reception"))
        self.assertFalse(prefs.should_send("report_ready"))
        # Work order notifications default to True (not configurable)
        self.assertTrue(prefs.should_send("work_order"))
