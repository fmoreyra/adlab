"""
Tests for custom permission mixins.

This module tests the role-based access control mixins
used in class-based views.
"""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from accounts.mixins import (
    AdminRequiredMixin,
    HistopathologistRequiredMixin,
    ProtocolOwnerOrStaffMixin,
    ReportAccessMixin,
    StaffRequiredMixin,
    VeterinarianProfileRequiredMixin,
    VeterinarianRequiredMixin,
    WorkOrderAccessMixin,
)
from accounts.models import Histopathologist, Veterinarian
from protocols.models import Protocol, Report, WorkOrder

User = get_user_model()


class TestView:
    """Mock view class for testing mixins."""

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs = kwargs


class StaffRequiredMixinTest(TestCase):
    """Test StaffRequiredMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create test users
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            is_staff=False,
        )

    def test_staff_user_passes_test(self):
        """Test that staff user passes the test."""
        request = self.factory.get("/")
        request.user = self.staff_user

        mixin = StaffRequiredMixin()
        mixin.request = request

        self.assertTrue(mixin.test_func())

    def test_non_staff_user_fails_test(self):
        """Test that non-staff user fails the test."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = StaffRequiredMixin()
        mixin.request = request

        self.assertFalse(mixin.test_func())

    def test_permission_denied_message(self):
        """Test permission denied message."""
        mixin = StaffRequiredMixin()
        message = mixin.get_permission_denied_message()
        self.assertIsInstance(message, str)
        self.assertIn("permisos", message)


class VeterinarianRequiredMixinTest(TestCase):
    """Test VeterinarianRequiredMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

    def test_veterinarian_user_passes_test(self):
        """Test that veterinarian user passes the test."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = VeterinarianRequiredMixin()
        mixin.request = request

        self.assertTrue(mixin.test_func())

    def test_non_veterinarian_user_fails_test(self):
        """Test that non-veterinarian user fails the test."""
        request = self.factory.get("/")
        request.user = self.staff_user

        mixin = VeterinarianRequiredMixin()
        mixin.request = request

        self.assertFalse(mixin.test_func())


class HistopathologistRequiredMixinTest(TestCase):
    """Test HistopathologistRequiredMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        self.histopathologist_user = User.objects.create_user(
            email="histo@example.com",
            username="histo",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
        )

        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

    def test_histopathologist_user_passes_test(self):
        """Test that histopathologist user passes the test."""
        request = self.factory.get("/")
        request.user = self.histopathologist_user

        mixin = HistopathologistRequiredMixin()
        mixin.request = request

        self.assertTrue(mixin.test_func())

    def test_non_histopathologist_user_fails_test(self):
        """Test that non-histopathologist user fails the test."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = HistopathologistRequiredMixin()
        mixin.request = request

        self.assertFalse(mixin.test_func())


class AdminRequiredMixinTest(TestCase):
    """Test AdminRequiredMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
        )

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

    def test_admin_user_passes_test(self):
        """Test that admin user passes the test."""
        request = self.factory.get("/")
        request.user = self.admin_user

        mixin = AdminRequiredMixin()
        mixin.request = request

        self.assertTrue(mixin.test_func())

    def test_non_admin_user_fails_test(self):
        """Test that non-admin user fails the test."""
        request = self.factory.get("/")
        request.user = self.staff_user

        mixin = AdminRequiredMixin()
        mixin.request = request

        self.assertFalse(mixin.test_func())


class ProtocolOwnerOrStaffMixinTest(TestCase):
    """Test ProtocolOwnerOrStaffMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create users
        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.other_vet_user = User.objects.create_user(
            email="other@example.com",
            username="other",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

        # Create veterinarian profiles
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

        self.other_veterinarian = Veterinarian.objects.create(
            user=self.other_vet_user,
            first_name="Jane",
            last_name="Smith",
            license_number="MP-67890",
            phone="+54 341 7654321",
            email="other@example.com",
        )

        # Create protocols
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.DRAFT,
        )

        self.other_protocol = Protocol.objects.create(
            veterinarian=self.other_veterinarian,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.DRAFT,
        )

    def test_staff_user_can_access_any_protocol(self):
        """Test that staff user can access any protocol."""
        request = self.factory.get("/")
        request.user = self.staff_user

        mixin = ProtocolOwnerOrStaffMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.protocol.pk}

        self.assertTrue(mixin.test_func())

    def test_owner_can_access_own_protocol(self):
        """Test that veterinarian can access their own protocol."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = ProtocolOwnerOrStaffMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.protocol.pk}

        self.assertTrue(mixin.test_func())

    def test_veterinarian_cannot_access_other_protocol(self):
        """Test that veterinarian cannot access other's protocol."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = ProtocolOwnerOrStaffMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.other_protocol.pk}

        self.assertFalse(mixin.test_func())

    def test_non_veterinarian_cannot_access_protocol(self):
        """Test that non-veterinarian cannot access protocol."""
        staff_user = User.objects.create_user(
            email="staff2@example.com",
            username="staff2",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=False,
        )

        request = self.factory.get("/")
        request.user = staff_user

        mixin = ProtocolOwnerOrStaffMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.protocol.pk}

        self.assertFalse(mixin.test_func())


class VeterinarianProfileRequiredMixinTest(TestCase):
    """Test VeterinarianProfileRequiredMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.incomplete_vet_user = User.objects.create_user(
            email="incomplete@example.com",
            username="incomplete",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        # Create complete veterinarian profile
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

        # Create incomplete veterinarian profile
        self.incomplete_veterinarian = Veterinarian.objects.create(
            user=self.incomplete_vet_user,
            first_name="Jane",
            last_name="",  # Missing last name
            license_number="MP-67890",
            phone="",  # Missing phone
            email="incomplete@example.com",
        )

    def test_complete_profile_passes_test(self):
        """Test that user with complete profile passes the test."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = VeterinarianProfileRequiredMixin()
        mixin.request = request

        self.assertTrue(mixin.test_func())

    def test_incomplete_profile_fails_test(self):
        """Test that user with incomplete profile fails the test."""
        request = self.factory.get("/")
        request.user = self.incomplete_vet_user

        mixin = VeterinarianProfileRequiredMixin()
        mixin.request = request

        self.assertFalse(mixin.test_func())

    def test_non_veterinarian_fails_test(self):
        """Test that non-veterinarian fails the test."""
        staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
        )

        request = self.factory.get("/")
        request.user = staff_user

        mixin = VeterinarianProfileRequiredMixin()
        mixin.request = request

        self.assertFalse(mixin.test_func())


class ReportAccessMixinTest(TestCase):
    """Test ReportAccessMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create users
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.histo_user = User.objects.create_user(
            email="histo@example.com",
            username="histo",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
        )

        # Create profiles
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

        self.histopathologist = Histopathologist.objects.create(
            user=self.histo_user,
            first_name="Dr. Jane",
            last_name="Smith",
            license_number="HP-12345",
            phone="+54 341 7654321",
            email="histo@example.com",
        )

        # Create protocol and report
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.READY,
        )

        self.report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            created_by=self.staff_user,
            status=Report.Status.DRAFT,
        )

    def test_staff_can_access_any_report(self):
        """Test that staff can access any report."""
        request = self.factory.get("/")
        request.user = self.staff_user

        mixin = ReportAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.report.pk}

        self.assertTrue(mixin.test_func())

    def test_veterinarian_can_access_own_report(self):
        """Test that veterinarian can access report for their protocol."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = ReportAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.report.pk}

        self.assertTrue(mixin.test_func())

    def test_histopathologist_can_access_assigned_report(self):
        """Test that histopathologist can access assigned report."""
        request = self.factory.get("/")
        request.user = self.histo_user

        mixin = ReportAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.report.pk}

        self.assertTrue(mixin.test_func())

    def test_histopathologist_can_access_created_report(self):
        """Test that histopathologist can access report they created."""
        # Create another report created by histopathologist
        other_report = Report.objects.create(
            protocol=self.protocol,
            histopathologist=self.histopathologist,
            created_by=self.histo_user,
            status=Report.Status.DRAFT,
        )

        request = self.factory.get("/")
        request.user = self.histo_user

        mixin = ReportAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": other_report.pk}

        self.assertTrue(mixin.test_func())


class WorkOrderAccessMixinTest(TestCase):
    """Test WorkOrderAccessMixin functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create users
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )

        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        self.other_vet_user = User.objects.create_user(
            email="other@example.com",
            username="other",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        # Create veterinarian profiles
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

        self.other_veterinarian = Veterinarian.objects.create(
            user=self.other_vet_user,
            first_name="Jane",
            last_name="Smith",
            license_number="MP-67890",
            phone="+54 341 7654321",
            email="other@example.com",
        )

        # Create work orders
        self.work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            created_by=self.staff_user,
            status=WorkOrder.Status.DRAFT,
        )

        self.other_work_order = WorkOrder.objects.create(
            veterinarian=self.other_veterinarian,
            created_by=self.staff_user,
            status=WorkOrder.Status.DRAFT,
        )

    def test_staff_can_access_any_work_order(self):
        """Test that staff can access any work order."""
        request = self.factory.get("/")
        request.user = self.staff_user

        mixin = WorkOrderAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.work_order.pk}

        self.assertTrue(mixin.test_func())

    def test_veterinarian_can_access_own_work_order(self):
        """Test that veterinarian can access their own work order."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = WorkOrderAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.work_order.pk}

        self.assertTrue(mixin.test_func())

    def test_veterinarian_cannot_access_other_work_order(self):
        """Test that veterinarian cannot access other's work order."""
        request = self.factory.get("/")
        request.user = self.vet_user

        mixin = WorkOrderAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.other_work_order.pk}

        self.assertFalse(mixin.test_func())

    def test_non_veterinarian_cannot_access_work_order(self):
        """Test that non-veterinarian cannot access work order."""
        staff_user = User.objects.create_user(
            email="staff2@example.com",
            username="staff2",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=False,
        )

        request = self.factory.get("/")
        request.user = staff_user

        mixin = WorkOrderAccessMixin()
        mixin.request = request
        mixin.kwargs = {"pk": self.work_order.pk}

        self.assertFalse(mixin.test_func())
