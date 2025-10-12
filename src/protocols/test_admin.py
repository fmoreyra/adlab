"""
Comprehensive Tests for Protocols Admin Interface - Phase 6.

This module tests:
1. Admin interface functionality
2. Admin actions (mark as received, processing, ready)
3. Admin permissions and access control
4. Admin form validation and data handling
5. Admin list displays and filters
6. Admin search functionality
7. Admin inline forms and relationships
"""

from datetime import date
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Histopathologist, Veterinarian
from protocols.admin import CytologySampleAdmin, ProtocolAdmin
from protocols.models import (
    CytologySample,
    EmailLog,
    HistopathologySample,
    NotificationPreference,
    Protocol,
    ProtocolCounter,
    WorkOrder,
)

User = get_user_model()


class ProtocolsAdminTest(TestCase):
    """Comprehensive tests for protocols admin interface."""

    def setUp(self):
        """Set up test data for admin tests."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="testpass123",
        )

        # Create staff user
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

        # Create veterinarian
        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

        # Create histopathologist
        self.histo_user = User.objects.create_user(
            email="histo@example.com",
            username="histo",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
            email_verified=True,
            is_staff=True,
        )

        self.histopathologist = Histopathologist.objects.create(
            user=self.histo_user,
            first_name="Dr. Jane",
            last_name="Smith",
            license_number="HP-67890",
            position="Profesor Titular",
            specialty="Patología Veterinaria",
        )

        # Create test protocols
        self.cytology_protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.SUBMITTED,
            temporary_code="C 25/001",
            protocol_number="C 25/001",
            submission_date=date.today(),
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Tumor mamario",
        )

        self.histopathology_protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.SUBMITTED,
            temporary_code="HP 25/002",
            protocol_number="HP 25/002",
            submission_date=date.today(),
            species="Felino",
            animal_identification="Luna",
            presumptive_diagnosis="Lesión cutánea",
        )

        # Create samples
        self.cytology_sample = CytologySample.objects.create(
            protocol=self.cytology_protocol,
            veterinarian=self.veterinarian,
            technique_used="PAAF",
            sampling_site="Mama",
            number_of_slides=3,
            observations="Muestra de buena calidad",
        )

        self.histopathology_sample = HistopathologySample.objects.create(
            protocol=self.histopathology_protocol,
            veterinarian=self.veterinarian,
            preservation="Formol 10%",
            observations="Tejido bien preservado",
            number_of_containers=2,
        )

        # Create work order
        self.work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            advance_payment=Decimal("100.00"),
            billing_name="John Doe",
            cuit_cuil="20-12345678-9",
            iva_condition="responsable_inscripto",
            observations="Test work order",
            order_number="WO-2025-001",
        )

        # Create counters
        self.cytology_counter = ProtocolCounter.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            year=2025,
            last_number=0,
        )

        self.histopathology_counter = ProtocolCounter.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            year=2025,
            last_number=0,
        )

    # ============================================================================
    # ADMIN ACCESS TESTS
    # ============================================================================

    def test_admin_access_requires_login(self):
        """Test that admin interface requires login."""
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/admin/login/?next=/admin/")

    def test_admin_access_requires_staff_permission(self):
        """Test that admin interface requires staff permission."""
        # Login as non-staff user
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/admin/login/?next=/admin/")

    def test_admin_access_with_staff_permission(self):
        """Test that staff users can access admin interface."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_admin_access_with_superuser(self):
        """Test that superusers can access admin interface."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    # ============================================================================
    # PROTOCOL ADMIN TESTS
    # ============================================================================

    def test_protocol_admin_list_view(self):
        """Test protocol admin list view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/protocol/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")
        self.assertContains(response, "HP 25/002")

    def test_protocol_admin_detail_view(self):
        """Test protocol admin detail view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            f"/admin/protocols/protocol/{self.cytology_protocol.id}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")

    def test_protocol_admin_search(self):
        """Test protocol admin search functionality."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/protocol/?q=Max")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")
        self.assertNotContains(response, "HP 25/002")

    def test_protocol_admin_filter_by_status(self):
        """Test protocol admin filtering by status."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            "/admin/protocols/protocol/?status=submitted"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")
        self.assertContains(response, "HP 25/002")

    def test_protocol_admin_filter_by_analysis_type(self):
        """Test protocol admin filtering by analysis type."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            "/admin/protocols/protocol/?analysis_type=cytology"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")
        self.assertNotContains(response, "HP 25/002")

    def test_protocol_admin_mark_as_received_action(self):
        """Test protocol admin mark as received action."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Select protocols for action
        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_received",
                "_selected_action": [str(self.cytology_protocol.id)],
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check that protocol was marked as received
        self.cytology_protocol.refresh_from_db()
        self.assertEqual(
            self.cytology_protocol.status, Protocol.Status.RECEIVED
        )

    def test_protocol_admin_mark_as_processing_action(self):
        """Test protocol admin mark as processing action."""
        # First mark as received
        self.cytology_protocol.status = Protocol.Status.RECEIVED
        self.cytology_protocol.save()

        self.client.login(email="admin@example.com", password="testpass123")

        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_processing",
                "_selected_action": [str(self.cytology_protocol.id)],
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check that protocol was marked as processing
        self.cytology_protocol.refresh_from_db()
        self.assertEqual(
            self.cytology_protocol.status, Protocol.Status.PROCESSING
        )

    def test_protocol_admin_mark_as_ready_action(self):
        """Test protocol admin mark as ready action."""
        # First mark as processing
        self.cytology_protocol.status = Protocol.Status.PROCESSING
        self.cytology_protocol.save()

        self.client.login(email="admin@example.com", password="testpass123")

        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_ready",
                "_selected_action": [str(self.cytology_protocol.id)],
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check that protocol was marked as ready
        self.cytology_protocol.refresh_from_db()
        self.assertEqual(self.cytology_protocol.status, Protocol.Status.READY)

    def test_protocol_admin_get_protocol_code_display(self):
        """Test protocol admin protocol code display method."""
        admin = ProtocolAdmin(Protocol, AdminSite())

        # Test with protocol number
        code = admin.get_protocol_code(self.cytology_protocol)
        self.assertIn("C 25/001", code)

        # Test with temporary code only
        self.cytology_protocol.protocol_number = None
        self.cytology_protocol.save()
        code = admin.get_protocol_code(self.cytology_protocol)
        self.assertIn("C 25/001", code)

    def test_protocol_admin_get_editable_status_display(self):
        """Test protocol admin editable status display method."""
        admin = ProtocolAdmin(Protocol, AdminSite())

        # Test editable protocol
        status = admin.get_editable_status(self.cytology_protocol)
        self.assertIn("Editable", status)

        # Test non-editable protocol
        self.cytology_protocol.status = Protocol.Status.RECEIVED
        self.cytology_protocol.save()
        status = admin.get_editable_status(self.cytology_protocol)
        self.assertIn("Locked", status)

    # ============================================================================
    # CYTOLOGY SAMPLE ADMIN TESTS
    # ============================================================================

    def test_cytology_sample_admin_list_view(self):
        """Test cytology sample admin list view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/cytologysample/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")

    def test_cytology_sample_admin_detail_view(self):
        """Test cytology sample admin detail view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            f"/admin/protocols/cytologysample/{self.cytology_sample.id}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PAAF")

    def test_cytology_sample_admin_search(self):
        """Test cytology sample admin search functionality."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/cytologysample/?q=Mama")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "C 25/001")

    def test_cytology_sample_admin_get_protocol_code(self):
        """Test cytology sample admin protocol code display method."""
        admin = CytologySampleAdmin(CytologySample, AdminSite())
        code = admin.get_protocol_code(self.cytology_sample)
        self.assertEqual(code, "C 25/001")

    # ============================================================================
    # HISTOPATHOLOGY SAMPLE ADMIN TESTS
    # ============================================================================

    def test_histopathology_sample_admin_list_view(self):
        """Test histopathology sample admin list view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/histopathologysample/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HP 25/002")

    def test_histopathology_sample_admin_detail_view(self):
        """Test histopathology sample admin detail view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            f"/admin/protocols/histopathologysample/{self.histopathology_sample.id}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formol 10%")

    def test_histopathology_sample_admin_search(self):
        """Test histopathology sample admin search functionality."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            "/admin/protocols/histopathologysample/?q=Formol"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HP 25/002")

    # ============================================================================
    # WORK ORDER ADMIN TESTS
    # ============================================================================

    def test_work_order_admin_list_view(self):
        """Test work order admin list view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/workorder/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WO-2025-001")

    def test_work_order_admin_detail_view(self):
        """Test work order admin detail view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(
            f"/admin/protocols/workorder/{self.work_order.id}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_work_order_admin_search(self):
        """Test work order admin search functionality."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/workorder/?q=John")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WO-2025-001")

    # ============================================================================
    # PROTOCOL COUNTER ADMIN TESTS
    # ============================================================================

    def test_protocol_counter_admin_list_view(self):
        """Test protocol counter admin list view."""
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/protocolcounter/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cytology")
        self.assertContains(response, "Histopathology")

    def test_protocol_counter_admin_get_formatted_display(self):
        """Test protocol counter admin formatted display method."""
        from protocols.admin import ProtocolCounterAdmin

        admin = ProtocolCounterAdmin(ProtocolCounter, AdminSite())

        display = admin.get_formatted_display(self.cytology_counter)
        self.assertIn("CT 25/001", display)

    def test_protocol_counter_admin_delete_permission(self):
        """Test protocol counter admin delete permission."""
        from protocols.admin import ProtocolCounterAdmin

        admin = ProtocolCounterAdmin(ProtocolCounter, AdminSite())

        # Test with superuser
        self.assertTrue(admin.has_delete_permission(self.admin_user))

        # Test with staff user
        self.assertFalse(admin.has_delete_permission(self.staff_user))

    # ============================================================================
    # EMAIL LOG ADMIN TESTS
    # ============================================================================

    def test_email_log_admin_list_view(self):
        """Test email log admin list view."""
        # Create an email log
        EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="test@example.com",
            recipient=self.veterinarian,
            subject="Test Email",
            protocol=self.cytology_protocol,
            status=EmailLog.Status.SENT,
        )

        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/emaillog/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Email")

    def test_email_log_admin_search(self):
        """Test email log admin search functionality."""
        # Create an email log
        EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="test@example.com",
            recipient=self.veterinarian,
            subject="Test Email",
            protocol=self.cytology_protocol,
            status=EmailLog.Status.SENT,
        )

        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/emaillog/?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Email")

    # ============================================================================
    # NOTIFICATION PREFERENCE ADMIN TESTS
    # ============================================================================

    def test_notification_preference_admin_list_view(self):
        """Test notification preference admin list view."""
        # Create notification preference
        NotificationPreference.objects.create(
            veterinarian=self.veterinarian,
            notify_on_reception=True,
            notify_on_processing=False,
            notify_on_report_ready=True,
        )

        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get("/admin/protocols/notificationpreference/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    # ============================================================================
    # ADMIN PERMISSION TESTS
    # ============================================================================

    def test_admin_permissions_staff_user(self):
        """Test admin permissions for staff users."""
        self.client.login(email="staff@example.com", password="testpass123")

        # Staff users should be able to view but not modify certain models
        response = self.client.get("/admin/protocols/protocol/")
        self.assertEqual(response.status_code, 200)

        # Test if staff can access admin actions
        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_received",
                "_selected_action": [str(self.cytology_protocol.id)],
            },
        )
        # Should work for staff users
        self.assertEqual(response.status_code, 302)

    def test_admin_permissions_superuser(self):
        """Test admin permissions for superusers."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Superusers should have full access
        response = self.client.get("/admin/protocols/protocol/")
        self.assertEqual(response.status_code, 200)

        # Test admin actions
        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_received",
                "_selected_action": [str(self.cytology_protocol.id)],
            },
        )
        self.assertEqual(response.status_code, 302)

    # ============================================================================
    # ADMIN FORM VALIDATION TESTS
    # ============================================================================

    def test_protocol_admin_form_validation(self):
        """Test protocol admin form validation."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Test invalid form data
        response = self.client.post(
            f"/admin/protocols/protocol/{self.cytology_protocol.id}/change/",
            {
                "veterinarian": self.veterinarian.id,
                "analysis_type": "invalid_type",
                "status": "invalid_status",
                "submission_date": "invalid_date",
            },
        )
        # Should return form with errors
        self.assertEqual(response.status_code, 200)

    def test_cytology_sample_admin_form_validation(self):
        """Test cytology sample admin form validation."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Test invalid form data
        response = self.client.post(
            f"/admin/protocols/cytologysample/{self.cytology_sample.id}/change/",
            {
                "protocol": self.cytology_protocol.id,
                "veterinarian": self.veterinarian.id,
                "number_of_slides": -1,  # Invalid negative number
            },
        )
        # Should return form with errors
        self.assertEqual(response.status_code, 200)

    # ============================================================================
    # ADMIN INLINE TESTS
    # ============================================================================

    def test_protocol_admin_inlines_cytology(self):
        """Test protocol admin inlines for cytology protocol."""
        admin = ProtocolAdmin(Protocol, AdminSite())
        inlines = admin.get_inlines(None, self.cytology_protocol)

        # Should include CytologySampleInline for cytology protocols
        self.assertTrue(len(inlines) > 0)

    def test_protocol_admin_inlines_histopathology(self):
        """Test protocol admin inlines for histopathology protocol."""
        admin = ProtocolAdmin(Protocol, AdminSite())
        inlines = admin.get_inlines(None, self.histopathology_protocol)

        # Should include HistopathologySampleInline for histopathology protocols
        self.assertTrue(len(inlines) > 0)

    # ============================================================================
    # ADMIN BULK OPERATIONS TESTS
    # ============================================================================

    def test_protocol_admin_bulk_mark_as_received(self):
        """Test bulk mark as received operation."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Select multiple protocols
        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_received",
                "_selected_action": [
                    str(self.cytology_protocol.id),
                    str(self.histopathology_protocol.id),
                ],
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check that both protocols were marked as received
        self.cytology_protocol.refresh_from_db()
        self.histopathology_protocol.refresh_from_db()
        self.assertEqual(
            self.cytology_protocol.status, Protocol.Status.RECEIVED
        )
        self.assertEqual(
            self.histopathology_protocol.status, Protocol.Status.RECEIVED
        )

    def test_protocol_admin_bulk_mark_as_processing(self):
        """Test bulk mark as processing operation."""
        # First mark as received
        self.cytology_protocol.status = Protocol.Status.RECEIVED
        self.histopathology_protocol.status = Protocol.Status.RECEIVED
        self.cytology_protocol.save()
        self.histopathology_protocol.save()

        self.client.login(email="admin@example.com", password="testpass123")

        # Select multiple protocols
        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "mark_as_processing",
                "_selected_action": [
                    str(self.cytology_protocol.id),
                    str(self.histopathology_protocol.id),
                ],
            },
        )
        self.assertEqual(response.status_code, 302)

        # Check that both protocols were marked as processing
        self.cytology_protocol.refresh_from_db()
        self.histopathology_protocol.refresh_from_db()
        self.assertEqual(
            self.cytology_protocol.status, Protocol.Status.PROCESSING
        )
        self.assertEqual(
            self.histopathology_protocol.status, Protocol.Status.PROCESSING
        )

    # ============================================================================
    # ADMIN ERROR HANDLING TESTS
    # ============================================================================

    def test_admin_handles_nonexistent_object(self):
        """Test admin handles nonexistent object gracefully."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Try to access nonexistent protocol
        response = self.client.get("/admin/protocols/protocol/99999/change/")
        self.assertEqual(response.status_code, 404)

    def test_admin_handles_invalid_action(self):
        """Test admin handles invalid action gracefully."""
        self.client.login(email="admin@example.com", password="testpass123")

        # Try invalid action
        response = self.client.post(
            "/admin/protocols/protocol/",
            {
                "action": "invalid_action",
                "_selected_action": [str(self.cytology_protocol.id)],
            },
        )
        # Should redirect back to list view
        self.assertEqual(response.status_code, 302)

    # ============================================================================
    # ADMIN PERFORMANCE TESTS
    # ============================================================================

    def test_admin_list_view_performance(self):
        """Test admin list view performance with multiple objects."""
        # Create multiple protocols
        for i in range(10):
            Protocol.objects.create(
                veterinarian=self.veterinarian,
                analysis_type=Protocol.AnalysisType.CYTOLOGY,
                status=Protocol.Status.SUBMITTED,
                temporary_code=f"C 25/{i:03d}",
                submission_date=date.today(),
                species="Canino",
                animal_identification=f"Dog {i}",
                presumptive_diagnosis="Test diagnosis",
            )

        self.client.login(email="admin@example.com", password="testpass123")

        # Test list view performance
        response = self.client.get("/admin/protocols/protocol/")
        self.assertEqual(response.status_code, 200)
        # Should contain all protocols
        self.assertContains(response, "C 25/000")
        self.assertContains(response, "C 25/009")

    def test_admin_search_performance(self):
        """Test admin search performance."""
        # Create multiple protocols with searchable content
        for i in range(10):
            Protocol.objects.create(
                veterinarian=self.veterinarian,
                analysis_type=Protocol.AnalysisType.CYTOLOGY,
                status=Protocol.Status.SUBMITTED,
                temporary_code=f"C 25/{i:03d}",
                submission_date=date.today(),
                species="Canino",
                animal_identification=f"Searchable Dog {i}",
                presumptive_diagnosis="Test diagnosis",
            )

        self.client.login(email="admin@example.com", password="testpass123")

        # Test search performance
        response = self.client.get("/admin/protocols/protocol/?q=Searchable")
        self.assertEqual(response.status_code, 200)
        # Should contain all matching protocols
        for i in range(10):
            self.assertContains(response, f"Searchable Dog {i}")
