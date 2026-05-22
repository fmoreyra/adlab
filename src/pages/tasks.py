"""
Celery tasks for the pages app.

Refreshes server stats snapshot for the admin dashboard.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from pages.models import DashboardAnnouncement, ServerStatsSnapshot
from pages.services.dashboard_announcement_service import (
    get_notification_preview_body,
)
from protocols.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

User = get_user_model()

NOTIFICATION_BATCH_SIZE = 100


@shared_task(name="pages.tasks.refresh_server_stats")
def refresh_server_stats():
    """
    Collect server stats and save to ServerStatsSnapshot (singleton).

    Called by Celery Beat every 5 seconds. The API endpoint reads from
    ServerStatsSnapshot only; it does not call the stats service.
    """
    try:
        from services.server_stats_service import (
            get_docker_stats,
            get_media_bucket_stats,
            get_system_stats,
        )

        system = get_system_stats()
        docker = get_docker_stats()
        storage = get_media_bucket_stats()
        payload = {
            "system": system,
            "docker": docker,
            "storage": storage,
        }
        ServerStatsSnapshot.update_payload(payload)
    except Exception as e:
        logger.warning("refresh_server_stats failed: %s", e, exc_info=True)


@shared_task(name="pages.tasks.notify_dashboard_announcement_update")
def notify_dashboard_announcement_update(announcement_id: int):
    """
    Fan out in-app notifications when the dashboard banner is updated.

    Push-only (Sockudo when enabled); does not send email.

    Args:
        announcement_id: DashboardAnnouncement primary key
    """
    announcement = DashboardAnnouncement.objects.filter(
        pk=announcement_id
    ).first()
    if announcement is None:
        logger.warning(
            "notify_dashboard_announcement_update: announcement %s not found",
            announcement_id,
        )
        return

    if not announcement.is_active or not announcement.message.strip():
        return

    dashboard_path = reverse("pages:dashboard")
    link_url = f"{settings.SITE_URL}{dashboard_path}"
    body = get_notification_preview_body(announcement.message)
    title = "Nuevo aviso del laboratorio"
    service = NotificationService()

    user_ids = list(
        User.objects.filter(is_active=True).values_list("id", flat=True)
    )
    for offset in range(0, len(user_ids), NOTIFICATION_BATCH_SIZE):
        batch_ids = user_ids[offset : offset + NOTIFICATION_BATCH_SIZE]
        for user in User.objects.filter(id__in=batch_ids):
            service.create_for_dashboard_announcement(
                recipient=user,
                title=title,
                body=body,
                link_url=link_url,
            )

    logger.info(
        "Dashboard announcement notifications sent",
        extra={
            "recipient_count": len(user_ids),
            "announcement_id": announcement_id,
        },
    )
