"""
In-app notification API views (Step 21).

Provides endpoints for bandeja (inbox), mark as read, unread count,
and realtime channel authentication.
"""

import hmac
import json
import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from protocols.models import InAppNotification

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class NotificationListView(LoginRequiredMixin, View):
    """List notifications for the current user."""

    def get(self, request, *args, **kwargs):
        """Return paginated list of notifications."""
        user = request.user
        filter_type = request.GET.get("filter", "all")  # all, unread, read
        page = int(request.GET.get("page", 1))
        per_page = min(int(request.GET.get("per_page", 20)), 50)
        offset = (page - 1) * per_page

        qs = InAppNotification.objects.filter(recipient=user).order_by(
            "-created_at"
        )
        if filter_type == "unread":
            qs = qs.filter(is_read=False)
        elif filter_type == "read":
            qs = qs.filter(is_read=True)

        total = qs.count()
        notifications = list(
            qs[offset : offset + per_page].values(
                "id",
                "notification_type",
                "title",
                "body",
                "link_url",
                "is_read",
                "read_at",
                "created_at",
            )
        )
        for n in notifications:
            n["created_at"] = n["created_at"].isoformat()
            n["read_at"] = n["read_at"].isoformat() if n["read_at"] else None

        return JsonResponse(
            {
                "notifications": notifications,
                "total": total,
                "page": page,
                "per_page": per_page,
            }
        )


class NotificationMarkReadView(LoginRequiredMixin, View):
    """Mark a single notification as read."""

    def post(self, request, pk, *args, **kwargs):
        """Mark notification as read if it belongs to the user."""
        user = request.user
        notification = InAppNotification.objects.filter(
            pk=pk, recipient=user
        ).first()
        if not notification:
            return JsonResponse(
                {"error": "Notificación no encontrada"}, status=404
            )
        notification.mark_as_read()
        return JsonResponse({"ok": True})


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""

    def post(self, request, *args, **kwargs):
        """Mark all user notifications as read."""
        user = request.user
        updated = InAppNotification.objects.filter(
            recipient=user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return JsonResponse({"ok": True, "updated": updated})


class NotificationUnreadCountView(LoginRequiredMixin, View):
    """Return unread notification count for badge."""

    def get(self, request, *args, **kwargs):
        """Return count of unread notifications."""
        user = request.user
        count = InAppNotification.objects.filter(
            recipient=user, is_read=False
        ).count()
        return JsonResponse({"count": count})


class RealtimeAuthView(LoginRequiredMixin, View):
    """
    Authenticate private channel subscription (Pusher format).

    Only signs channel_name if it equals private-user-{request.user.id}.
    """

    def post(self, request, *args, **kwargs):
        """Return auth signature for valid private-user channel."""
        user = request.user
        socket_id = request.POST.get("socket_id")
        channel_name = request.POST.get("channel_name")
        if not socket_id and request.body:
            try:
                data = json.loads(request.body)
                socket_id = data.get("socket_id")
                channel_name = data.get("channel_name")
            except json.JSONDecodeError:
                pass

        if not socket_id or not channel_name:
            return JsonResponse(
                {"error": "socket_id and channel_name required"},
                status=400,
            )

        expected_channel = f"private-user-{user.id}"
        if channel_name != expected_channel:
            logger.warning(
                "Realtime auth rejected: channel mismatch",
                extra={
                    "user_id": user.id,
                    "channel_name": channel_name,
                    "expected": expected_channel,
                    "ip": _get_client_ip(request),
                },
            )
            return JsonResponse({"error": "Unauthorized channel"}, status=403)

        app_key = settings.SOCKUDO_APP_KEY
        app_secret = settings.SOCKUDO_APP_SECRET.encode("utf-8")
        string_to_sign = f"{socket_id}:{channel_name}"
        signature = hmac.new(
            app_secret, string_to_sign.encode("utf-8"), "sha256"
        ).hexdigest()
        auth = f"{app_key}:{signature}"

        logger.info(
            "Realtime auth granted",
            extra={
                "user_id": user.id,
                "channel_name": channel_name,
                "ip": _get_client_ip(request),
            },
        )

        return JsonResponse({"auth": auth})


class NotificationInboxView(LoginRequiredMixin, ListView):
    """
    Full-page inbox for all user notifications (paginated).

    Accessible by any authenticated user. Supports filter: all, unread, read.
    """

    model = InAppNotification
    template_name = "protocols/notifications/inbox.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        """Filter by recipient and optional read status."""
        qs = InAppNotification.objects.filter(
            recipient=self.request.user
        ).order_by("-created_at")
        filter_type = self.request.GET.get("filter", "all")
        if filter_type == "unread":
            qs = qs.filter(is_read=False)
        elif filter_type == "read":
            qs = qs.filter(is_read=True)
        return qs

    def get_context_data(self, **kwargs):
        """Add current filter to context."""
        context = super().get_context_data(**kwargs)
        context["filter"] = self.request.GET.get("filter", "all")
        return context


class NotificationMarkAllReadRedirectView(LoginRequiredMixin, View):
    """
    Mark all user notifications as read and redirect to inbox.

    Used by the inbox page form (server-side, no JS required).
    """

    def post(self, request, *args, **kwargs):
        """Mark all as read and redirect back to inbox."""
        InAppNotification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return redirect("pages:notifications_inbox")
