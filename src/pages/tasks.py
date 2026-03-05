"""
Celery tasks for the pages app.

Refreshes server stats snapshot for the admin dashboard.
"""

import logging

from celery import shared_task

from pages.models import ServerStatsSnapshot

logger = logging.getLogger(__name__)


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
