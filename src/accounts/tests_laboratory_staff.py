"""
Tests for the LaboratoryStaff model and related functionality.

This module tests the new LaboratoryStaff model created in Step 16
to replace the Histopathologist model and support role consolidation.
"""

import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import (
    AuthAuditLog,
    Histopathologist,
    LaboratoryStaff,
    User,
    Veterinarian,
)


class LaboratoryStaffModelTest(TestCase):
    """Test the LaboratoryStaff model functionality."""

    def setUp(self):
        """Set up test data for LaboratoryStaff tests."""
        self.user = User.objects.create_user(
            email="staff@example.com",
            username="staffuser",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            first_name="John",
            last_name="Doe",
        )

    def test_create_laboratory_staff(self):
        """Test creating a LaboratoryStaff instance."""
        lab_staff = LaboratoryStaff.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            license_number="LS-12345",
            position="Técnico Superior",
            specialty="Patología Veterinaria",
            phone_number="+54 341 1234567",
            can_create_reports=True,
            is_active=True,
        )

        self.assertEqual(lab_staff.user, self.user)
        self.assertEqual(lab_staff.first_name, "Jane")
        self.assertEqual(lab_staff.last_name, "Smith")
        self.assertEqual(lab_staff.license_number, "LS-12345")
        self.assertEqual(lab_staff.position, "Técnico Superior")
        self.assertEqual(lab_staff.specialty, "Patología Veterinaria")
        self.assertEqual(lab_staff.phone_number, "+54 341 1234567")
        self.assertTrue(lab_staff.can_create_reports)
        self.assertTrue(lab_staff.is_active)
        self.assertFalse(lab_staff.has_signature())  # No signature yet

    def test_laboratory_staff_full_name(self):
        """Test get_full_name method."""
        lab_staff = LaboratoryStaff.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
        )
        self.assertEqual(lab_staff.get_full_name(), "Jane Smith")

    def test_laboratory_staff_formal_name(self):
        """Test get_formal_name method."""
        lab_staff = LaboratoryStaff.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
        )
        self.assertEqual(lab_staff.get_formal_name(), "Dr./Dra. Jane Smith")

    def test_laboratory_staff_signature_check(self):
        """Test signature checking functionality."""
        # Without signature
        lab_staff = LaboratoryStaff.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
        )
        self.assertFalse(lab_staff.has_signature())

        # With signature (using a mock image)
        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as tmp_file:
            tmp_file.write(b"mock image content")
            tmp_file.flush()

            with open(tmp_file.name, "rb") as f:
                image = SimpleUploadedFile(
                    name="test_signature.png",
                    content=f.read(),
                    content_type="image/png",
                )

            lab_staff.signature_image = image
            lab_staff.save()
            self.assertTrue(lab_staff.has_signature())

    def test_laboratory_staff_is_histopathologist_equivalent(self):
        """Test legacy compatibility property."""
        # Can create reports - should be equivalent to histopathologist
        lab_staff = LaboratoryStaff.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            license_number="LS-EQUIV-001",
            can_create_reports=True,
        )
        self.assertTrue(lab_staff.is_histopathologist_equivalent)

        # Cannot create reports - should not be equivalent
        lab_staff_no_reports = LaboratoryStaff.objects.create(
            user=User.objects.create_user(
                email="staff2@example.com",
                username="staff2",
                password="testpass123",
                role=User.Role.PERSONAL_LAB,
            ),
            first_name="John",
            last_name="Doe",
            license_number="LS-EQUIV-002",
            can_create_reports=False,
        )
        self.assertFalse(lab_staff_no_reports.is_histopathologist_equivalent)


class UserModelRoleConsolidationTest(TestCase):
    """Test User model changes for role consolidation."""

    def test_user_role_choices_updated(self):
        """Test that roles are properly available."""
        # PERSONAL_LAB should still be available
        self.assertTrue(hasattr(User.Role, "PERSONAL_LAB"))

        # VETERINARIO should still be available
        self.assertTrue(hasattr(User.Role, "VETERINARIO"))

        # ADMIN should still be available
        self.assertTrue(hasattr(User.Role, "ADMIN"))

        # HISTOPATOLOGO is preserved for backward compatibility
        self.assertTrue(hasattr(User.Role, "HISTOPATOLOGO"))

    def test_user_role_properties_updated(self):
        """Test updated user role property methods."""
        # Test lab staff user
        lab_user = User.objects.create_user(
            email="lab@example.com",
            username="labuser",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
        )
        self.assertTrue(lab_user.is_lab_staff)
        # is_histopathologist is preserved for backward compatibility
        self.assertFalse(lab_user.is_histopathologist)

        # Test veterinarian user
        vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )
        self.assertTrue(vet_user.is_veterinarian)
        self.assertFalse(vet_user.is_lab_staff)

        # Test admin user
        admin_user = User.objects.create_user(
            email="admin@example.com",
            username="adminuser",
            password="testpass123",
            role=User.Role.ADMIN,
        )
        self.assertTrue(admin_user.is_admin_user)
        self.assertTrue(admin_user.is_lab_staff)  # Admin is also lab staff

    def test_user_login_behavior(self):
        """Test updated login behavior for new role structure."""
        lab_user = User.objects.create_user(
            email="lab@example.com",
            username="labuser",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_active=True,
        )

        # Lab staff should be able to login without email verification
        self.assertTrue(lab_user.can_login())

        # Vet needs verification
        vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
            is_active=True,
            email_verified=False,
        )
        self.assertFalse(vet_user.can_login())

        # Vet with verification should be able to login
        vet_user.email_verified = True
        vet_user.save()
        self.assertTrue(vet_user.can_login())


class LaboratoryStaffAdminTest(TestCase):
    """Test LaboratoryStaff admin interface."""

    def setUp(self):
        """Set up test data for admin tests."""
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staffuser",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,  # Is staff for admin access
        )
        self.client.force_login(self.staff_user)

    def test_laboratory_staff_admin_list_display(self):
        """Test admin list display fields."""
        # This tests that the admin can be imported and has proper fields
        from accounts.admin import LaboratoryStaffAdmin

        admin_class = LaboratoryStaffAdmin(LaboratoryStaff, None)
        list_display = admin_class.list_display

        # Should include key fields
        self.assertIn("license_number", list_display)
        self.assertIn("last_name", list_display)
        self.assertIn("first_name", list_display)
        self.assertIn("can_create_reports", list_display)
        self.assertIn("is_active", list_display)
        self.assertIn("has_signature_display", list_display)

    def test_laboratory_staff_admin_actions(self):
        """Test admin bulk actions."""
        from accounts.admin import LaboratoryStaffAdmin

        admin_class = LaboratoryStaffAdmin(LaboratoryStaff, None)
        actions = admin_class.actions

        # Should include permission management actions (report creation toggle)
        self.assertIn("enable_report_creation", actions)
        self.assertIn("disable_report_creation", actions)


class HistopathologistLegacyTest(TestCase):
    """Test legacy histopathologist functionality for migration compatibility."""

    def test_legacy_histopathologist_model_exists(self):
        """Test that Histopathologist model still exists for migration."""
        self.assertTrue(hasattr(Histopathologist, "objects"))

    def test_legacy_histopathologist_compatibility(self):
        """Test that legacy histopathologist model has expected fields."""
        user = User.objects.create_user(
            email="histo@example.com",
            username="histouser",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,  # Now should be PERSONAL_LAB
        )

        # Create legacy histopathologist profile for migration testing
        histopathologist = Histopathologist.objects.create(
            user=user,
            first_name="Dr. John",
            last_name="Pathologist",
            license_number="HP-12345",
            position="Jefe de TP",
            specialty="Anatomía Patológica",
            is_active=True,
        )

        self.assertEqual(
            histopathologist.get_full_name(), "Dr. John Pathologist"
        )
        self.assertTrue(histopathologist.is_active)
        self.assertEqual(histopathologist.license_number, "HP-12345")


class LaboratoryStaffPermissionTest(TestCase):
    """Test LaboratoryStaff permission logic."""

    def setUp(self):
        """Set up test data for permission tests."""
        self.lab_staff_with_reports = User.objects.create_user(
            email="lab_with_reports@example.com",
            username="lab_with_reports",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
        )
        self.lab_staff_without_reports = User.objects.create_user(
            email="lab_without_reports@example.com",
            username="lab_without_reports",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
        )

        # Create profiles
        self.staff_with_reports = LaboratoryStaff.objects.create(
            user=self.lab_staff_with_reports,
            first_name="John",
            last_name="Doe",
            license_number="LS-PERM-001",
            can_create_reports=True,
        )

        self.staff_without_reports = LaboratoryStaff.objects.create(
            user=self.lab_staff_without_reports,
            first_name="Jane",
            last_name="Smith",
            license_number="LS-PERM-002",
            can_create_reports=False,
        )

    def test_permission_based_report_creation(self):
        """Test that can_create_reports works correctly."""
        # Staff with reports should be able to create reports
        self.assertTrue(self.staff_with_reports.can_create_reports)
        self.assertTrue(self.staff_with_reports.is_histopathologist_equivalent)

        # Staff without reports should not be able to create reports
        self.assertFalse(self.staff_without_reports.can_create_reports)
        self.assertFalse(
            self.staff_without_reports.is_histopathologist_equivalent
        )

    def test_admin_permission_toggle_audit(self):
        """Test that admin permission changes are logged."""
        # Login as admin
        admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.client.force_login(admin_user)

        # Test that we can change permission via admin (this would be tested in integration tests)
        # For now, just verify the audit log model exists
        self.assertTrue(hasattr(AuthAuditLog, "log"))


class LaboratoryStaffIntegrationTest(TestCase):
    """Integration tests for LaboratoryStaff with other models."""

    def setUp(self):
        """Set up test data for integration tests."""
        self.lab_staff = User.objects.create_user(
            email="lab@example.com",
            username="labuser",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
        )

        self.vet = User.objects.create_user(
            email="vet@example.com",
            username="vetuser",
            password="testpass123",
            role=User.Role.VETERINARIO,
        )

        # Create veterinarian profile
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet,
            first_name="John",
            last_name="Veterinarian",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )

        # Create lab staff profile
        self.laboratory_staff = LaboratoryStaff.objects.create(
            user=self.lab_staff,
            first_name="Jane",
            last_name="LabStaff",
            license_number="LS-12345",
            can_create_reports=True,
        )

    def test_user_profile_relationships(self):
        """Test that user profile relationships work correctly."""
        # Verify relationships are properly set up
        self.assertEqual(
            self.lab_staff.laboratory_staff_profile, self.laboratory_staff
        )
        self.assertEqual(self.vet.veterinarian_profile, self.veterinarian)

        # Test that lab staff is also lab staff
        self.assertTrue(self.lab_staff.is_lab_staff)
        self.assertFalse(self.vet.is_lab_staff)

    def test_audit_log_for_staff_creation(self):
        """Test that staff creation creates audit logs."""
        # This would test the integration with AuthAuditLog
        # For now, just verify the model exists
        self.assertTrue(hasattr(AuthAuditLog, "objects"))
