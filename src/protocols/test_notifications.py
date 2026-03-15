"""
Tests for in-app notifications (Step 21).

Covers API endpoints, NotificationService, and integration points.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Histopathologist, LaboratoryStaff, Veterinarian
from protocols.models import (
    CytologySample,
    HistopathologySample,
    InAppNotification,
    Protocol,
    Report,
    WorkOrder,
    WorkOrderService,
)
from protocols.services.notification_service import NotificationService

User = get_user_model()


class NotificationAPITestCase(TestCase):
    """Tests for notification API endpoints."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        Veterinarian.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_unread_count_empty(self):
        """Unread count returns 0 when no notifications."""
        url = reverse("pages_api:notifications:unread_count")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)

    def test_unread_count_with_notifications(self):
        """Unread count returns correct count."""
        InAppNotification.objects.create(
            recipient=self.user,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test",
            body="Body",
            is_read=False,
        )
        InAppNotification.objects.create(
            recipient=self.user,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test 2",
            body="Body 2",
            is_read=True,
        )
        url = reverse("pages_api:notifications:unread_count")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_list_notifications(self):
        """List returns user notifications."""
        n = InAppNotification.objects.create(
            recipient=self.user,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test",
            body="Body",
            is_read=False,
        )
        url = reverse("pages_api:notifications:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["notifications"]), 1)
        self.assertEqual(data["notifications"][0]["title"], "Test")
        self.assertEqual(data["notifications"][0]["id"], n.id)

    def test_mark_read(self):
        """Mark single notification as read."""
        n = InAppNotification.objects.create(
            recipient=self.user,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test",
            body="Body",
            is_read=False,
        )
        url = reverse("pages_api:notifications:mark_read", kwargs={"pk": n.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_read_other_user_forbidden(self):
        """Cannot mark another user's notification as read."""
        other = User.objects.create_user(
            email="other@example.com",
            username="other",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        n = InAppNotification.objects.create(
            recipient=other,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test",
            body="Body",
            is_read=False,
        )
        url = reverse("pages_api:notifications:mark_read", kwargs={"pk": n.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        n.refresh_from_db()
        self.assertFalse(n.is_read)

    def test_mark_all_read(self):
        """Mark all notifications as read."""
        InAppNotification.objects.create(
            recipient=self.user,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test 1",
            is_read=False,
        )
        InAppNotification.objects.create(
            recipient=self.user,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Test 2",
            is_read=False,
        )
        url = reverse("pages_api:notifications:read_all")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        unread = InAppNotification.objects.filter(
            recipient=self.user, is_read=False
        ).count()
        self.assertEqual(unread, 0)

    def test_list_requires_login(self):
        """API requires authentication."""
        self.client.logout()
        url = reverse("pages_api:notifications:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class NotificationServiceTestCase(TestCase):
    """Tests for NotificationService."""

    def setUp(self):
        """Set up test user and veterinarian."""
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

    def test_create_test_notification(self):
        """Create test notification."""
        svc = NotificationService()
        n = svc.create_test_notification(self.user, "Mensaje de prueba")
        self.assertIsNotNone(n.id)
        self.assertEqual(n.recipient, self.user)
        self.assertEqual(n.title, "Notificación de prueba")
        self.assertIn("Mensaje de prueba", n.body)

    def test_create_for_protocol_submitted(self):
        """Create notification when protocol submitted."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        protocol.generate_temporary_code()
        protocol.submit()
        svc = NotificationService()
        n = svc.create_for_protocol_submitted(protocol)
        self.assertEqual(n.recipient, self.user)
        self.assertIn(protocol.temporary_code, n.title)


class NotificationViewIntegrationTestCase(TestCase):
    """
    Integration tests: verify views create InAppNotification when triggered.
    """

    def setUp(self):
        """Set up users, veterinarian, and base protocol."""
        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
            is_staff=True,
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
            is_staff=True,
        )
        self.histo_user = User.objects.create_user(
            email="histo@example.com",
            username="histo",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
            email_verified=True,
            is_staff=True,
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )
        LaboratoryStaff.objects.create(
            user=self.staff_user,
            first_name="Staff",
            last_name="Member",
            license_number="LAB-001",
            can_create_reports=True,
            is_active=True,
        )
        Histopathologist.objects.create(
            user=self.histo_user,
            first_name="Histo",
            last_name="Path",
            license_number="HP-001",
            is_active=True,
        )
        self.client = Client()

    @patch(
        "protocols.services.email_service.EmailNotificationService.send_submission_confirmation_email"
    )
    def test_protocol_submit_view_creates_notification(self, mock_send_email):
        """ProtocolSubmitView creates InAppNotification type SUBMITTED."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        self.client.force_login(self.vet_user)

        self.client.post(
            reverse("protocols:protocol_submit", kwargs={"pk": protocol.pk})
        )

        notifications = InAppNotification.objects.filter(
            recipient=self.vet_user,
            notification_type=InAppNotification.NotificationType.SUBMITTED,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn("enviado", notifications.first().title.lower())

    @patch(
        "protocols.services.email_service.EmailNotificationService.send_reception_email"
    )
    @patch(
        "protocols.services.email_service.EmailNotificationService.send_rejection_email",
        new=lambda s, p: None,
    )
    def test_reception_confirm_view_creates_reception_notification(
        self, mock_send_reception
    ):
        """ReceptionConfirmView (received) creates InAppNotification RECEPTION."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        CytologySample.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            technique_used="PAAF",
            sampling_site="Linfonodo",
            number_of_slides=2,
        )
        protocol.submit()
        self.client.force_login(self.staff_user)

        form_data = {
            "sample_condition": Protocol.SampleCondition.OPTIMAL,
            "reception_notes": "OK",
            "discrepancies": "",
            "number_slides_received": 2,
        }
        self.client.post(
            reverse(
                "protocols:reception_confirm",
                kwargs={"pk": protocol.pk},
            ),
            data=form_data,
        )

        notifications = InAppNotification.objects.filter(
            recipient=self.vet_user,
            notification_type=InAppNotification.NotificationType.RECEPTION,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn("recibida", notifications.first().title.lower())

    @patch(
        "protocols.services.email_service.EmailNotificationService.send_rejection_email"
    )
    def test_reception_confirm_view_creates_rejection_notification(
        self, mock_send_rejection
    ):
        """ReceptionConfirmView (rejected) creates InAppNotification REJECTION."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        CytologySample.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            technique_used="PAAF",
            sampling_site="Linfonodo",
            number_of_slides=2,
        )
        protocol.submit()
        self.client.force_login(self.staff_user)

        form_data = {
            "sample_condition": Protocol.SampleCondition.REJECTED,
            "reception_notes": "Poor quality",
            "discrepancies": "",
            "number_slides_received": 0,
        }
        self.client.post(
            reverse(
                "protocols:reception_confirm",
                kwargs={"pk": protocol.pk},
            ),
            data=form_data,
        )

        notifications = InAppNotification.objects.filter(
            recipient=self.vet_user,
            notification_type=InAppNotification.NotificationType.REJECTION,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn("rechazada", notifications.first().title.lower())

    @patch(
        "protocols.services.email_service.EmailNotificationService.send_reception_email"
    )
    @patch(
        "protocols.services.email_service.EmailNotificationService.send_discrepancy_alert_email"
    )
    def test_reception_confirm_view_creates_discrepancy_notification(
        self, mock_discrepancy, mock_reception
    ):
        """ReceptionConfirmView (with discrepancies) creates DISCREPANCY notification."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        CytologySample.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
            technique_used="PAAF",
            sampling_site="Linfonodo",
            number_of_slides=2,
        )
        protocol.submit()
        self.client.force_login(self.staff_user)

        form_data = {
            "sample_condition": Protocol.SampleCondition.SUBOPTIMAL,
            "reception_notes": "Issues found",
            "discrepancies": "Falta etiqueta",
            "number_slides_received": 1,
        }
        self.client.post(
            reverse(
                "protocols:reception_confirm",
                kwargs={"pk": protocol.pk},
            ),
            data=form_data,
        )

        discrepancy_notifs = InAppNotification.objects.filter(
            recipient=self.vet_user,
            notification_type=InAppNotification.NotificationType.DISCREPANCY,
        )
        self.assertEqual(discrepancy_notifs.count(), 1)
        self.assertIn("Discrepancias", discrepancy_notifs.first().title)

    @patch(
        "protocols.services.email_service.EmailNotificationService.send_report_ready_notification"
    )
    @patch("builtins.open", create=True)
    @patch("os.path.exists")
    def test_report_send_view_creates_notification(
        self, mock_exists, mock_open, mock_send_report
    ):
        """ReportSendView creates InAppNotification REPORT_READY."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value = b"fake pdf"

        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        protocol.submit()
        protocol.receive(
            received_by=self.staff_user,
            sample_condition=Protocol.SampleCondition.OPTIMAL,
        )
        HistopathologySample.objects.create(
            protocol=protocol,
            veterinarian=self.veterinarian,
        )
        report = Report.objects.create(
            protocol=protocol,
            histopathologist=Histopathologist.objects.get(
                user=self.histo_user
            ),
            veterinarian=self.veterinarian,
            macroscopic_observations="OK",
            microscopic_observations="OK",
            diagnosis="Test",
            status=Report.Status.FINALIZED,
            pdf_path="/tmp/test.pdf",
        )
        self.client.force_login(self.histo_user)

        form_data = {
            "recipient_email": "vet@example.com",
            "subject": "Informe",
            "message": "Listo",
        }
        self.client.post(
            reverse(
                "protocols:report_send",
                kwargs={"pk": report.pk},
            ),
            data=form_data,
        )

        notifications = InAppNotification.objects.filter(
            recipient=self.vet_user,
            notification_type=InAppNotification.NotificationType.REPORT_READY,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn("Informe", notifications.first().title)

    @patch("protocols.views_workorder.send_work_order_notification")
    def test_workorder_send_view_creates_notification(self, mock_send_wo):
        """WorkOrderSendView creates InAppNotification WORK_ORDER."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
        )
        protocol.submit()
        protocol.receive(
            received_by=self.staff_user,
            sample_condition=Protocol.SampleCondition.OPTIMAL,
        )
        protocol.status = Protocol.Status.READY
        protocol.save()

        work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            created_by=self.staff_user,
            status=WorkOrder.Status.DRAFT,
        )
        protocol.work_order = work_order
        protocol.save()
        WorkOrderService.objects.create(
            work_order=work_order,
            protocol=protocol,
            description="Citologia",
            service_type="citologia",
            unit_price=Decimal("150.00"),
        )

        self.client.force_login(self.staff_user)
        self.client.post(
            reverse(
                "protocols:workorder_send",
                kwargs={"pk": work_order.pk},
            ),
        )

        notifications = InAppNotification.objects.filter(
            recipient=self.vet_user,
            notification_type=InAppNotification.NotificationType.WORK_ORDER,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn("Orden de trabajo", notifications.first().title)
