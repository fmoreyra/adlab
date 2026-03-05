"""
Models for the pages app.

Stores dashboard-related data such as cached server stats snapshots.
"""

from django.db import models


class ServerStatsSnapshot(models.Model):
    """
    Singleton row storing the latest server stats (CPU, RAM, disk, Docker).

    Updated by the Celery Beat task refresh_server_stats every few seconds.
    The API endpoint reads this row only; it does not compute stats.
    """

    SINGLETON_PK = 1

    payload = models.JSONField(
        verbose_name="Payload",
        help_text="JSON: system, docker, storage keys as returned by server_stats_service",
        default=dict,
    )
    updated_at = models.DateTimeField(
        verbose_name="Actualizado",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Snapshot de estadísticas del servidor"
        verbose_name_plural = "Snapshots de estadísticas del servidor"

    def __str__(self):
        return f"Server stats @ {self.updated_at.isoformat()}"

    @classmethod
    def get_latest(cls):
        """Return the singleton snapshot or None if not yet created."""
        return cls.objects.filter(pk=cls.SINGLETON_PK).first()

    @classmethod
    def update_payload(cls, payload):
        """Create or update the singleton row with the given payload."""
        obj, _ = cls.objects.get_or_create(
            pk=cls.SINGLETON_PK,
            defaults={"payload": payload},
        )
        if not _:
            obj.payload = payload
            obj.save(update_fields=["payload", "updated_at"])
        return obj
