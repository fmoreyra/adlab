"""
Tests for the admin dashboard announcement banner feature.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Address, Veterinarian
from pages.models import DashboardAnnouncement
from pages.services.dashboard_announcement_service import (
    CACHE_KEY,
    get_cached_banner,
    invalidate_banner_cache,
    render_message_safe,
    warm_banner_cache,
)
from pages.tasks import notify_dashboard_announcement_update
from protocols.models import InAppNotification

User = get_user_model()


class DashboardAnnouncementServiceTest(TestCase):
    """Tests for Markdown rendering and sanitization."""

    def test_render_message_safe_strips_script_tags(self):
        """XSS payloads must not appear in rendered HTML."""
        html = render_message_safe(
            'Hello <script>alert("xss")</script> **bold**'
        )
        self.assertNotIn("<script>", html)
        self.assertIn("bold", html)

    def test_render_message_safe_supports_markdown_links(self):
        """Markdown links are converted to safe anchor tags."""
        html = render_message_safe("[Lab](https://example.com)")
        self.assertIn("href=", html)
        self.assertIn("example.com", html)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "announcement-tests",
        }
    }
)
class DashboardAnnouncementCacheTest(TestCase):
    """Tests for Redis/LocMem cache behavior."""

    def setUp(self):
        cache.clear()

    def test_warm_cache_after_save(self):
        """Saving active announcement populates cache."""
        DashboardAnnouncement.update_announcement(
            message="**Aviso** de prueba",
            is_active=True,
            user=None,
        )
        invalidate_banner_cache()
        payload = warm_banner_cache()
        self.assertIsNotNone(payload)
        self.assertTrue(payload["is_active"])
        self.assertIn("Aviso", payload["html"])
        self.assertIsNotNone(cache.get(CACHE_KEY))

    def test_invalidate_clears_stale_cache(self):
        """Cache delete forces reload on next read."""
        cache.set(CACHE_KEY, {"is_active": True, "html": "<p>viejo</p>"}, 3600)
        invalidate_banner_cache()
        DashboardAnnouncement.update_announcement(
            message="Contenido nuevo",
            is_active=True,
            user=None,
        )
        warm_banner_cache()
        payload = get_cached_banner()
        self.assertIn("nuevo", payload["html"])


class DashboardAnnouncementViewTest(TestCase):
    """Tests for admin edit view and dashboard display."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-banner@example.com",
            username="adminbanner",
            password="testpass123",
            role=User.Role.ADMIN,
            email_verified=True,
            is_staff=True,
        )
        self.vet_user = User.objects.create_user(
            email="vet-banner@example.com",
            username="vetbanner",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )
        vet_profile = Veterinarian.objects.create(
            user=self.vet_user,
            first_name="Ana",
            last_name="Vet",
            license_number="MP-BANNER-01",
            cuil_cuit="20-12345678-9",
            phone="+54 341 1111111",
            email="vet-banner@example.com",
        )
        Address.objects.create(
            veterinarian=vet_profile,
            province="Santa Fe",
            locality="Rosario",
            street="San Martín",
            number="100",
            postal_code="2000",
        )
        self.staff_user = User.objects.create_user(
            email="staff-banner@example.com",
            username="staffbanner",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            email_verified=True,
            is_staff=True,
        )
        self.edit_url = reverse("pages:dashboard_announcement_edit")

    def test_admin_can_access_edit_view(self):
        """Admin user can load the announcement edit form."""
        self.client.login(
            email="admin-banner@example.com", password="testpass123"
        )
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aviso general del dashboard")

    def test_non_admin_cannot_access_edit_view(self):
        """Non-admin users cannot access the edit view."""
        self.client.login(
            email="vet-banner@example.com", password="testpass123"
        )
        response = self.client.get(self.edit_url)
        self.assertIn(response.status_code, (302, 403))

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "announcement-view-tests",
            }
        }
    )
    def test_banner_visible_on_lab_staff_dashboard_when_active(self):
        """Active announcement appears on role dashboard."""
        DashboardAnnouncement.update_announcement(
            message="Mantenimiento programado el viernes",
            is_active=True,
            user=self.admin_user,
        )
        warm_banner_cache()
        self.client.login(
            email="staff-banner@example.com", password="testpass123"
        )
        response = self.client.get(reverse("pages:dashboard_lab_staff"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mantenimiento programado")

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "announcement-view-tests-2",
            }
        }
    )
    def test_banner_hidden_when_inactive(self):
        """Inactive announcement does not render on dashboard."""
        DashboardAnnouncement.update_announcement(
            message="Texto oculto",
            is_active=False,
            user=self.admin_user,
        )
        warm_banner_cache()
        self.client.login(
            email="staff-banner@example.com", password="testpass123"
        )
        response = self.client.get(reverse("pages:dashboard_lab_staff"))
        self.assertNotContains(response, "Texto oculto")


class DashboardAnnouncementNotificationTest(TestCase):
    """Tests for in-app notification fan-out on banner update."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin-notif@example.com",
            username="adminnotif",
            password="testpass123",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.user_a = User.objects.create_user(
            email="usera@example.com",
            username="usera",
            password="testpass123",
            role=User.Role.PERSONAL_LAB,
            is_staff=True,
        )
        self.user_b = User.objects.create_user(
            email="userb@example.com",
            username="userb",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

    @patch("django.db.transaction.on_commit", side_effect=lambda fn: fn())
    @patch("pages.tasks.notify_dashboard_announcement_update.delay")
    def test_save_without_content_change_does_not_queue_task(
        self, mock_delay, _mock_on_commit
    ):
        """Unchanged hash must not trigger notification task."""
        announcement, _, _ = DashboardAnnouncement.update_announcement(
            message="Mismo texto",
            is_active=True,
            user=self.admin_user,
        )
        self.client.login(
            email="admin-notif@example.com", password="testpass123"
        )
        self.client.post(
            reverse("pages:dashboard_announcement_edit"),
            {
                "message": "Mismo texto",
                "is_active": "on",
                "action": "save",
            },
        )
        mock_delay.assert_not_called()
        announcement.refresh_from_db()
        self.assertEqual(announcement.message, "Mismo texto")

    @patch("django.db.transaction.on_commit", side_effect=lambda fn: fn())
    @patch("pages.tasks.notify_dashboard_announcement_update.delay")
    def test_save_with_content_change_queues_task(
        self, mock_delay, _mock_on_commit
    ):
        """Changed active announcement enqueues Celery notification task."""
        DashboardAnnouncement.update_announcement(
            message="Texto inicial",
            is_active=True,
            user=self.admin_user,
        )
        self.client.login(
            email="admin-notif@example.com", password="testpass123"
        )
        self.client.post(
            reverse("pages:dashboard_announcement_edit"),
            {
                "message": "Texto actualizado",
                "is_active": "on",
                "action": "save",
            },
        )
        mock_delay.assert_called_once()

    def test_notify_task_creates_in_app_notifications_without_email(self):
        """Fan-out creates ANNOUNCEMENT notifications and sends no email."""
        announcement, _, _ = DashboardAnnouncement.update_announcement(
            message="**Cierre** por feriado",
            is_active=True,
            user=self.admin_user,
        )
        mail.outbox.clear()
        notify_dashboard_announcement_update(announcement.pk)
        count = InAppNotification.objects.filter(
            notification_type=InAppNotification.NotificationType.ANNOUNCEMENT,
        ).count()
        self.assertEqual(count, User.objects.filter(is_active=True).count())
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_task_skips_when_inactive(self):
        """Inactive announcement does not create notifications."""
        announcement, _, _ = DashboardAnnouncement.update_announcement(
            message="No debe notificar",
            is_active=False,
            user=self.admin_user,
        )
        notify_dashboard_announcement_update(announcement.pk)
        self.assertEqual(InAppNotification.objects.count(), 0)
