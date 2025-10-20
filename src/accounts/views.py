import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from .forms import (
    HistopathologistCreationForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    ResendVerificationEmailForm,
    UserLoginForm,
    UserProfileForm,
    VeterinarianProfileCompleteForm,
    VeterinarianProfileEditForm,
    VeterinarianRegistrationForm,
)
from .mixins import AdminRequiredMixin, VeterinarianRequiredMixin
from .models import (
    Address,
    AuthAuditLog,
    PasswordResetToken,
    User,
    Veterinarian,
    VeterinarianChangeLog,
)
from .services.auth_service import AuthenticationService

# =============================================================================
# HELPER FUNCTIONS (REMOVED - REPLACED BY SERVICE CLASSES)
# =============================================================================
# The following helper functions have been moved to service classes:
# - get_client_ip -> AuthenticationService._get_client_ip
# - get_user_agent -> AuthenticationService._get_user_agent
# - send_verification_email -> AuthenticationService.send_verification_email


# =============================================================================
# CLASS-BASED VIEWS
# =============================================================================


class LoginView(FormView):
    """
    User login view with service integration and early returns.
    """

    form_class = UserLoginForm
    template_name = "accounts/login.html"
    success_url = "/dashboard/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthenticationService()

    def get(self, request, *args, **kwargs):
        """Handle GET request with early return for authenticated users."""
        if request.user.is_authenticated:
            return redirect("home")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """Process valid login form with early returns and service integration."""
        # Process login using authentication service
        success, redirect_url, error_message = self.auth_service.process_login(
            form, self.request
        )

        if not success:
            messages.error(self.request, error_message)
            return self.form_invalid(form)

        messages.success(self.request, _("¡Bienvenido!"))

        # Redirect to appropriate URL
        if redirect_url:
            return redirect(redirect_url)

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid login form with service integration."""
        email = form.data.get("username", "N/A")
        self.auth_service.handle_failed_login(email, self.request)
        return super().form_invalid(form)


class HistopathologistLoginView(LoginView):
    """
    Histopathologist login view with no registration link.
    
    Uses the same authentication logic as LoginView but displays
    a different template without the registration section.
    """

    template_name = "accounts/histopathologist_login.html"


class RegisterView(CreateView):
    """
    User registration view.
    """

    model = User
    form_class = VeterinarianRegistrationForm
    template_name = "accounts/register.html"
    success_url = "/accounts/login/"

    def form_valid(self, form):
        """Process valid registration form."""
        user = form.save(commit=False)
        user.is_active = False  # Require email verification
        user.save()

        # Send verification email using service
        auth_service = AuthenticationService()
        if auth_service.send_verification_email(user, self.request):
            # Log email verification sent
            AuthAuditLog.objects.create(
                user=user,
                email=user.email,
                action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                ip_address=auth_service._get_client_ip(self.request),
                user_agent=auth_service._get_user_agent(self.request),
            )
            messages.success(
                self.request,
                _(
                    "Registro exitoso. Por favor verifique su email para activar su cuenta."
                ),
            )
        else:
            messages.error(
                self.request,
                _(
                    "Error al enviar email de verificación. Contacte al administrador."
                ),
            )

        return super().form_valid(form)


class CreateHistopathologistView(AdminRequiredMixin, FormView):
    """
    View for creating histopathologist users with complete profile.
    
    Creates both User account and Histopathologist profile in a single form.
    Only accessible by administrators and superusers.
    """

    form_class = HistopathologistCreationForm
    template_name = "accounts/create_histopathologist.html"
    success_url = reverse_lazy("admin:accounts_histopathologist_changelist")

    def form_valid(self, form):
        """Process valid form and create histopathologist."""
        try:
            user, _ = form.save()
            
            # Log creation in audit log
            auth_service = AuthenticationService()
            AuthAuditLog.objects.create(
                user=user,
                email=user.email,
                action=AuthAuditLog.Action.USER_CREATED,
                ip_address=auth_service._get_client_ip(self.request),
                user_agent=auth_service._get_user_agent(self.request),
                details=f"Histopathologist created by {self.request.user.email}",
            )
            
            messages.success(
                self.request,
                f"Histopatólogo {user.get_full_name()} creado exitosamente. "
                f"Email: {user.email}"
            )
            
        except Exception:
            messages.error(
                self.request,
                _("Error al crear el histopatólogo. Intente nuevamente."),
            )
            return self.form_invalid(form)
        
        return super().form_valid(form)


class PasswordResetRequestView(FormView):
    """
    Password reset request view.
    """

    form_class = PasswordResetRequestForm
    template_name = "accounts/password_reset_request.html"
    success_url = "/accounts/login/"

    def form_valid(self, form):
        """Process valid password reset request."""
        email = form.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
            # Create password reset token
            token = PasswordResetToken.objects.create(
                user=user,
                token=secrets.token_urlsafe(32),
                expires_at=timezone.now() + timedelta(hours=24),
            )

            # Send password reset email
            reset_url = self.request.build_absolute_uri(
                reverse(
                    "accounts:password_reset_confirm",
                    kwargs={"token": token.token},
                )
            )

            html_message = render_to_string(
                "accounts/emails/password_reset.html",
                {"user": user, "reset_url": reset_url},
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject="Restablecer contraseña - AdLab",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            messages.success(
                self.request,
                _("Se ha enviado un enlace de restablecimiento a su email."),
            )
        except User.DoesNotExist:
            # Don't reveal if email exists
            messages.success(
                self.request,
                _("Se ha enviado un enlace de restablecimiento a su email."),
            )

        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    """
    Password reset confirmation view.
    """

    form_class = PasswordResetConfirmForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = "/accounts/login/"

    def get_context_data(self, **kwargs):
        """Add token to context."""
        context = super().get_context_data(**kwargs)
        context["token"] = self.kwargs.get("token")
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET request."""
        token = self.kwargs.get("token")
        try:
            PasswordResetToken.objects.get(
                token=token,
                expires_at__gt=timezone.now(),
                used_at__isnull=True,
            )
            return super().get(request, *args, **kwargs)
        except PasswordResetToken.DoesNotExist:
            messages.error(
                request,
                _("El enlace de restablecimiento es inválido o ha expirado."),
            )
            return redirect("accounts:password_reset_request")

    def form_valid(self, form):
        """Process valid password reset confirmation."""
        token = self.kwargs.get("token")
        try:
            reset_token = PasswordResetToken.objects.get(
                token=token,
                expires_at__gt=timezone.now(),
                used_at__isnull=True,
            )

            # Update password
            user = reset_token.user
            user.set_password(form.cleaned_data["password1"])
            user.save()

            # Mark token as used
            reset_token.used_at = timezone.now()
            reset_token.save()

            messages.success(
                self.request,
                _(
                    "Contraseña restablecida exitosamente. Puede iniciar sesión ahora."
                ),
            )

            return super().form_valid(form)
        except PasswordResetToken.DoesNotExist:
            messages.error(
                self.request,
                _("El enlace de restablecimiento es inválido o ha expirado."),
            )
            return redirect("accounts:password_reset_request")


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    User profile view.
    """

    model = User
    form_class = UserProfileForm
    template_name = "accounts/profile.html"
    success_url = "/accounts/profile/"

    def get(self, request, *args, **kwargs):
        """Handle GET request with role-based redirects."""
        user = request.user
        
        # Redirect veterinarians to their specific profile view
        if user.role == User.Role.VETERINARIO:
            return redirect("accounts:veterinarian_profile_detail")
        
        
        # For other roles, show the generic profile view
        return super().get(request, *args, **kwargs)

    def get_object(self):
        """Get the current user."""
        return self.request.user

    def form_valid(self, form):
        """Process valid profile form."""
        messages.success(self.request, _("Perfil actualizado exitosamente."))
        return super().form_valid(form)


class VerifyEmailView(View):
    """
    Email verification view.
    """

    def get(self, request, *args, **kwargs):
        """Handle email verification."""
        token = self.kwargs.get("token")
        auth_service = AuthenticationService()

        try:
            user = User.objects.get(email_verification_token=token)
            if not user.is_verification_token_expired():
                user.verify_email()
                user.is_active = True
                user.save()

                # Log successful email verification
                AuthAuditLog.objects.create(
                    user=user,
                    email=user.email,
                    action=AuthAuditLog.Action.EMAIL_VERIFIED,
                    ip_address=auth_service._get_client_ip(request),
                    user_agent=auth_service._get_user_agent(request),
                )

                messages.success(
                    request,
                    _(
                        "Email verificado exitosamente. Ya puede iniciar sesión."
                    ),
                )
                return redirect("accounts:login")
            else:
                messages.error(
                    request, _("El enlace de verificación ha expirado.")
                )
                return redirect("accounts:resend_verification")
        except User.DoesNotExist:
            messages.error(request, _("Enlace de verificación inválido."))
            return redirect("accounts:login")


class ResendVerificationView(FormView):
    """
    Resend email verification view.
    """

    form_class = ResendVerificationEmailForm
    template_name = "accounts/resend_verification.html"
    success_url = "/accounts/login/"

    def get(self, request, *args, **kwargs):
        """Handle GET request."""
        if request.user.is_authenticated and not request.user.is_active:
            # Resend verification for current user
            auth_service = AuthenticationService()
            if auth_service.send_verification_email(request.user, request):
                messages.success(
                    request, _("Email de verificación reenviado.")
                )
            else:
                messages.error(
                    request, _("Error al reenviar email de verificación.")
                )
            return redirect("accounts:login")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """Process valid resend verification form."""
        email = form.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
            # Send verification email for inactive users or unverified veterinarians
            if not user.is_active or (
                user.role == User.Role.VETERINARIO and not user.email_verified
            ):
                auth_service = AuthenticationService()
                auth_service.send_verification_email(user, self.request)

                # Log verification email sent
                AuthAuditLog.objects.create(
                    user=user,
                    email=email,
                    action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                    ip_address=auth_service._get_client_ip(self.request),
                    user_agent=auth_service._get_user_agent(self.request),
                    details="Verification email resent",
                )
        except User.DoesNotExist:
            pass  # Don't reveal if email exists

        # Always show same message for security
        messages.success(
            self.request,
            _(
                "Si el email existe, se ha reenviado un enlace de verificación."
            ),
        )
        return super().form_valid(form)


class CompleteProfileView(LoginRequiredMixin, FormView):
    """
    Complete veterinarian profile view.
    """

    form_class = VeterinarianProfileCompleteForm
    template_name = "accounts/complete_profile.html"
    success_url = reverse_lazy("pages:dashboard")

    def get(self, request, *args, **kwargs):
        """Handle GET request with validation."""
        # Check if user is a veterinarian
        if not request.user.is_veterinarian:
            messages.error(
                request, _("Solo los veterinarios pueden completar su perfil.")
            )
            return redirect("home")

        # Check if profile is already complete
        if hasattr(request.user, "veterinarian_profile"):
            messages.info(request, _("Su perfil ya está completo."))
            return redirect("accounts:veterinarian_profile_detail")

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Add user to form kwargs and remove instance."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        # Remove 'instance' if present (CreateView passes this but Form doesn't need it)
        kwargs.pop("instance", None)
        return kwargs

    def form_valid(self, form):
        """Process valid profile completion form."""
        # Create veterinarian profile and address
        form.save()

        messages.success(self.request, _("Perfil completado exitosamente."))

        return super().form_valid(form)


class VeterinarianProfileDetailView(VeterinarianRequiredMixin, DetailView):
    """
    Veterinarian profile detail view.
    """

    model = User
    template_name = "accounts/veterinarian_profile_detail.html"
    context_object_name = "veterinarian_user"

    def get(self, request, *args, **kwargs):
        """Handle GET request with validation."""
        if not hasattr(request.user, "veterinarian_profile"):
            messages.error(request, _("No tiene un perfil de veterinario."))
            return redirect("accounts:complete_profile")
        return super().get(request, *args, **kwargs)

    def get_object(self):
        """Get the veterinarian user."""
        return self.request.user

    def get_context_data(self, **kwargs):
        """Add veterinarian profile to context."""
        context = super().get_context_data(**kwargs)
        veterinarian = self.request.user.veterinarian_profile
        context["veterinarian"] = veterinarian
        context["profile_completeness"] = veterinarian.profile_completeness
        return context


class VeterinarianProfileEditView(VeterinarianRequiredMixin, UpdateView):
    """
    Veterinarian profile edit view.
    """

    model = Veterinarian
    form_class = VeterinarianProfileEditForm
    template_name = "accounts/veterinarian_profile_edit.html"
    success_url = "/accounts/profile/"

    def get_object(self):
        """Get the current user's veterinarian profile."""
        return self.request.user.veterinarian_profile

    def get_context_data(self, **kwargs):
        """Add form as vet_form to context."""
        context = super().get_context_data(**kwargs)
        context["vet_form"] = context["form"]
        return context

    def form_valid(self, form):
        """Process valid profile edit form."""
        # Get the veterinarian profile and address
        veterinarian = self.request.user.veterinarian_profile

        # Get old values for change logging from form's initial data
        old_values = form.initial.copy()

        # Get address values from the current address
        try:
            address = veterinarian.address
            old_values.update(
                {
                    "province": address.province or "",
                    "locality": address.locality or "",
                    "street": address.street or "",
                    "number": address.number or "",
                    "floor": address.floor or "",
                    "apartment": address.apartment or "",
                    "postal_code": address.postal_code or "",
                    "notes": address.notes or "",
                }
            )
        except Address.DoesNotExist:
            old_values.update(
                {
                    "province": "",
                    "locality": "",
                    "street": "",
                    "number": "",
                    "floor": "",
                    "apartment": "",
                    "postal_code": "",
                    "notes": "",
                }
            )

        # Log changes BEFORE saving
        for field_name, new_value in form.cleaned_data.items():
            old_value = old_values.get(field_name, "")
            # Convert both to strings for comparison to avoid type mismatches
            old_value_str = str(old_value) if old_value is not None else ""
            new_value_str = str(new_value) if new_value is not None else ""
            if old_value_str != new_value_str:
                VeterinarianChangeLog.objects.create(
                    veterinarian=veterinarian,
                    changed_by=self.request.user,
                    field_name=field_name,
                    old_value=old_value_str,
                    new_value=new_value_str,
                )

        messages.success(self.request, _("Perfil actualizado exitosamente."))
        # Save the form (this will update both veterinarian and address)
        return super().form_valid(form)


class VeterinarianProfileHistoryView(VeterinarianRequiredMixin, ListView):
    """
    Veterinarian profile history view.
    """

    model = VeterinarianChangeLog
    template_name = "accounts/veterinarian_profile_history.html"
    context_object_name = "change_logs"
    paginate_by = 20

    def get_queryset(self):
        """Get change logs for current user's veterinarian profile."""
        return VeterinarianChangeLog.objects.filter(
            veterinarian=self.request.user.veterinarian_profile
        ).order_by("-changed_at")


# =============================================================================
# FUNCTION-BASED VIEWS
# =============================================================================


def logout_view(request):
    """Handle user logout with audit logging using service."""
    auth_service = AuthenticationService()

    # Log logout action
    AuthAuditLog.objects.create(
        user=request.user,
        email=request.user.email,
        action=AuthAuditLog.Action.LOGOUT,
        ip_address=auth_service._get_client_ip(request),
        user_agent=auth_service._get_user_agent(request),
    )

    logout(request)
    messages.success(request, _("Ha cerrado sesión exitosamente."))
    return redirect(settings.LOGOUT_REDIRECT_URL)
