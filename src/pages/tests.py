from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Histopathologist, Veterinarian
from protocols.models import Protocol, Report, WorkOrder

User = get_user_model()


class ViewTests(TestCase):
    def test_home_page(self):
        """Home page should respond with a success 200."""
        response = self.client.get("/", follow=True)
        self.assertEqual(response.status_code, 200)


class DashboardViewsTest(TestCase):
    """Test cases for dashboard views (Phase 3)."""
    
    def setUp(self):
        """Set up test data for dashboard views."""
        # Create users with different roles
        self.vet_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staff",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
            is_staff=True,
        )
        self.histopathologist_user = User.objects.create_user(
            email="histo@example.com",
            username="histo",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
            email_verified=True,
            is_staff=True,
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="testpass123",
            role=User.Role.ADMIN,
            email_verified=True,
            is_staff=True,
        )
        
        # Create veterinarian
        self.veterinarian = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="John",
            last_name="Doe",
            license_number="MP-12345",
            phone="+54 341 1234567",
            email="vet@example.com",
        )
        
        # Create histopathologist
        self.histopathologist = Histopathologist.objects.create(
            user=self.histopathologist_user,
            first_name="Dr. Jane",
            last_name="Smith",
            license_number="MP-67890",
            position="Jefe de Histopatología",
            specialty="Oncología",
        )
        
        # Create test protocols with different statuses
        self.submitted_protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Max",
            presumptive_diagnosis="Masa cutánea",
            submission_date=date.today(),
        )
        self.submitted_protocol.submit()
        
        self.received_protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Felino",
            animal_identification="Luna",
            presumptive_diagnosis="Tumor mamario",
            submission_date=date.today(),
        )
        self.received_protocol.submit()
        self.received_protocol.receive(received_by=self.staff_user)
        
        self.processing_protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Canino",
            animal_identification="Rex",
            presumptive_diagnosis="Linfoma",
            submission_date=date.today(),
        )
        self.processing_protocol.submit()
        self.processing_protocol.receive(received_by=self.staff_user)
        self.processing_protocol.status = Protocol.Status.PROCESSING
        self.processing_protocol.save(update_fields=["status"])
        
        self.ready_protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=self.veterinarian,
            species="Felino",
            animal_identification="Mittens",
            presumptive_diagnosis="Sarcoma",
            submission_date=date.today(),
        )
        self.ready_protocol.submit()
        self.ready_protocol.receive(received_by=self.staff_user)
        self.ready_protocol.status = Protocol.Status.READY
        self.ready_protocol.save(update_fields=["status"])
        
        # Create reports
        self.draft_report = Report.objects.create(
            protocol=self.ready_protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            macroscopic_observations="Masa firme, bien delimitada",
            microscopic_observations="Células epiteliales atípicas",
            diagnosis="Carcinoma mamario",
            comments="Recomiendo seguimiento",
            recommendations="Cirugía de ampliación",
            status=Report.Status.DRAFT,
        )
        
        self.finalized_report = Report.objects.create(
            protocol=self.received_protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            macroscopic_observations="Masa firme, bien delimitada",
            microscopic_observations="Células epiteliales atípicas",
            diagnosis="Tumor benigno",
            comments="Buen pronóstico",
            recommendations="Seguimiento rutinario",
            status=Report.Status.DRAFT,
        )
        self.finalized_report.finalize()
        
        # Create work order
        self.work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("1500.00"),
            status=WorkOrder.Status.DRAFT,
        )
    
    # =============================================================================
    # DASHBOARD VIEW ROUTING TESTS
    # =============================================================================
    
    def test_dashboard_view_veterinarian_redirect(self):
        """Test that dashboard_view redirects veterinarians to veterinarian_dashboard."""
        self.client.login(email="vet@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_veterinarian.html")
        self.assertIn("veterinarian", response.context)
        self.assertIn("active_protocols_count", response.context)
    
    def test_dashboard_view_histopathologist_redirect(self):
        """Test that dashboard_view redirects histopathologists to histopathologist_dashboard."""
        self.client.login(email="histo@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_histopathologist.html")
        self.assertIn("pending_reports_count", response.context)
    
    def test_dashboard_view_lab_staff_redirect(self):
        """Test that dashboard_view redirects lab staff to lab_staff_dashboard."""
        self.client.login(email="staff@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_lab_staff.html")
        self.assertIn("pending_reception_count", response.context)
    
    def test_dashboard_view_admin_redirect(self):
        """Test that dashboard_view redirects admins to admin_dashboard."""
        self.client.login(email="admin@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_admin.html")
        self.assertIn("total_protocols_count", response.context)
    
    def test_dashboard_view_requires_login(self):
        """Test that dashboard_view requires login."""
        response = self.client.get(reverse("pages:dashboard"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/dashboard/")
    
    # =============================================================================
    # VETERINARIAN DASHBOARD TESTS
    # =============================================================================
    
    def test_veterinarian_dashboard_get(self):
        """Test GET request to veterinarian dashboard."""
        self.client.login(email="vet@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_veterinarian"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_veterinarian.html")
        self.assertIn("veterinarian", response.context)
        self.assertIn("active_protocols_count", response.context)
        self.assertIn("ready_reports_count", response.context)
        self.assertIn("monthly_protocols_count", response.context)
        self.assertIn("recent_protocols", response.context)
    
    def test_veterinarian_dashboard_statistics(self):
        """Test that veterinarian dashboard shows correct statistics."""
        self.client.login(email="vet@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_veterinarian"))
        
        # Should have 3 active protocols (submitted, received, processing, ready)
        self.assertEqual(response.context["active_protocols_count"], 4)
        # Should have 1 ready report
        self.assertEqual(response.context["ready_reports_count"], 1)
        # Should have 4 monthly protocols (all created today)
        self.assertEqual(response.context["monthly_protocols_count"], 4)
        # Should have recent protocols
        self.assertEqual(len(response.context["recent_protocols"]), 4)
    
    def test_veterinarian_dashboard_permission_non_veterinarian(self):
        """Test that non-veterinarians are redirected from veterinarian dashboard."""
        self.client.login(email="staff@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_veterinarian"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:dashboard"))
    
    def test_veterinarian_dashboard_requires_login(self):
        """Test that veterinarian dashboard requires login."""
        response = self.client.get(reverse("pages:dashboard_veterinarian"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/dashboard/veterinarian/")
    
    def test_veterinarian_dashboard_no_profile_redirect(self):
        """Test that veterinarians without profile are redirected to create profile."""
        # Create a veterinarian user without profile
        User.objects.create_user(
            email="vet_noprofile@example.com",
            username="vet_noprofile",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        
        self.client.login(email="vet_noprofile@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_veterinarian"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:complete_profile"))
    
    # =============================================================================
    # LAB STAFF DASHBOARD TESTS
    # =============================================================================
    
    def test_lab_staff_dashboard_get(self):
        """Test GET request to lab staff dashboard."""
        self.client.login(email="staff@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_lab_staff"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_lab_staff.html")
        self.assertIn("pending_reception_count", response.context)
        self.assertIn("processing_count", response.context)
        self.assertIn("today_received_count", response.context)
        self.assertIn("processing_queue", response.context)
    
    def test_lab_staff_dashboard_statistics(self):
        """Test that lab staff dashboard shows correct statistics."""
        self.client.login(email="staff@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_lab_staff"))
        
        # Should have 1 pending reception (submitted)
        self.assertEqual(response.context["pending_reception_count"], 1)
        # Should have 2 processing (received + processing)
        self.assertEqual(response.context["processing_count"], 2)
        # Should have 2 today received (received + processing, both received today)
        self.assertEqual(response.context["today_received_count"], 2)
        # Should have processing queue
        self.assertEqual(len(response.context["processing_queue"]), 2)
    
    def test_lab_staff_dashboard_permission_non_lab_staff(self):
        """Test that non-lab staff are redirected from lab staff dashboard."""
        self.client.login(email="vet@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_lab_staff"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:dashboard"))
    
    def test_lab_staff_dashboard_requires_login(self):
        """Test that lab staff dashboard requires login."""
        response = self.client.get(reverse("pages:dashboard_lab_staff"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/dashboard/lab-staff/")
    
    # =============================================================================
    # HISTOPATHOLOGIST DASHBOARD TESTS
    # =============================================================================
    
    def test_histopathologist_dashboard_get(self):
        """Test GET request to histopathologist dashboard."""
        self.client.login(email="histo@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_histopathologist"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_histopathologist.html")
        self.assertIn("pending_reports_count", response.context)
        self.assertIn("monthly_reports_count", response.context)
        self.assertIn("avg_report_time", response.context)
        self.assertIn("pending_reports", response.context)
    
    def test_histopathologist_dashboard_statistics(self):
        """Test that histopathologist dashboard shows correct statistics."""
        self.client.login(email="histo@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_histopathologist"))
        
        # Should have 1 pending report (draft)
        self.assertEqual(response.context["pending_reports_count"], 1)
        # Should have 1 monthly report (finalized this month)
        self.assertEqual(response.context["monthly_reports_count"], 1)
        # Should have pending reports list
        self.assertEqual(len(response.context["pending_reports"]), 1)
    
    def test_histopathologist_dashboard_permission_non_histopathologist(self):
        """Test that non-histopathologists are redirected from histopathologist dashboard."""
        self.client.login(email="vet@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_histopathologist"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:dashboard"))
    
    def test_histopathologist_dashboard_requires_login(self):
        """Test that histopathologist dashboard requires login."""
        response = self.client.get(reverse("pages:dashboard_histopathologist"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/dashboard/histopathologist/")
    
    # =============================================================================
    # ADMIN DASHBOARD TESTS
    # =============================================================================
    
    def test_admin_dashboard_get(self):
        """Test GET request to admin dashboard."""
        self.client.login(email="admin@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_admin"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/dashboard_admin.html")
        self.assertIn("total_protocols_count", response.context)
        self.assertIn("completed_reports_count", response.context)
        self.assertIn("total_users_count", response.context)
        self.assertIn("active_users_count", response.context)
        self.assertIn("avg_tat_days", response.context)
        self.assertIn("recent_activities", response.context)
    
    def test_admin_dashboard_statistics(self):
        """Test that admin dashboard shows correct statistics."""
        self.client.login(email="admin@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_admin"))
        
        # Should have 4 total protocols (all created this year)
        self.assertEqual(response.context["total_protocols_count"], 4)
        # Should have 1 completed report (finalized this month)
        self.assertEqual(response.context["completed_reports_count"], 1)
        # Should have 4 total users
        self.assertEqual(response.context["total_users_count"], 4)
        # Should have recent activities
        self.assertEqual(len(response.context["recent_activities"]), 3)
    
    def test_admin_dashboard_permission_non_admin(self):
        """Test that non-admins are redirected from admin dashboard."""
        self.client.login(email="vet@example.com", password="testpass123")
        
        response = self.client.get(reverse("pages:dashboard_admin"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:dashboard"))
    
    def test_admin_dashboard_requires_login(self):
        """Test that admin dashboard requires login."""
        response = self.client.get(reverse("pages:dashboard_admin"))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/dashboard/admin/")
    
    # =============================================================================
    # HOME PAGE TESTS
    # =============================================================================
    
    def test_home_page_statistics(self):
        """Test that home page shows correct statistics."""
        response = self.client.get(reverse("home"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/landing.html")
        self.assertIn("total_protocols", response.context)
        self.assertIn("total_users", response.context)
        self.assertIn("total_veterinarians", response.context)
        self.assertIn("recent_protocols", response.context)
        
        # Should have 4 total protocols
        self.assertEqual(response.context["total_protocols"], 4)
        # Should have 4 total users
        self.assertEqual(response.context["total_users"], 4)
        # Should have 1 total veterinarian
        self.assertEqual(response.context["total_veterinarians"], 1)
        # Should have recent protocols
        self.assertEqual(len(response.context["recent_protocols"]), 4)
    
    def test_home_page_context(self):
        """Test that home page has correct context variables."""
        response = self.client.get(reverse("home"))
        
        self.assertIn("debug", response.context)
        self.assertIn("django_ver", response.context)
        self.assertIn("python_ver", response.context)
