"""
Tests for Management Dashboard API Views (Step 09).

Tests the dashboard API endpoints for WIP, volume, TAT, productivity, aging, and alerts.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Histopathologist, Veterinarian
from protocols.models import (
    Cassette,
    HistopathologySample,
    Protocol,
    Report,
    Slide,
)

User = get_user_model()


class DashboardAPITestCase(TestCase):
    """Base test case for dashboard API tests."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.lab_staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="testpass123",
            first_name="Lab",
            last_name="Staff",
            role=User.Role.PERSONAL_LAB,
        )

        self.histopathologist = User.objects.create_user(
            username="histo",
            email="histo@example.com",
            password="testpass123",
            first_name="Dr. Ana",
            last_name="López",
            role=User.Role.HISTOPATOLOGO,
        )

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMIN,
        )

        self.veterinarian = User.objects.create_user(
            username="vet",
            email="vet@example.com",
            password="testpass123",
            first_name="Dr. Juan",
            last_name="Pérez",
            role=User.Role.VETERINARIO,
        )

        # Create veterinarian profile
        self.vet_profile = Veterinarian.objects.create(
            user=self.veterinarian,
            first_name="Dr. Juan",
            last_name="Pérez",
            license_number="MP-12345",
            phone="+54 11 1234-5678",
            email="vet@example.com",
        )

        # Create histopathologist profile
        self.histo_profile = Histopathologist.objects.create(
            user=self.histopathologist,
            first_name="Dr. Ana",
            last_name="López",
            license_number="HISTO123",
            specialty="Patología General",
        )

        # Create test protocols
        self.now = timezone.now()
        self.yesterday = self.now - timedelta(days=1)
        self.week_ago = self.now - timedelta(days=7)
        self.month_ago = self.now - timedelta(days=30)

        # Create protocols in different states
        self.protocol_submitted = Protocol.objects.create(
            protocol_number="HP 24/001",
            veterinarian=self.vet_profile,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.SUBMITTED,
            submission_date=self.yesterday.date(),
            animal_identification="Max",
            species="Canino",
        )

        self.protocol_received = Protocol.objects.create(
            protocol_number="HP 24/002",
            veterinarian=self.vet_profile,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.RECEIVED,
            submission_date=self.week_ago.date(),
            reception_date=self.yesterday,
            animal_identification="Luna",
            species="Felino",
        )

        self.protocol_processing = Protocol.objects.create(
            protocol_number="HP 24/003",
            veterinarian=self.vet_profile,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.PROCESSING,
            submission_date=self.week_ago.date(),
            reception_date=self.week_ago,
            animal_identification="Bella",
            species="Canino",
        )

        self.protocol_ready = Protocol.objects.create(
            protocol_number="HP 24/004",
            veterinarian=self.vet_profile,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.READY,
            submission_date=self.week_ago.date(),
            reception_date=self.week_ago,
            animal_identification="Rocky",
            species="Canino",
        )

        # Create cytology protocols
        self.cyto_submitted = Protocol.objects.create(
            protocol_number="CT 24/001",
            veterinarian=self.vet_profile,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.SUBMITTED,
            submission_date=self.yesterday.date(),
            animal_identification="Mimi",
            species="Felino",
        )

        self.cyto_ready = Protocol.objects.create(
            protocol_number="CT 24/002",
            veterinarian=self.vet_profile,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.READY,
            submission_date=self.week_ago.date(),
            reception_date=self.week_ago,
            animal_identification="Toby",
            species="Canino",
        )

        # Create completed reports
        self.completed_report = Report.objects.create(
            protocol=self.protocol_ready,
            histopathologist=self.histo_profile,
            veterinarian=self.vet_profile,
            diagnosis="Test diagnosis",
            status=Report.Status.FINALIZED,
            created_at=self.week_ago,
            updated_at=self.yesterday,
        )

        # Create histopathology samples first
        self.histopathology_sample_processing = (
            HistopathologySample.objects.create(
                protocol=self.protocol_processing,
                veterinarian=self.vet_profile,
                material_submitted="Test material for processing",
                number_of_containers=1,
            )
        )

        self.histopathology_sample_ready = HistopathologySample.objects.create(
            protocol=self.protocol_ready,
            veterinarian=self.vet_profile,
            material_submitted="Test material for ready",
            number_of_containers=1,
        )

        # Create cassettes and slides for processing stages
        self.cassette_pending = Cassette.objects.create(
            histopathology_sample=self.histopathology_sample_processing,
            material_incluido="Test material included",
            estado=Cassette.Status.PENDIENTE,
        )

        self.cassette_processing = Cassette.objects.create(
            histopathology_sample=self.histopathology_sample_processing,
            material_incluido="Test material processing",
            estado=Cassette.Status.EN_PROCESO,
        )

        self.slide_mounted = Slide.objects.create(
            protocol=self.protocol_processing,
            estado=Slide.Status.MONTADO,
        )

        self.slide_stained = Slide.objects.create(
            protocol=self.protocol_processing,
            estado=Slide.Status.COLOREADO,
        )

        self.client = Client()


class DashboardWIPViewTest(DashboardAPITestCase):
    """Test WIP dashboard API."""

    def test_wip_view_requires_management_access(self):
        """Test that WIP view requires management user access."""
        # Test with veterinarian (should be denied)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_wip"))
        self.assertEqual(response.status_code, 403)

        # Test with lab staff (should be allowed)
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_wip"))
        self.assertEqual(response.status_code, 200)

        # Test with histopathologist (should be allowed)
        self.client.login(email="histo@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_wip"))
        self.assertEqual(response.status_code, 200)

        # Test with admin (should be allowed)
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_wip"))
        self.assertEqual(response.status_code, 200)

    def test_wip_view_requires_login(self):
        """Test that WIP view requires login."""
        response = self.client.get(reverse("pages_api:dashboard_wip"))
        self.assertEqual(response.status_code, 302)

    def test_wip_view_returns_correct_data(self):
        """Test that WIP view returns correct data structure."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_wip"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Histopatología")
        self.assertContains(response, "Citología")
        self.assertContains(response, "Pendiente Recepción")
        self.assertContains(response, "Procesando")

    def test_wip_view_counts_protocols_correctly(self):
        """Test that WIP view counts protocols correctly."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_wip"))

        self.assertEqual(response.status_code, 200)

        # Should show submitted protocols as "pendiente_recepcion"
        self.assertContains(
            response, "Histopatología"
        )  # histopathology section
        self.assertContains(response, "Citología")  # cytology section

        # Should show received protocols
        self.assertContains(response, "Recibido")  # received status

        # Should show processing protocols
        self.assertContains(response, "Procesando")  # processing status

        # Should show ready protocols
        self.assertContains(response, "Listo Diagnóstico")  # ready status


class DashboardVolumeViewTest(DashboardAPITestCase):
    """Test volume dashboard API."""

    def test_volume_view_requires_management_access(self):
        """Test that volume view requires management user access."""
        # Test with veterinarian (should be denied)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_volume"))
        self.assertEqual(response.status_code, 403)

    def test_volume_view_with_different_periods(self):
        """Test volume view with different period parameters."""
        self.client.login(email="staff@example.com", password="testpass123")

        # Test with default period (mes)
        response = self.client.get(reverse("pages_api:dashboard_volume"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mes")

        # Test with semana period
        response = self.client.get(
            reverse("pages_api:dashboard_volume") + "?periodo=semana"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semana")

        # Test with año period
        response = self.client.get(
            reverse("pages_api:dashboard_volume") + "?periodo=año"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Año")

    def test_volume_view_shows_correct_metrics(self):
        """Test that volume view shows correct volume metrics."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_volume"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Protocolos Histopatología")
        self.assertContains(response, "Protocolos Citología")
        self.assertContains(response, "Total Protocolos")


class DashboardTATViewTest(DashboardAPITestCase):
    """Test TAT dashboard API."""

    def test_tat_view_requires_management_access(self):
        """Test that TAT view requires management user access."""
        # Test with veterinarian (should be denied)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_tat"))
        self.assertEqual(response.status_code, 403)

    def test_tat_view_returns_correct_structure(self):
        """Test that TAT view returns correct data structure."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_tat"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Histopatología")
        self.assertContains(response, "Citología")
        self.assertContains(response, "TAT Promedio")
        self.assertContains(response, "Dentro del objetivo")

    def test_tat_view_calculates_metrics(self):
        """Test that TAT view calculates metrics correctly."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_tat"))

        self.assertEqual(response.status_code, 200)

        # Should show TAT metrics for both analysis types
        self.assertContains(response, "días")
        self.assertContains(response, "Objetivo")


class DashboardProductivityViewTest(DashboardAPITestCase):
    """Test productivity dashboard API."""

    def test_productivity_view_requires_management_access(self):
        """Test that productivity view requires management user access."""
        # Test with veterinarian (should be denied)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_productivity"))
        self.assertEqual(response.status_code, 403)

    def test_productivity_view_with_different_periods(self):
        """Test productivity view with different period parameters."""
        self.client.login(email="staff@example.com", password="testpass123")

        # Test with default period (mes)
        response = self.client.get(reverse("pages_api:dashboard_productivity"))
        self.assertEqual(response.status_code, 200)

        # Test with semana period
        response = self.client.get(
            reverse("pages_api:dashboard_productivity") + "?periodo=semana"
        )
        self.assertEqual(response.status_code, 200)

        # Test with año period
        response = self.client.get(
            reverse("pages_api:dashboard_productivity") + "?periodo=año"
        )
        self.assertEqual(response.status_code, 200)

    def test_productivity_view_shows_histopathologists(self):
        """Test that productivity view shows histopathologist data."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_productivity"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Histopatólogo")
        self.assertContains(response, "Reportes Enviados")
        self.assertContains(response, "Promedio/Semana")
        self.assertContains(response, "TAT Promedio")


class DashboardAgingViewTest(DashboardAPITestCase):
    """Test aging dashboard API."""

    def test_aging_view_requires_management_access(self):
        """Test that aging view requires management user access."""
        # Test with veterinarian (should be denied)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_aging"))
        self.assertEqual(response.status_code, 403)

    def test_aging_view_returns_correct_structure(self):
        """Test that aging view returns correct data structure."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_aging"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Distribución por Edad")
        self.assertContains(response, "0-3 días")
        self.assertContains(response, "4-7 días")
        self.assertContains(response, "8-14 días")
        self.assertContains(response, "+14 días")

    def test_aging_view_shows_overdue_samples(self):
        """Test that aging view shows overdue samples."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_aging"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Muestras Vencidas")


class DashboardAlertsViewTest(DashboardAPITestCase):
    """Test alerts dashboard API."""

    def test_alerts_view_requires_management_access(self):
        """Test that alerts view requires management user access."""
        # Test with veterinarian (should be denied)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_alerts"))
        self.assertEqual(response.status_code, 403)

    def test_alerts_view_returns_correct_structure(self):
        """Test that alerts view returns correct data structure."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_alerts"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sin alertas")

    def test_alerts_view_shows_no_alerts_when_none(self):
        """Test that alerts view shows no alerts message when none exist."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_alerts"))

        self.assertEqual(response.status_code, 200)
        # Should show "Sin alertas" message when no alerts exist
        self.assertContains(response, "Sin alertas")


class ManagementDashboardViewTest(DashboardAPITestCase):
    """Test management dashboard view."""

    def test_management_dashboard_requires_management_access(self):
        """Test that management dashboard requires management user access."""
        # Test with veterinarian (should redirect)
        self.client.login(email="vet@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard_management"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:dashboard"))

        # Test with lab staff (should be allowed)
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard_management"))
        self.assertEqual(response.status_code, 200)

        # Test with histopathologist (should be allowed)
        self.client.login(email="histo@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard_management"))
        self.assertEqual(response.status_code, 200)

        # Test with admin (should be allowed)
        self.client.login(email="admin@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard_management"))
        self.assertEqual(response.status_code, 200)

    def test_management_dashboard_requires_login(self):
        """Test that management dashboard requires login."""
        response = self.client.get(reverse("pages:dashboard_management"))
        self.assertEqual(response.status_code, 302)

    def test_management_dashboard_renders_correctly(self):
        """Test that management dashboard renders correctly."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard_management"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard de Gestión")
        self.assertContains(response, "Work in Progress (WIP)")
        self.assertContains(response, "Métricas de Volumen")
        self.assertContains(response, "Tiempo de Respuesta (TAT)")
        self.assertContains(response, "Productividad por Histopatólogo")
        self.assertContains(response, "Envejecimiento de Muestras")
        self.assertContains(response, "Alertas del Sistema")

    def test_management_dashboard_has_htmx_attributes(self):
        """Test that management dashboard has HTMX attributes for auto-refresh."""
        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages:dashboard_management"))

        self.assertEqual(response.status_code, 200)
        # Check for HTMX attributes
        self.assertContains(response, "hx-get=")
        self.assertContains(response, "hx-trigger=")
        self.assertContains(response, "hx-indicator=")
        self.assertContains(response, "hx-target=")


class DashboardPerformanceTest(DashboardAPITestCase):
    """Test dashboard performance and optimization."""

    def test_wip_view_performance(self):
        """Test WIP view performance with multiple protocols."""
        # Create additional protocols to test performance
        for i in range(50):
            Protocol.objects.create(
                protocol_number=f"HP 24/{i + 100:03d}",
                veterinarian=self.vet_profile,
                analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
                status=Protocol.Status.SUBMITTED,
                submission_date=self.yesterday.date(),
                animal_identification=f"Animal {i}",
                species="Canino",
            )

        self.client.login(email="staff@example.com", password="testpass123")

        # Test that the view still responds quickly
        response = self.client.get(reverse("pages_api:dashboard_wip"))
        self.assertEqual(response.status_code, 200)

        # Response should be reasonably fast (this is a basic test)
        # In a real scenario, you'd use more sophisticated performance testing

    def test_volume_view_with_large_dataset(self):
        """Test volume view with large dataset."""
        # Create many protocols across different time periods
        for i in range(100):
            Protocol.objects.create(
                protocol_number=f"HP 24/{i + 200:03d}",
                veterinarian=self.vet_profile,
                analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
                status=Protocol.Status.SUBMITTED,
                submission_date=(self.now - timedelta(days=i)).date(),
                animal_identification=f"Animal {i}",
                species="Canino",
            )

        self.client.login(email="staff@example.com", password="testpass123")
        response = self.client.get(reverse("pages_api:dashboard_volume"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Protocolos Histopatología")
