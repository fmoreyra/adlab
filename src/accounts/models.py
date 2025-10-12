import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model for the laboratory system.
    Extends Django's AbstractUser with role-based access control.
    """

    class Role(models.TextChoices):
        VETERINARIO = "veterinario", _("Veterinario Cliente")
        PERSONAL_LAB = "personal_lab", _("Personal de Laboratorio")
        HISTOPATOLOGO = "histopatologo", _("Histopatólogo")
        ADMIN = "admin", _("Administrador")

    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.VETERINARIO,
    )
    is_active = models.BooleanField(_("active"), default=True)
    failed_login_attempts = models.IntegerField(
        _("failed login attempts"), default=0
    )
    last_login_at = models.DateTimeField(
        _("last login at"), null=True, blank=True
    )

    # Email verification fields
    email_verified = models.BooleanField(_("email verified"), default=False)
    email_verification_token = models.CharField(
        _("email verification token"),
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )
    email_verification_sent_at = models.DateTimeField(
        _("email verification sent at"),
        null=True,
        blank=True,
    )

    # Use email as the username field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.email

    def reset_failed_login_attempts(self):
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.save(update_fields=["failed_login_attempts"])

    def increment_failed_login_attempts(self):
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1
        self.save(update_fields=["failed_login_attempts"])

    def is_locked_out(self):
        """Check if account is locked due to too many failed login attempts."""
        return self.failed_login_attempts >= 5

    @property
    def is_veterinarian(self):
        """Check if user is a veterinarian."""
        return self.role == self.Role.VETERINARIO

    @property
    def is_lab_staff(self):
        """Check if user is laboratory staff."""
        return self.role in [self.Role.PERSONAL_LAB, self.Role.HISTOPATOLOGO]

    @property
    def is_histopathologist(self):
        """Check if user is a histopathologist."""
        return self.role == self.Role.HISTOPATOLOGO

    @property
    def is_admin_user(self):
        """Check if user is an administrator."""
        return self.role == self.Role.ADMIN or self.is_superuser

    def can_login(self):
        """
        Determine if user can login based on role and verification status.

        Rules:
        - Internal users (lab staff, admin): Only need is_active=True
        - External users (veterinarians): Need is_active=True AND email_verified=True
        """
        # Internal users don't need verification
        if self.role in [
            self.Role.PERSONAL_LAB,
            self.Role.HISTOPATOLOGO,
            self.Role.ADMIN,
        ]:
            return self.is_active

        # External users (veterinarians) need verification
        if self.role == self.Role.VETERINARIO:
            return self.is_active and self.email_verified

        return self.is_active

    def generate_email_verification_token(self):
        """
        Generate cryptographically secure verification token.

        Returns:
            str: The generated token (32-byte urlsafe)
        """
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save(
            update_fields=[
                "email_verification_token",
                "email_verification_sent_at",
            ]
        )
        return self.email_verification_token

    def is_verification_token_expired(self):
        """
        Check if verification token is older than 24 hours.

        Returns:
            bool: True if expired, False if still valid
        """
        if not self.email_verification_sent_at:
            return True

        token_age = timezone.now() - self.email_verification_sent_at
        return token_age > timedelta(hours=24)

    def verify_email(self):
        """Mark email as verified and invalidate token."""
        self.email_verified = True
        self.email_verification_token = None
        self.save(update_fields=["email_verified", "email_verification_token"])


class PasswordResetToken(models.Model):
    """
    Model for password reset tokens.
    Tokens expire after 1 hour and can only be used once.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
        verbose_name=_("user"),
    )
    token = models.CharField(
        _("token"), max_length=255, unique=True, db_index=True
    )
    expires_at = models.DateTimeField(_("expires at"))
    used_at = models.DateTimeField(_("used at"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("password reset token")
        verbose_name_plural = _("password reset tokens")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def is_valid(self):
        """Check if token is still valid (not expired and not used)."""
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_as_used(self):
        """Mark token as used."""
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class AuthAuditLog(models.Model):
    """
    Audit log for authentication events.
    Tracks all login attempts, password resets, and other security events.
    """

    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", _("Login Success")
        LOGIN_FAILED = "login_failed", _("Login Failed")
        LOGOUT = "logout", _("Logout")
        PASSWORD_RESET_REQUEST = (
            "password_reset_request",
            _("Password Reset Request"),
        )
        PASSWORD_RESET_COMPLETE = (
            "password_reset_complete",
            _("Password Reset Complete"),
        )
        ACCOUNT_LOCKED = "account_locked", _("Account Locked")
        ACCOUNT_UNLOCKED = "account_unlocked", _("Account Unlocked")
        PASSWORD_CHANGED = "password_changed", _("Password Changed")
        EMAIL_VERIFICATION_SENT = (
            "email_verification_sent",
            _("Email Verification Sent"),
        )
        EMAIL_VERIFIED = "email_verified", _("Email Verified")
        EMAIL_VERIFICATION_FAILED = (
            "email_verification_failed",
            _("Email Verification Failed"),
        )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("user"),
    )
    email = models.EmailField(_("email"), max_length=255)
    action = models.CharField(
        _("action"), max_length=50, choices=Action.choices
    )
    ip_address = models.GenericIPAddressField(
        _("IP address"), null=True, blank=True
    )
    user_agent = models.TextField(_("user agent"), blank=True)
    details = models.TextField(_("details"), blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("authentication audit log")
        verbose_name_plural = _("authentication audit logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["email", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.email} - {self.created_at}"

    @classmethod
    def log(
        cls,
        action,
        email,
        user=None,
        ip_address=None,
        user_agent=None,
        details="",
    ):
        """
        Helper method to create audit log entries.

        Args:
            action: Action type from AuthAuditLog.Action
            email: User email
            user: User instance (optional)
            ip_address: IP address of the request
            user_agent: User agent string
            details: Additional details about the event
        """
        return cls.objects.create(
            user=user,
            email=email,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent or "",
            details=details,
        )


class Veterinarian(models.Model):
    """
    Veterinarian profile with professional credentials and contact information.
    Each veterinarian is linked to a User account with role=VETERINARIO.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="veterinarian_profile",
        verbose_name=_("user"),
    )
    first_name = models.CharField(_("first name"), max_length=100)
    last_name = models.CharField(_("last name"), max_length=100)
    license_number = models.CharField(
        _("license number"),
        max_length=50,
        unique=True,
        help_text=_(
            "Professional license number (matrícula). Example: MP-12345"
        ),
    )
    phone = models.CharField(
        _("phone"),
        max_length=50,
        help_text=_("Argentine format: +54 XXX XXXXXXX"),
    )
    email = models.EmailField(
        _("email"),
        max_length=255,
        help_text=_("Denormalized for quick access"),
    )

    # Verification status
    is_verified = models.BooleanField(_("is verified"), default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_veterinarians",
        verbose_name=_("verified by"),
    )
    verified_at = models.DateTimeField(_("verified at"), null=True, blank=True)
    verification_notes = models.TextField(
        _("verification notes"),
        blank=True,
        help_text=_("Admin notes about verification process"),
    )

    # Timestamps
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("veterinarian")
        verbose_name_plural = _("veterinarians")
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["license_number"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_verified"]),
        ]

    def __str__(self):
        return (
            f"{self.last_name}, {self.first_name} (MP: {self.license_number})"
        )

    def get_full_name(self):
        """Return the full name in 'First Last' format."""
        return f"{self.first_name} {self.last_name}".strip()

    def verify(self, verified_by_user, notes=""):
        """
        Mark veterinarian as verified.

        Args:
            verified_by_user: User instance who is verifying
            notes: Optional verification notes
        """
        self.is_verified = True
        self.verified_by = verified_by_user
        self.verified_at = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save(
            update_fields=[
                "is_verified",
                "verified_by",
                "verified_at",
                "verification_notes",
            ]
        )

    @property
    def profile_completeness(self):
        """
        Calculate profile completeness percentage.

        Returns:
            int: Percentage of required fields completed (0-100)
        """
        required_fields = [
            self.first_name,
            self.last_name,
            self.license_number,
            self.phone,
            self.email,
        ]

        # Check if address exists and is complete
        try:
            address = self.address
            address_fields = [
                address.province,
                address.locality,
                address.street,
                address.number,
            ]
            required_fields.extend(address_fields)
        except Address.DoesNotExist:
            # No address, add 4 empty fields
            required_fields.extend([None, None, None, None])

        completed = sum(1 for field in required_fields if field)
        total = len(required_fields)
        return int((completed / total) * 100) if total > 0 else 0


class Address(models.Model):
    """
    Address information for veterinarians.
    Used for invoicing and communication purposes.
    """

    veterinarian = models.OneToOneField(
        Veterinarian,
        on_delete=models.CASCADE,
        related_name="address",
        verbose_name=_("veterinarian"),
    )

    # Required fields
    province = models.CharField(_("province"), max_length=100)
    locality = models.CharField(_("locality"), max_length=100)
    street = models.CharField(_("street"), max_length=200)
    number = models.CharField(_("number"), max_length=20)

    # Optional fields
    postal_code = models.CharField(_("postal code"), max_length=20, blank=True)
    floor = models.CharField(_("floor"), max_length=10, blank=True)
    apartment = models.CharField(_("apartment"), max_length=10, blank=True)
    notes = models.TextField(
        _("notes"), blank=True, help_text=_("Additional address information")
    )

    # Timestamps
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")
        indexes = [
            models.Index(fields=["province"]),
            models.Index(fields=["locality"]),
        ]

    def __str__(self):
        parts = [f"{self.street} {self.number}"]
        if self.floor:
            parts.append(f"Floor {self.floor}")
        if self.apartment:
            parts.append(f"Apt {self.apartment}")
        parts.append(f"{self.locality}, {self.province}")
        result = ", ".join(parts)
        if self.postal_code:
            result += f" ({self.postal_code})"
        return result

    def get_full_address(self):
        """Return complete formatted address."""
        return str(self)


class VeterinarianChangeLog(models.Model):
    """
    Audit log for veterinarian profile changes.
    Tracks all modifications to profile data for compliance.
    """

    veterinarian = models.ForeignKey(
        Veterinarian,
        on_delete=models.CASCADE,
        related_name="change_logs",
        verbose_name=_("veterinarian"),
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="veterinarian_changes_made",
        verbose_name=_("changed by"),
    )
    field_name = models.CharField(_("field name"), max_length=50)
    old_value = models.TextField(_("old value"), blank=True)
    new_value = models.TextField(_("new value"), blank=True)
    changed_at = models.DateTimeField(_("changed at"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        _("IP address"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("veterinarian change log")
        verbose_name_plural = _("veterinarian change logs")
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["veterinarian", "-changed_at"]),
            models.Index(fields=["-changed_at"]),
        ]

    def __str__(self):
        return f"{self.veterinarian} - {self.field_name} changed at {self.changed_at}"

    @classmethod
    def log_change(
        cls,
        veterinarian,
        changed_by,
        field_name,
        old_value,
        new_value,
        ip_address=None,
    ):
        """
        Helper method to log a change.

        Args:
            veterinarian: Veterinarian instance
            changed_by: User who made the change
            field_name: Name of the field that changed
            old_value: Previous value
            new_value: New value
            ip_address: IP address of the request (optional)
        """
        return cls.objects.create(
            veterinarian=veterinarian,
            changed_by=changed_by,
            field_name=field_name,
            old_value=str(old_value) if old_value else "",
            new_value=str(new_value) if new_value else "",
            ip_address=ip_address,
        )


class Histopathologist(models.Model):
    """
    Histopathologist profile for laboratory staff who write reports.
    Contains professional information and digital signature.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="histopathologist_profile",
        verbose_name=_("usuario"),
    )
    last_name = models.CharField(
        _("apellido"),
        max_length=100,
        help_text=_("Apellido del histopatólogo"),
    )
    first_name = models.CharField(
        _("nombre"),
        max_length=100,
        help_text=_("Nombre del histopatólogo"),
    )
    license_number = models.CharField(
        _("número de matrícula"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Número de matrícula profesional"),
    )
    position = models.CharField(
        _("cargo"),
        max_length=100,
        blank=True,
        help_text=_("Ej: Profesor Titular, Profesor Asociado, Jefe de TP"),
    )
    specialty = models.CharField(
        _("especialidad"),
        max_length=200,
        blank=True,
        help_text=_("Especialidad o área de expertise"),
    )
    signature_image = models.ImageField(
        _("firma digital"),
        upload_to="signatures/histopathologists/",
        blank=True,
        null=True,
        help_text=_("Imagen de la firma para incluir en informes"),
    )
    phone_number = models.CharField(
        _("teléfono"),
        max_length=20,
        blank=True,
        help_text=_("Número de teléfono de contacto"),
    )
    
    # Professional info
    is_active = models.BooleanField(
        _("activo"),
        default=True,
        help_text=_("Si el histopatólogo está activo para firmar informes"),
    )
    
    # Timestamps
    created_at = models.DateTimeField(_("creado el"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado el"), auto_now=True)

    class Meta:
        verbose_name = _("histopatólogo")
        verbose_name_plural = _("histopatólogos")
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["license_number"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Return histopathologist's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_formal_name(self):
        """Return formal name with title."""
        return f"Dr./Dra. {self.get_full_name()}"

    def has_signature(self):
        """Check if histopathologist has uploaded signature."""
        return bool(self.signature_image)
