"""
Notification API URLs (Step 21).
"""

from django.urls import path

from protocols import notification_views

app_name = "notifications"

urlpatterns = [
    path("", notification_views.NotificationListView.as_view(), name="list"),
    path(
        "unread-count/",
        notification_views.NotificationUnreadCountView.as_view(),
        name="unread_count",
    ),
    path(
        "read-all/",
        notification_views.NotificationMarkAllReadView.as_view(),
        name="read_all",
    ),
    path(
        "realtime-auth/",
        notification_views.RealtimeAuthView.as_view(),
        name="realtime_auth",
    ),
    path(
        "<int:pk>/read/",
        notification_views.NotificationMarkReadView.as_view(),
        name="mark_read",
    ),
]
