from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "histopathologist/login/",
        views.HistopathologistLoginView.as_view(),
        name="histopathologist_login",
    ),
    path(
        "logout/", views.logout_view, name="logout"
    ),  # Keep as function (simple redirect)
    path("register/", views.RegisterView.as_view(), name="register"),
    path(
        "password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/confirm/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Email Verification
    path(
        "verify-email/<str:token>/",
        views.VerifyEmailView.as_view(),
        name="verify_email",
    ),
    path(
        "resend-verification/",
        views.ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    # User Profile (Generic)
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Veterinarian Profile
    path(
        "veterinarian/complete-profile/",
        views.CompleteProfileView.as_view(),
        name="complete_profile",
    ),
    path(
        "veterinarian/profile/",
        views.VeterinarianProfileDetailView.as_view(),
        name="veterinarian_profile_detail",
    ),
    path(
        "veterinarian/profile/edit/",
        views.VeterinarianProfileEditView.as_view(),
        name="veterinarian_profile_edit",
    ),
    path(
        "veterinarian/profile/history/",
        views.VeterinarianProfileHistoryView.as_view(),
        name="veterinarian_profile_history",
    ),
    # Histopathologist Management
    path(
        "histopathologist/create/",
        views.CreateHistopathologistView.as_view(),
        name="create_histopathologist",
    ),
]
