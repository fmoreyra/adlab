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
from django.utils.decorators import method_decorator
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
from django_ratelimit.decorators import ratelimit

from .forms import (
    LaboratoryStaffCreationForm,
    LaboratoryStaffSignatureForm,
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
from .rate_limit import (
    LOGIN_RATE,
    PASSWORD_RESET_RATE,
    REGISTER_RATE,
    RESEND_VERIFICATION_RATE,
    RateLimitedFormMixin,
    ratelimit_post,
)
from .redirect_utils import resolve_safe_redirect
from .report_access import get_or_create_laboratory_staff_profile
from .services.auth_service import AuthenticationService
from .services.turnstile_service import get_turnstile_site_key

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


@ratelimit_post(key="ip", rate=LOGIN_RATE)
class LoginView(RateLimitedFormMixin, FormView):
    """
    User login view with service integration and early returns.
    """

    form_class = UserLoginForm
    template_name = "accounts/login.html"
    success_url = "/dashboard/"
    rate_limit_message = _(
        "Demasiados intentos de inicio de sesión. "
        "Por favor espere unos minutos e intente de nuevo."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_service = AuthenticationService()

    def get(self, request, *args, **kwargs):
        """Handle GET request with early return for authenticated users."""
        if request.user.is_authenticated:
            next_url = resolve_safe_redirect(
                request,
                request.GET.get("next"),
                default=reverse("pages:dashboard"),
            )
            return redirect(next_url)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Expose ``next`` for login form action and hidden field."""
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.request.GET.get("next", "")
        return context

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


@ratelimit_post(key="ip", rate=REGISTER_RATE)
class RegisterView(RateLimitedFormMixin, CreateView):
    """
    User registration view.
    """

    model = User
    form_class = VeterinarianRegistrationForm
    template_name = "accounts/register.html"
    success_url = "/accounts/login/"
    rate_limit_message = _(
        "Demasiados intentos de registro. "
        "Por favor espere e intente de nuevo más tarde."
    )

    def get_form_kwargs(self):
        """Pass request to registration form for Turnstile validation."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        """Expose Turnstile site key when configured."""
        context = super().get_context_data(**kwargs)
        context["turnstile_site_key"] = get_turnstile_site_key()
        return context

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


class CreateLaboratoryStaffView(AdminRequiredMixin, FormView):
    """
    View for creating laboratory staff with unified profile.

    Creates User account and LaboratoryStaff profile, sends verification
    email, and logs the creation. Only accessible by administrators.
    """

    form_class = LaboratoryStaffCreationForm
    template_name = "accounts/create_laboratory_staff.html"
    success_url = reverse_lazy("admin:accounts_laboratorystaff_changelist")

    def form_valid(self, form):
        """Process valid form and create laboratory staff."""
        try:
            user, lab_staff = form.save()
            auth_service = AuthenticationService()

            AuthAuditLog.objects.create(
                user=user,
                email=user.email,
                action=AuthAuditLog.Action.USER_CREATED,
                ip_address=auth_service._get_client_ip(self.request),
                user_agent=auth_service._get_user_agent(self.request),
                details=(
                    f"Laboratory staff created by {self.request.user.email}"
                ),
            )

            if auth_service.send_verification_email(user, self.request):
                AuthAuditLog.objects.create(
                    user=user,
                    email=user.email,
                    action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                    ip_address=auth_service._get_client_ip(self.request),
                    user_agent=auth_service._get_user_agent(self.request),
                )
                verification_note = _(
                    " Se envió un email de verificación al empleado."
                )
            else:
                verification_note = _(
                    " No se pudo enviar el email de verificación; "
                    "verifique la configuración SMTP."
                )

            signature_note = ""
            if not lab_staff.has_signature():
                signature_note = _(
                    " Deberá cargar su firma digital en el primer ingreso."
                )

            messages.success(
                self.request,
                _(
                    "Personal de laboratorio %(name)s creado exitosamente. "
                    "Email: %(email)s.%(verification)s%(signature)s"
                )
                % {
                    "name": user.get_full_name(),
                    "email": user.email,
                    "verification": verification_note,
                    "signature": signature_note,
                },
            )

        except Exception:
            messages.error(
                self.request,
                _(
                    "Error al crear el personal de laboratorio. "
                    "Intente nuevamente."
                ),
            )
            return self.form_invalid(form)

        return super().form_valid(form)


def redirect_create_histopathologist(request):
    """Redirect legacy histopathologist creation URL to unified staff flow."""
    return redirect("accounts:create_laboratory_staff", permanent=True)


@ratelimit_post(key="ip", rate=PASSWORD_RESET_RATE)
class PasswordResetRequestView(RateLimitedFormMixin, FormView):
    """
    Password reset request view.
    """

    form_class = PasswordResetRequestForm
    template_name = "accounts/password_reset_request.html"
    success_url = "/accounts/login/"
    rate_limit_message = _(
        "Demasiados intentos de restablecimiento de contraseña. "
        "Por favor espere e intente de nuevo más tarde."
    )

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

            from protocols.emails import (
                prepare_outbound_email,
                record_sent_email,
            )
            from protocols.models import EmailLog

            delivery_email, delivery_subject = prepare_outbound_email(
                user.email, "Restablecer contraseña - AdLab"
            )

            send_mail(
                subject=delivery_subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[delivery_email],
                html_message=html_message,
                fail_silently=False,
            )
            record_sent_email(
                EmailLog.EmailType.PASSWORD_RESET,
                delivery_email,
                delivery_subject,
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


class LabStaffSignatureView(LoginRequiredMixin, FormView):
    """
    Upload digital signature for laboratory staff who create reports.
    """

    form_class = LaboratoryStaffSignatureForm
    template_name = "accounts/lab_staff_signature.html"

    def dispatch(self, request, *args, **kwargs):
        """Only laboratory staff may access the signature upload form."""
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.is_lab_staff:
            messages.error(
                request,
                _("Solo el personal de laboratorio puede cargar una firma."),
            )
            return redirect("pages:dashboard")

        self.lab_staff_profile = get_or_create_laboratory_staff_profile(
            request.user
        )
        if not self.lab_staff_profile:
            messages.error(
                request,
                _("No se encontró un perfil de personal de laboratorio."),
            )
            return redirect("pages:dashboard")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Return to dashboard or the page the user came from."""
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url

        return reverse_lazy("pages:dashboard")

    def get(self, request, *args, **kwargs):
        """Skip form when signature already exists unless forced."""
        # Check the profile image directly: admins are exempted from the
        # onboarding middleware helper but still need this form when unsigned.
        if self.lab_staff_profile.has_signature() and not request.GET.get(
            "force"
        ):
            messages.info(request, _("Su firma digital ya está cargada."))
            return redirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Bind the form to the current user's laboratory staff profile."""
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.lab_staff_profile
        return kwargs

    def get_context_data(self, **kwargs):
        """Expose profile in template for optional preview text."""
        context = super().get_context_data(**kwargs)
        context["object"] = self.lab_staff_profile
        return context

    def form_valid(self, form):
        """Save signature and confirm success."""
        form.save()
        messages.success(
            self.request,
            _("Firma digital guardada. Ya puede continuar con su trabajo."),
        )
        return super().form_valid(form)


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


@method_decorator(
    ratelimit(
        key="ip", rate=RESEND_VERIFICATION_RATE, method="POST", block=False
    ),
    name="post",
)
@method_decorator(
    ratelimit(
        key="post:email",
        rate=RESEND_VERIFICATION_RATE,
        method="POST",
        block=False,
    ),
    name="post",
)
class ResendVerificationView(RateLimitedFormMixin, FormView):
    """
    Resend email verification view.
    """

    form_class = ResendVerificationEmailForm
    template_name = "accounts/resend_verification.html"
    success_url = "/accounts/login/"
    rate_limit_message = _(
        "Demasiados intentos de reenvío de verificación. "
        "Por favor espere e intente de nuevo más tarde."
    )

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
            from django.http import HttpResponseForbidden
            from django.template.loader import render_to_string

            messages.error(
                request, _("Solo los veterinarios pueden completar su perfil.")
            )
            return HttpResponseForbidden(
                render_to_string(
                    "403.html", {"user": request.user}, request=request
                )
            )

        # Redirect only when profile meets the same rules as middleware
        veterinarian = Veterinarian.objects.filter(user=request.user).first()
        if veterinarian and veterinarian.is_profile_complete_for_access():
            messages.info(request, _("Su perfil ya está completo."))
            return redirect("pages:dashboard")

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

        # Add address to context if it exists
        try:
            context["address"] = veterinarian.address
        except Address.DoesNotExist:
            context["address"] = None

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

    # Log logout action only if user is authenticated
    if request.user.is_authenticated:
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
