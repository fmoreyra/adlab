"""
In-app notification service (Step 21).

Creates persistent notifications in PostgreSQL and publishes realtime events
to Sockudo (Pusher-compatible). Sockudo is used only for push; persistence
is the source of truth.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from protocols.models import InAppNotification, Protocol, WorkOrder

logger = logging.getLogger(__name__)


def _sign_pusher_request(method: str, path: str, body: str = "") -> dict:
    """
    Sign HTTP request for Sockudo/Pusher API.

    Args:
        method: HTTP method (GET or POST)
        path: Request path (e.g. /apps/app-id/events)
        body: Request body for POST (empty for GET)

    Returns:
        dict: Query params including auth_signature
    """
    app_key = settings.SOCKUDO_APP_KEY
    app_secret = settings.SOCKUDO_APP_SECRET.encode("utf-8")
    auth_timestamp = str(int(timezone.now().timestamp()))
    params = {
        "auth_key": app_key,
        "auth_timestamp": auth_timestamp,
        "auth_version": "1.0",
    }
    if method == "POST" and body:
        params["body_md5"] = hashlib.md5(body.encode("utf-8")).hexdigest()
    query_for_sig = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    string_to_sign = f"{method}\n{path}\n{query_for_sig}"
    params["auth_signature"] = hmac.new(
        app_secret, string_to_sign.encode("utf-8"), "sha256"
    ).hexdigest()
    return params


def _publish_to_sockudo(channel: str, event_name: str, data: dict) -> bool:
    """
    Publish event to Sockudo via HTTP API.

    Args:
        channel: Channel name (e.g. private-user-123)
        event_name: Event name (e.g. notification.created)
        data: Event payload (will be JSON-serialized)

    Returns:
        bool: True if published successfully, False otherwise
    """
    if not getattr(settings, "SOCKUDO_ENABLED", False):
        return False
    app_id = settings.SOCKUDO_APP_ID
    base_url = settings.SOCKUDO_HTTP_URL.rstrip("/")
    path = f"/apps/{app_id}/events"
    body = json.dumps(
        {
            "name": event_name,
            "channel": channel,
            "data": json.dumps(data),
        }
    )
    params = _sign_pusher_request("POST", path, body)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base_url}{path}?{qs}"
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            data=body.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status in (200, 201):
                logger.info(
                    "Realtime event published",
                    extra={
                        "channel": channel,
                        "event": event_name,
                        "notification_id": data.get("id"),
                    },
                )
                return True
            logger.warning(
                f"Sockudo returned {resp.status} for {event_name}",
                extra={"channel": channel},
            )
            return False
    except Exception as e:
        logger.warning(
            f"Failed to publish to Sockudo: {e}",
            extra={"channel": channel, "event": event_name},
        )
        return False


class NotificationService:
    """
    Service for creating in-app notifications and publishing realtime events.
    """

    def create_notification(
        self,
        recipient,
        notification_type: str,
        title: str,
        body: str = "",
        link_url: str = "",
        protocol: Optional[Protocol] = None,
        work_order: Optional[WorkOrder] = None,
        publish_realtime: bool = True,
    ) -> InAppNotification:
        """
        Create in-app notification and optionally publish to Sockudo.

        Args:
            recipient: User instance (recipient)
            notification_type: InAppNotification.NotificationType value
            title: Notification title
            body: Optional body text
            link_url: Optional URL to related resource
            protocol: Optional related protocol
            work_order: Optional related work order
            publish_realtime: Whether to publish event to Sockudo

        Returns:
            InAppNotification: Created notification instance
        """
        notification = InAppNotification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            link_url=link_url or "",
            protocol=protocol,
            work_order=work_order,
        )
        if publish_realtime and getattr(settings, "SOCKUDO_ENABLED", False):
            channel = f"private-user-{recipient.id}"
            payload = {"type": "notification.created", "id": notification.id}
            success = _publish_to_sockudo(
                channel, "notification.created", payload
            )
            logger.info(
                "Notification created",
                extra={
                    "notification_id": notification.id,
                    "recipient_id": recipient.id,
                    "realtime_published": success,
                },
            )
        return notification

    def create_for_protocol_submitted(self, protocol) -> InAppNotification:
        """Create notification when protocol is submitted."""
        user = protocol.veterinarian.user
        link = _build_protocol_url(protocol)
        return self.create_notification(
            recipient=user,
            notification_type=InAppNotification.NotificationType.SUBMITTED,
            title=f"Protocolo {protocol.temporary_code} enviado",
            body="Su protocolo ha sido enviado correctamente. Incluya el código con su muestra.",
            link_url=link,
            protocol=protocol,
        )

    def create_for_reception(self, protocol) -> InAppNotification:
        """Create notification when sample is received."""
        user = protocol.veterinarian.user
        link = _build_protocol_url(protocol)
        return self.create_notification(
            recipient=user,
            notification_type=InAppNotification.NotificationType.RECEPTION,
            title=f"Muestra recibida - {protocol.protocol_number}",
            body="Hemos recibido su muestra. Puede seguir el estado en el portal.",
            link_url=link,
            protocol=protocol,
        )

    def create_for_rejection(self, protocol) -> InAppNotification:
        """Create notification when sample is rejected."""
        user = protocol.veterinarian.user
        link = _build_protocol_url(protocol)
        return self.create_notification(
            recipient=user,
            notification_type=InAppNotification.NotificationType.REJECTION,
            title=f"Muestra rechazada - {protocol.protocol_number}",
            body="Su muestra fue rechazada. Contacte al laboratorio para coordinar el reenvío.",
            link_url=link,
            protocol=protocol,
        )

    def create_for_discrepancy(
        self, protocol, discrepancies: str
    ) -> InAppNotification:
        """Create notification when reception has discrepancies."""
        user = protocol.veterinarian.user
        link = _build_protocol_url(protocol)
        return self.create_notification(
            recipient=user,
            notification_type=InAppNotification.NotificationType.DISCREPANCY,
            title=f"Discrepancias - {protocol.protocol_number}",
            body=discrepancies[:500]
            if discrepancies
            else "Se encontraron discrepancias.",
            link_url=link,
            protocol=protocol,
        )

    def create_for_ready(self, protocol) -> InAppNotification:
        """Create notification when sample is ready for diagnosis."""
        user = protocol.veterinarian.user
        link = _build_protocol_url(protocol)
        return self.create_notification(
            recipient=user,
            notification_type=InAppNotification.NotificationType.READY,
            title=f"Muestra lista - {protocol.protocol_number}",
            body="Su muestra está lista para diagnóstico. El informe estará disponible pronto.",
            link_url=link,
            protocol=protocol,
        )

    def create_for_report_ready(self, protocol) -> InAppNotification:
        """Create notification when report is ready."""
        user = protocol.veterinarian.user
        link = _build_protocol_url(protocol)
        return self.create_notification(
            recipient=user,
            notification_type=InAppNotification.NotificationType.REPORT_READY,
            title=f"Informe disponible - {protocol.protocol_number}",
            body="Su informe histopatológico está disponible para descargar.",
            link_url=link,
            protocol=protocol,
        )

    def create_for_work_order(
        self, work_order, veterinarian_user
    ) -> InAppNotification:
        """Create notification for work order (one per veterinarian)."""
        link = _build_workorder_url(work_order)
        return self.create_notification(
            recipient=veterinarian_user,
            notification_type=InAppNotification.NotificationType.WORK_ORDER,
            title=f"Orden de trabajo - {work_order.order_number}",
            body="Se ha generado una orden de trabajo. Puede ver el detalle en el portal.",
            link_url=link,
            work_order=work_order,
        )

    def create_test_notification(
        self, recipient, message: str = ""
    ) -> InAppNotification:
        """Create a test notification (for admin action)."""
        return self.create_notification(
            recipient=recipient,
            notification_type=InAppNotification.NotificationType.CUSTOM,
            title="Notificación de prueba",
            body=message or "Esta es una notificación de prueba del sistema.",
            link_url="",
        )


def _build_protocol_url(protocol) -> str:
    """Build absolute URL for protocol public detail."""
    path = reverse(
        "protocols:protocol_public_detail",
        kwargs={"external_id": protocol.external_id},
    )
    return f"{settings.SITE_URL}{path}"


def _build_workorder_url(work_order) -> str:
    """Build absolute URL for work order detail."""
    path = reverse(
        "protocols:workorder_detail",
        kwargs={"pk": work_order.pk},
    )
    return f"{settings.SITE_URL}{path}"
