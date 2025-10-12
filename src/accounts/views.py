import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from .forms import (
    AddressForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    UserLoginForm,
    UserProfileForm,
    VeterinarianProfileCompleteForm,
    VeterinarianProfileForm,
    VeterinarianRegistrationForm,
)
from .models import (
    Address,
    AuthAuditLog,
    PasswordResetToken,
    User,
    VeterinarianChangeLog,
)


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(request):
    """Get the user agent from the request."""
    return request.META.get("HTTP_USER_AGENT", "")


def send_verification_email(request, user):
    """
    Send email verification to user.

    Args:
        request: HTTP request object (for building absolute URI)
        user: User object to send verification to

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    token = user.generate_email_verification_token()
    verification_url = request.build_absolute_uri(
        f"/accounts/verify-email/{token}/"
    )

    html_message = render_to_string(
        "accounts/emails/email_verification.html",
        {"user": user, "verification_url": verification_url},
    )
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject="Verifique su email - AdLab",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception:
        return False


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_view(request):
    """Handle user login with audit logging and account lockout."""
    # Early return: already authenticated
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    # GET request: show form
    if request.method != "POST":
        return render(
            request, "accounts/login.html", {"form": UserLoginForm()}
        )

    # POST request: process login
    form = UserLoginForm(request, data=request.POST)
    email = request.POST.get("username", "").lower()

    # Check pre-authentication conditions
    user = User.objects.filter(email=email).first()

    if user:
        # Early return: account locked
        if user.is_locked_out():
            _log_failed_login(request, email, user, "Account is locked")
            messages.error(
                request,
                _(
                    "Su cuenta está bloqueada. Por favor contacte al administrador."
                ),
            )
            return render(request, "accounts/login.html", {"form": form})

        # Early return: account inactive
        if not user.is_active:
            _log_failed_login(request, email, user, "Account is inactive")
            messages.error(request, _("Esta cuenta está desactivada."))
            return render(request, "accounts/login.html", {"form": form})

    # Validate form (also authenticates internally)
    if not form.is_valid():
        # Form validation failed (wrong password or other error)
        _handle_failed_login(request, email, user)
        return render(request, "accounts/login.html", {"form": form})

    # Get authenticated user from form
    authenticated_user = form.get_user()

    # Early return: email not verified
    if not authenticated_user.can_login():
        _log_failed_login(
            request, email, authenticated_user, "Email not verified"
        )
        messages.error(
            request,
            _(
                "Por favor verifique su email antes de iniciar sesión. "
                '¿No recibió el email? <a href="/accounts/resend-verification/" '
                'class="font-medium underline">Reenviar</a>'
            ),
        )
        return render(request, "accounts/login.html", {"form": form})

    # Success: login user
    return _handle_successful_login(request, authenticated_user, form)


def _log_failed_login(request, email, user, details):
    """Helper to log failed login attempts."""
    AuthAuditLog.log(
        action=AuthAuditLog.Action.LOGIN_FAILED,
        email=email,
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details=details,
    )


def _handle_failed_login(request, email, user):
    """Handle failed login attempt with lockout logic."""
    if user:
        user.increment_failed_login_attempts()
        remaining_attempts = 5 - user.failed_login_attempts

        _log_failed_login(
            request,
            email,
            user,
            f"Failed login attempt {user.failed_login_attempts}/5",
        )

        if user.is_locked_out():
            AuthAuditLog.log(
                action=AuthAuditLog.Action.ACCOUNT_LOCKED,
                email=email,
                user=user,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details="Account locked after 5 failed attempts",
            )
            messages.error(
                request,
                _(
                    "Su cuenta ha sido bloqueada. Por favor contacte al administrador."
                ),
            )
        elif remaining_attempts > 0:
            messages.error(
                request,
                _(
                    f"Email o contraseña incorrectos. Le quedan {remaining_attempts} intentos."
                ),
            )
        else:
            messages.error(request, _("Email o contraseña incorrectos."))
    else:
        _log_failed_login(request, email, None, "User does not exist")
        messages.error(request, _("Email o contraseña incorrectos."))


def _handle_successful_login(request, user, form):
    """Handle successful login."""
    # Reset failed attempts and update last login
    user.reset_failed_login_attempts()
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])

    # Log success
    AuthAuditLog.log(
        action=AuthAuditLog.Action.LOGIN_SUCCESS,
        email=user.email,
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    # Login user
    login(request, user)

    # Handle "remember me"
    if not form.cleaned_data.get("remember_me"):
        request.session.set_expiry(0)

    messages.success(request, _(f"Bienvenido, {user.get_full_name()}!"))

    # Smart redirect based on user role
    next_url = request.GET.get("next")
    if not next_url:
        if user.is_veterinarian:
            # Veterinarians go to protocol selection
            next_url = reverse("protocols:protocol_select_type")
        elif user.is_lab_staff:
            # Lab staff go to processing dashboard
            next_url = reverse("protocols:processing_dashboard")
        elif user.is_admin_user:
            # Admins go to admin panel
            next_url = reverse("admin:index")
        else:
            # Default to home page
            next_url = settings.LOGIN_REDIRECT_URL

    return redirect(next_url)


@login_required
def logout_view(request):
    """Handle user logout with audit logging."""
    AuthAuditLog.log(
        action=AuthAuditLog.Action.LOGOUT,
        email=request.user.email,
        user=request.user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    logout(request)
    messages.success(request, _("Ha cerrado sesión exitosamente."))
    return redirect(settings.LOGOUT_REDIRECT_URL)


@sensitive_post_parameters()
@csrf_protect
def register_view(request):
    """Handle veterinarian registration."""
    # Early return: already authenticated
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    # GET request: show form
    if request.method != "POST":
        return render(
            request,
            "accounts/register.html",
            {"form": VeterinarianRegistrationForm()},
        )

    # POST request: process registration
    form = VeterinarianRegistrationForm(request.POST)

    # Early return: form invalid
    if not form.is_valid():
        return render(request, "accounts/register.html", {"form": form})

    # Create user and send verification email
    user = form.save()
    send_verification_email(request, user)

    # Log registration
    AuthAuditLog.log(
        action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
        email=user.email,
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details="New veterinarian registration",
    )

    messages.success(
        request,
        _(
            "Registro exitoso. Por favor verifique su email para activar su cuenta. "
            "Revise su carpeta de spam si no lo encuentra."
        ),
    )
    return redirect("accounts:login")


@csrf_protect
def password_reset_request_view(request):
    """Handle password reset request."""
    # GET request: show form
    if request.method != "POST":
        return render(
            request,
            "accounts/password_reset_request.html",
            {"form": PasswordResetRequestForm()},
        )

    # POST request: process reset request
    form = PasswordResetRequestForm(request.POST)

    # Early return: form invalid
    if not form.is_valid():
        return render(
            request, "accounts/password_reset_request.html", {"form": form}
        )

    email = form.cleaned_data["email"].lower()
    user = User.objects.filter(email=email, is_active=True).first()

    if user:
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(
            seconds=settings.PASSWORD_RESET_TIMEOUT
        )

        PasswordResetToken.objects.create(
            user=user, token=token, expires_at=expires_at
        )

        # Send reset email
        reset_url = request.build_absolute_uri(
            f"/accounts/password-reset/confirm/{token}/"
        )
        html_message = render_to_string(
            "accounts/emails/password_reset.html",
            {
                "user": user,
                "reset_url": reset_url,
                "expiry_hours": settings.PASSWORD_RESET_TIMEOUT // 3600,
            },
        )

        send_mail(
            subject="Restablecer contraseña - AdLab",
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Log request
        AuthAuditLog.log(
            action=AuthAuditLog.Action.PASSWORD_RESET_REQUEST,
            email=user.email,
            user=user,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

    # Always show success (security: don't reveal if email exists)
    messages.success(
        request,
        _("Si el email existe en nuestro sistema, recibirá instrucciones."),
    )
    return redirect("accounts:login")


@sensitive_post_parameters()
@csrf_protect
def password_reset_confirm_view(request, token):
    """Handle password reset confirmation."""
    # Validate token
    reset_token = PasswordResetToken.objects.filter(token=token).first()

    # Early return: token invalid
    if not reset_token:
        messages.error(request, _("Enlace de restablecimiento inválido."))
        return redirect("accounts:password_reset_request")

    # Early return: token expired or used
    if not reset_token.is_valid():
        messages.error(
            request, _("Este enlace ha expirado o ya fue utilizado.")
        )
        return redirect("accounts:password_reset_request")

    # GET request: show form
    if request.method != "POST":
        return render(
            request,
            "accounts/password_reset_confirm.html",
            {
                "form": PasswordResetConfirmForm(),
                "token": token,
            },
        )

    # POST request: process password reset
    form = PasswordResetConfirmForm(request.POST)

    # Early return: form invalid
    if not form.is_valid():
        return render(
            request,
            "accounts/password_reset_confirm.html",
            {"form": form, "token": token},
        )

    # Update password
    user = reset_token.user
    user.set_password(form.cleaned_data["password1"])
    user.failed_login_attempts = 0
    user.save()

    # Mark token as used
    reset_token.mark_as_used()

    # Log password reset
    AuthAuditLog.log(
        action=AuthAuditLog.Action.PASSWORD_RESET_COMPLETE,
        email=user.email,
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    messages.success(
        request,
        _("Su contraseña ha sido actualizada. Ya puede iniciar sesión."),
    )
    return redirect("accounts:login")


@login_required
def profile_view(request):
    """Display and update user profile."""
    # GET request: show form
    if request.method != "POST":
        return render(
            request,
            "accounts/profile.html",
            {"form": UserProfileForm(instance=request.user)},
        )

    # POST request: update profile
    form = UserProfileForm(request.POST, instance=request.user)

    # Early return: form invalid
    if not form.is_valid():
        return render(request, "accounts/profile.html", {"form": form})

    form.save()
    messages.success(request, _("Perfil actualizado exitosamente."))
    return redirect("accounts:profile")


@csrf_protect
def verify_email_view(request, token):
    """Verify user email with token."""
    # Find user by token
    user = User.objects.filter(
        email_verification_token=token,
        email_verified=False,
    ).first()

    # Early return: invalid token
    if not user:
        AuthAuditLog.log(
            action=AuthAuditLog.Action.EMAIL_VERIFICATION_FAILED,
            email="unknown",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details=f"Invalid token: {token[:20]}...",
        )
        messages.error(
            request, _("Enlace de verificación inválido o ya utilizado.")
        )
        return redirect("accounts:login")

    # Early return: token expired
    if user.is_verification_token_expired():
        AuthAuditLog.log(
            action=AuthAuditLog.Action.EMAIL_VERIFICATION_FAILED,
            email=user.email,
            user=user,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details="Token expired",
        )
        messages.error(
            request,
            _("Este enlace ha expirado. Por favor solicite uno nuevo."),
        )
        return redirect("accounts:resend_verification")

    # Verify email
    user.verify_email()

    # Log success
    AuthAuditLog.log(
        action=AuthAuditLog.Action.EMAIL_VERIFIED,
        email=user.email,
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details="Email verified successfully",
    )

    messages.success(
        request, _("¡Email verificado exitosamente! Ya puede iniciar sesión.")
    )
    return redirect("accounts:login")


@csrf_protect
def resend_verification_view(request):
    """Request new verification email."""
    # GET request: show form
    if request.method != "POST":
        return render(request, "accounts/resend_verification.html")

    # POST request: resend verification
    email = request.POST.get("email", "").lower()

    user = User.objects.filter(
        email=email,
        role=User.Role.VETERINARIO,
        email_verified=False,
        is_active=True,
    ).first()

    if user:
        send_verification_email(request, user)
        AuthAuditLog.log(
            action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
            email=user.email,
            user=user,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details="Verification email resent",
        )
        messages.success(
            request,
            _("Email de verificación reenviado. Por favor revise su bandeja."),
        )
    else:
        # Security: don't reveal if email exists
        messages.success(
            request,
            _("Si el email existe y no está verificado, recibirá un enlace."),
        )

    return redirect("accounts:login")


# ============================================================================
# VETERINARIAN PROFILE VIEWS
# ============================================================================


@login_required
@csrf_protect
def complete_profile_view(request):
    """
    Complete veterinarian profile after registration.
    Required for veterinarians to submit protocols.
    """
    # Only veterinarians can access this view
    if not request.user.is_veterinarian:
        messages.error(
            request, _("Solo veterinarios pueden completar este perfil.")
        )
        return redirect("/")

    # Check if profile already exists
    if hasattr(request.user, "veterinarian_profile"):
        messages.info(request, _("Su perfil ya está completo."))
        return redirect("accounts:veterinarian_profile_detail")

    # GET request: show form
    if request.method != "POST":
        form = VeterinarianProfileCompleteForm(user=request.user)
        return render(
            request, "accounts/complete_profile.html", {"form": form}
        )

    # POST request: process profile completion
    form = VeterinarianProfileCompleteForm(
        user=request.user, data=request.POST
    )

    # Early return: form invalid
    if not form.is_valid():
        return render(
            request, "accounts/complete_profile.html", {"form": form}
        )

    # Save profile
    form.save()

    # Log profile creation
    AuthAuditLog.log(
        action=AuthAuditLog.Action.EMAIL_VERIFIED,  # Reusing action
        email=request.user.email,
        user=request.user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details="Veterinarian profile completed",
    )

    messages.success(
        request,
        _(
            "¡Perfil completado exitosamente! Ya puede enviar protocolos al laboratorio."
        ),
    )
    return redirect("accounts:veterinarian_profile_detail")


@login_required
def veterinarian_profile_detail_view(request):
    """Display veterinarian profile details."""
    # Only veterinarians can access this view
    if not request.user.is_veterinarian:
        messages.error(request, _("Solo veterinarios pueden ver este perfil."))
        return redirect("/")

    # Check if profile exists
    if not hasattr(request.user, "veterinarian_profile"):
        messages.warning(
            request, _("Por favor complete su perfil para continuar.")
        )
        return redirect("accounts:complete_profile")

    veterinarian = request.user.veterinarian_profile

    # Get address (if exists)
    try:
        address = veterinarian.address
    except Address.DoesNotExist:
        address = None

    context = {
        "veterinarian": veterinarian,
        "address": address,
        "profile_completeness": veterinarian.profile_completeness,
    }

    return render(
        request, "accounts/veterinarian_profile_detail.html", context
    )


@login_required
@csrf_protect
def veterinarian_profile_edit_view(request):
    """Edit veterinarian profile."""
    # Only veterinarians can access this view
    if not request.user.is_veterinarian:
        messages.error(
            request, _("Solo veterinarios pueden editar este perfil.")
        )
        return redirect("/")

    # Check if profile exists
    if not hasattr(request.user, "veterinarian_profile"):
        messages.warning(
            request, _("Por favor complete su perfil para continuar.")
        )
        return redirect("accounts:complete_profile")

    veterinarian = request.user.veterinarian_profile

    # Get or create address
    try:
        address = veterinarian.address
    except Address.DoesNotExist:
        address = None

    # GET request: show form
    if request.method != "POST":
        vet_form = VeterinarianProfileForm(instance=veterinarian)
        address_form = (
            AddressForm(instance=address) if address else AddressForm()
        )

        context = {
            "vet_form": vet_form,
            "address_form": address_form,
            "veterinarian": veterinarian,
        }
        return render(
            request, "accounts/veterinarian_profile_edit.html", context
        )

    # POST request: process form
    vet_form = VeterinarianProfileForm(request.POST, instance=veterinarian)
    address_form = (
        AddressForm(request.POST, instance=address)
        if address
        else AddressForm(request.POST)
    )

    # Validate both forms
    if not (vet_form.is_valid() and address_form.is_valid()):
        context = {
            "vet_form": vet_form,
            "address_form": address_form,
            "veterinarian": veterinarian,
        }
        return render(
            request, "accounts/veterinarian_profile_edit.html", context
        )

    # Track changes for audit log
    changed_fields = []

    # Check veterinarian changes
    if vet_form.has_changed():
        for field in vet_form.changed_data:
            old_value = getattr(veterinarian, field)
            new_value = vet_form.cleaned_data[field]
            VeterinarianChangeLog.log_change(
                veterinarian=veterinarian,
                changed_by=request.user,
                field_name=field,
                old_value=old_value,
                new_value=new_value,
                ip_address=get_client_ip(request),
            )
            changed_fields.append(field)

    # Save veterinarian
    vet_form.save()

    # Save or create address
    if not address:
        address = address_form.save(commit=False)
        address.veterinarian = veterinarian
        address.save()
    else:
        # Check address changes
        if address_form.has_changed():
            for field in address_form.changed_data:
                old_value = getattr(address, field)
                new_value = address_form.cleaned_data[field]
                VeterinarianChangeLog.log_change(
                    veterinarian=veterinarian,
                    changed_by=request.user,
                    field_name=f"address.{field}",
                    old_value=old_value,
                    new_value=new_value,
                    ip_address=get_client_ip(request),
                )
                changed_fields.append(f"address.{field}")

        address_form.save()

    # Log profile update
    if changed_fields:
        AuthAuditLog.log(
            action=AuthAuditLog.Action.PASSWORD_CHANGED,  # Reusing action
            email=request.user.email,
            user=request.user,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details=f"Profile updated: {', '.join(changed_fields)}",
        )

    messages.success(request, _("Perfil actualizado exitosamente."))
    return redirect("accounts:veterinarian_profile_detail")


@login_required
def veterinarian_profile_history_view(request):
    """View veterinarian profile change history."""
    # Only veterinarians can access this view
    if not request.user.is_veterinarian:
        messages.error(
            request, _("Solo veterinarios pueden ver este historial.")
        )
        return redirect("/")

    # Check if profile exists
    if not hasattr(request.user, "veterinarian_profile"):
        messages.warning(
            request, _("Por favor complete su perfil para continuar.")
        )
        return redirect("accounts:complete_profile")

    veterinarian = request.user.veterinarian_profile
    changes = veterinarian.change_logs.all()[:50]  # Last 50 changes

    context = {
        "veterinarian": veterinarian,
        "changes": changes,
    }

    return render(
        request, "accounts/veterinarian_profile_history.html", context
    )
