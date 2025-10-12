from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path(
        "password-reset/",
        views.password_reset_request_view,
        name="password_reset_request",
    ),
    path(
        "password-reset/confirm/<str:token>/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
    # Email Verification
    path(
        "verify-email/<str:token>/",
        views.verify_email_view,
        name="verify_email",
    ),
    path(
        "resend-verification/",
        views.resend_verification_view,
        name="resend_verification",
    ),
    # User Profile (Generic)
    path("profile/", views.profile_view, name="profile"),
    # Veterinarian Profile
    path(
        "veterinarian/complete-profile/",
        views.complete_profile_view,
        name="complete_profile",
    ),
    path(
        "veterinarian/profile/",
        views.veterinarian_profile_detail_view,
        name="veterinarian_profile_detail",
    ),
    path(
        "veterinarian/profile/edit/",
        views.veterinarian_profile_edit_view,
        name="veterinarian_profile_edit",
    ),
    path(
        "veterinarian/profile/history/",
        views.veterinarian_profile_history_view,
        name="veterinarian_profile_history",
    ),
]
