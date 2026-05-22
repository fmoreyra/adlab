"""
Models for the pages app.

Stores dashboard-related data such as cached server stats snapshots.
"""

import hashlib

from django.conf import settings
from django.db import models


def _compute_announcement_hash(message: str, is_active: bool) -> str:
    """Return SHA-256 hex digest for announcement content identity."""
    payload = f"{is_active}:{message.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


class DashboardAnnouncement(models.Model):
    """
    Singleton row for the site-wide dashboard communication banner.

    Edited by administrators via a custom view; rendered on all pages
    dashboards with Redis caching.
    """

    SINGLETON_PK = 1
    MAX_MESSAGE_LENGTH = 4000

    message = models.TextField(
        verbose_name="Mensaje",
        blank=True,
        default="",
        help_text="Texto en Markdown (negrita, enlaces, listas).",
    )
    is_active = models.BooleanField(
        verbose_name="Activo",
        default=False,
        help_text="Si está desactivado, no se muestra el banner ni se notifica.",
    )
    content_hash = models.CharField(
        verbose_name="Hash de contenido",
        max_length=64,
        blank=True,
        default="",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dashboard_announcements_updated",
        verbose_name="Actualizado por",
    )
    updated_at = models.DateTimeField(
        verbose_name="Actualizado el",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Aviso general del dashboard"
        verbose_name_plural = "Avisos generales del dashboard"

    def __str__(self):
        status = "activo" if self.is_active else "inactivo"
        return f"Aviso dashboard ({status})"

    @classmethod
    def get_singleton(cls):
        """Return the singleton announcement row, creating it if needed."""
        obj, _ = cls.objects.get_or_create(
            pk=cls.SINGLETON_PK,
            defaults={"message": "", "is_active": False},
        )
        return obj

    @classmethod
    def update_announcement(cls, message, is_active, user):
        """
        Persist announcement and return (instance, hash_changed, previous_hash).

        Args:
            message: Markdown source text
            is_active: Whether the banner is visible
            user: Admin user performing the update

        Returns:
            tuple: (DashboardAnnouncement, hash_changed bool, previous_hash str)
        """
        obj = cls.get_singleton()
        previous_hash = obj.content_hash
        new_hash = _compute_announcement_hash(message, is_active)
        obj.message = message
        obj.is_active = is_active
        obj.content_hash = new_hash
        obj.updated_by = user
        obj.save(
            update_fields=[
                "message",
                "is_active",
                "content_hash",
                "updated_by",
                "updated_at",
            ]
        )
        hash_changed = previous_hash != new_hash
        return obj, hash_changed, previous_hash
