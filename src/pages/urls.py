from django.urls import path

from pages import views

app_name = "pages"

urlpatterns = [
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
