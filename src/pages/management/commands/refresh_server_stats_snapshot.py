"""
Management command to refresh ServerStatsSnapshot once.

Use when the Celery task is not running (e.g. worker/beat down) and the
server-stats API returns 503. Run on the server:

  make manage ARGS="refresh_server_stats_snapshot"
"""

from django.core.management.base import BaseCommand

from pages.models import ServerStatsSnapshot


class Command(BaseCommand):
    help = "Refresh ServerStatsSnapshot once (same as Celery task). Use to fix 503 when beat/worker are down."

    def handle(self, *args, **options):
        try:
            from services.server_stats_service import (
                get_docker_stats,
                get_media_bucket_stats,
                get_system_stats,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            return

        payload = {
            "system": get_system_stats(),
            "docker": get_docker_stats(),
            "storage": get_media_bucket_stats(),
        }
        ServerStatsSnapshot.update_payload(payload)
        snapshot = ServerStatsSnapshot.get_latest()
        self.stdout.write(
            self.style.SUCCESS(
                f"ServerStatsSnapshot updated at {snapshot.updated_at.isoformat()}"
            )
        )
