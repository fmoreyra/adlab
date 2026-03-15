from django.urls import path

from pages import views
from protocols import notification_views

app_name = "pages"

urlpatterns = [
    # Notifications inbox (Step 21) - any authenticated user
    path(
        "notifications/",
        notification_views.NotificationInboxView.as_view(),
        name="notifications_inbox",
    ),
    path(
        "notifications/mark-all-read/",
        notification_views.NotificationMarkAllReadRedirectView.as_view(),
        name="notifications_mark_all_read",
    ),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/veterinarian/",
        views.VeterinarianDashboardView.as_view(),
        name="dashboard_veterinarian",
    ),
    path(
        "dashboard/lab-staff/",
        views.LabStaffDashboardView.as_view(),
        name="dashboard_lab_staff",
    ),
    path(
        "dashboard/admin/",
        views.AdminDashboardView.as_view(),
        name="dashboard_admin",
    ),
    path(
        "dashboard/management/",
        views.ManagementDashboardView.as_view(),
        name="dashboard_management",
    ),
]
