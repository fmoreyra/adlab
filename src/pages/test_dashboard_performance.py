"""
Performance tests for Management Dashboard API Views.

Tests the performance of dashboard API endpoints with larger datasets
and monitors query counts, response times, and caching effectiveness.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Histopathologist, Veterinarian
from pages.performance_monitor import (
    check_performance_thresholds,
    monitor_performance,
)
from protocols.models import (
    Protocol,
    Report,
)

User = get_user_model()


class DashboardPerformanceTest(TestCase):
    """Performance tests for dashboard API endpoints."""

    def setUp(self):
        """Set up test data for performance testing."""
        # Create test users
        self.lab_staff = User.objects.create_user(
            username="lab_staff",
            email="lab@test.com",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_active=True,
        )

        # Create test data for performance testing
        self._create_performance_test_data()

    def _create_performance_test_data(self):
        """Create a larger dataset for performance testing."""
        # Create multiple veterinarians
        self.vets = []
        for i in range(10):
            vet_user = User.objects.create_user(
                username=f"vet_{i}",
                email=f"vet{i}@test.com",
                password="testpass123",
                role=User.Role.VETERINARIO,
                is_active=True,
            )
            vet = Veterinarian.objects.create(
                user=vet_user,
                first_name=f"Vet{i}",
                last_name="Test",
                license_number=f"LIC{i:03d}",
                phone="1234567890",
                email=f"vet{i}@test.com",
            )
            self.vets.append(vet)

        # Create multiple histopathologists
        self.histos = []
        for i in range(5):
            histo_user = User.objects.create_user(
                username=f"histo_{i}",
                email=f"histo{i}@test.com",
                password="testpass123",
                role=User.Role.HISTOPATOLOGO,
                is_active=True,
            )
            histo = Histopathologist.objects.create(
                user=histo_user,
                first_name=f"Histo{i}",
                last_name="Test",
                license_number=f"HISTO{i:03d}",
                specialty="General Pathology",
            )
            self.histos.append(histo)

        # Create multiple protocols with different statuses
        self.protocols = []
        for i in range(50):  # 50 protocols for performance testing
            vet = self.vets[i % len(self.vets)]
            protocol = Protocol.objects.create(
                veterinarian=vet,
                animal_identification=f"Animal{i:03d}",
                species="Canine",
                analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY
                if i % 2 == 0
                else Protocol.AnalysisType.CYTOLOGY,
                status=Protocol.Status.RECEIVED
                if i % 3 == 0
                else Protocol.Status.PROCESSING,
                reception_date=timezone.now() - timedelta(days=i % 10),
                submission_date=timezone.now() - timedelta(days=i % 10 + 1),
            )
            self.protocols.append(protocol)

        # Create reports for some protocols
        for i, protocol in enumerate(self.protocols[:30]):  # 30 reports
            histo = self.histos[i % len(self.histos)]
            Report.objects.create(
                protocol=protocol,
                histopathologist=histo,
                veterinarian=protocol.veterinarian,
                status=Report.Status.FINALIZED
                if i % 2 == 0
                else Report.Status.DRAFT,
                updated_at=timezone.now() - timedelta(days=i % 5),
            )

    def test_wip_view_performance(self):
        """Test WIP view performance with multiple protocols."""
        client = Client()
        client.force_login(self.lab_staff)

        with monitor_performance("wip_view") as monitor:
            response = client.get(reverse("pages_api:dashboard_wip"))

        # Check performance thresholds
        checks = check_performance_thresholds("wip", monitor.metrics)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            checks["passed"], f"Performance check failed: {checks['errors']}"
        )

        # Log performance metrics
        print("\nWIP View Performance:")
        print(f"  Response time: {monitor.metrics['total_time']}s")
        print(f"  Query count: {monitor.metrics['query_count']}")
        print(f"  Query time: {monitor.metrics['query_time']}s")

    def test_volume_view_with_large_dataset(self):
        """Test volume view performance with large dataset."""
        client = Client()
        client.force_login(self.lab_staff)

        with monitor_performance("volume_view") as monitor:
            response = client.get(reverse("pages_api:dashboard_volume"))

        # Check performance thresholds
        checks = check_performance_thresholds("volume", monitor.metrics)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            checks["passed"], f"Performance check failed: {checks['errors']}"
        )

        # Log performance metrics
        print("\nVolume View Performance:")
        print(f"  Response time: {monitor.metrics['total_time']}s")
        print(f"  Query count: {monitor.metrics['query_count']}")
        print(f"  Query time: {monitor.metrics['query_time']}s")

    def test_productivity_view_performance(self):
        """Test productivity view performance (should be optimized)."""
        client = Client()
        client.force_login(self.lab_staff)

        with monitor_performance("productivity_view") as monitor:
            response = client.get(reverse("pages_api:dashboard_productivity"))

        # Check performance thresholds
        checks = check_performance_thresholds("productivity", monitor.metrics)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            checks["passed"], f"Performance check failed: {checks['errors']}"
        )

        # Log performance metrics
        print("\nProductivity View Performance:")
        print(f"  Response time: {monitor.metrics['total_time']}s")
        print(f"  Query count: {monitor.metrics['query_count']}")
        print(f"  Query time: {monitor.metrics['query_time']}s")

        # Productivity view should have very few queries after optimization
        self.assertLessEqual(
            monitor.metrics["query_count"],
            2,
            "Productivity view should have ≤2 queries after optimization",
        )

    def test_aging_view_performance(self):
        """Test aging view performance."""
        client = Client()
        client.force_login(self.lab_staff)

        with monitor_performance("aging_view") as monitor:
            response = client.get(reverse("pages_api:dashboard_aging"))

        # Check performance thresholds
        checks = check_performance_thresholds("aging", monitor.metrics)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            checks["passed"], f"Performance check failed: {checks['errors']}"
        )

        # Log performance metrics
        print("\nAging View Performance:")
        print(f"  Response time: {monitor.metrics['total_time']}s")
        print(f"  Query count: {monitor.metrics['query_count']}")
        print(f"  Query time: {monitor.metrics['query_time']}s")

    def test_alerts_view_performance(self):
        """Test alerts view performance."""
        client = Client()
        client.force_login(self.lab_staff)

        with monitor_performance("alerts_view") as monitor:
            response = client.get(reverse("pages_api:dashboard_alerts"))

        # Check performance thresholds
        checks = check_performance_thresholds("alerts", monitor.metrics)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            checks["passed"], f"Performance check failed: {checks['errors']}"
        )

        # Log performance metrics
        print("\nAlerts View Performance:")
        print(f"  Response time: {monitor.metrics['total_time']}s")
        print(f"  Query count: {monitor.metrics['query_count']}")
        print(f"  Query time: {monitor.metrics['query_time']}s")

    def test_cache_effectiveness(self):
        """Test that caching improves performance on subsequent requests."""
        from django.core.cache import cache

        client = Client()
        client.force_login(self.lab_staff)

        # Clear cache before test
        cache.delete("dashboard_wip_metrics")

        # First request (cache miss)
        with monitor_performance("wip_first_request") as monitor1:
            response1 = client.get(reverse("pages_api:dashboard_wip"))

        # Verify cache was set
        self.assertIsNotNone(
            cache.get("dashboard_wip_metrics"),
            "Cache should be set after first request",
        )

        # Second request (cache hit)
        with monitor_performance("wip_second_request") as monitor2:
            response2 = client.get(reverse("pages_api:dashboard_wip"))

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Cached request should have fewer queries (more reliable than timing)
        self.assertLess(
            monitor2.metrics["query_count"],
            monitor1.metrics["query_count"],
            "Cached request should have fewer queries than first request",
        )

        # Second request should be faster or at least not significantly slower
        # (accounting for timing variance in fast operations)
        time_ratio = (
            monitor2.metrics["total_time"] / monitor1.metrics["total_time"]
        )
        self.assertLess(
            time_ratio,
            1.5,  # Allow up to 50% slower due to timing variance
            f"Cached request should not be significantly slower "
            f"(ratio: {time_ratio:.2f}, first: {monitor1.metrics['total_time']}s, "
            f"second: {monitor2.metrics['total_time']}s)",
        )

        print("\nCache Effectiveness:")
        print(
            f"  First request: {monitor1.metrics['total_time']}s, {monitor1.metrics['query_count']} queries"
        )
        print(
            f"  Second request: {monitor2.metrics['total_time']}s, {monitor2.metrics['query_count']} queries"
        )
        if monitor2.metrics["total_time"] < monitor1.metrics["total_time"]:
            print(
                f"  Speed improvement: {monitor1.metrics['total_time'] / monitor2.metrics['total_time']:.1f}x"
            )
        else:
            print(
                f"  Query reduction: {monitor1.metrics['query_count'] - monitor2.metrics['query_count']} fewer queries"
            )

    def test_performance_thresholds(self):
        """Test that all dashboard views meet performance thresholds."""
        client = Client()
        client.force_login(self.lab_staff)

        views = [
            ("wip", reverse("pages_api:dashboard_wip")),
            ("volume", reverse("pages_api:dashboard_volume")),
            ("productivity", reverse("pages_api:dashboard_productivity")),
            ("aging", reverse("pages_api:dashboard_aging")),
            ("alerts", reverse("pages_api:dashboard_alerts")),
        ]

        results = {}

        for view_name, url in views:
            with monitor_performance(f"{view_name}_threshold_test") as monitor:
                response = client.get(url)

            checks = check_performance_thresholds(view_name, monitor.metrics)
            results[view_name] = {
                "status_code": response.status_code,
                "metrics": monitor.metrics,
                "checks": checks,
            }

        # All views should pass performance checks
        for view_name, result in results.items():
            self.assertEqual(
                result["status_code"],
                200,
                f"{view_name} view should return 200",
            )
            self.assertTrue(
                result["checks"]["passed"],
                f"{view_name} view failed performance checks: {result['checks']['errors']}",
            )

        # Log summary
        print("\nPerformance Summary:")
        for view_name, result in results.items():
            metrics = result["metrics"]
            print(
                f"  {view_name}: {metrics['total_time']}s, {metrics['query_count']} queries"
            )
