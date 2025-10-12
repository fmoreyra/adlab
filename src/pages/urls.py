from django.urls import path

from pages import views

app_name = "pages"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path(
        "dashboard/veterinarian/",
        views.veterinarian_dashboard,
        name="dashboard_veterinarian",
    ),
    path(
        "dashboard/lab-staff/",
        views.lab_staff_dashboard,
        name="dashboard_lab_staff",
    ),
    path(
        "dashboard/histopathologist/",
        views.histopathologist_dashboard,
        name="dashboard_histopathologist",
    ),
    path("dashboard/admin/", views.admin_dashboard, name="dashboard_admin"),
]
