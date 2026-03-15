"""
Management Dashboard API URLs for Step 09.
Notification API URLs for Step 21.
"""

from django.urls import include, path

from pages import api_views

app_name = "pages_api"

urlpatterns = [
    # Notifications (Step 21)
    path("notifications/", include("protocols.notification_urls")),
    # Dashboard API endpoints
    path(
        "dashboard/wip/",
        api_views.DashboardWIPView.as_view(),
        name="dashboard_wip",
    ),
    path(
        "dashboard/volume/",
        api_views.DashboardVolumeView.as_view(),
        name="dashboard_volume",
    ),
    path(
        "dashboard/tat/",
        api_views.DashboardTATView.as_view(),
        name="dashboard_tat",
    ),
    path(
        "dashboard/productivity/",
        api_views.DashboardProductivityView.as_view(),
        name="dashboard_productivity",
    ),
    path(
        "dashboard/aging/",
        api_views.DashboardAgingView.as_view(),
        name="dashboard_aging",
    ),
    path(
        "dashboard/alerts/",
        api_views.DashboardAlertsView.as_view(),
        name="dashboard_alerts",
    ),
    path(
        "dashboard/server-stats/",
        api_views.ServerStatsView.as_view(),
        name="dashboard_server_stats",
    ),
]
