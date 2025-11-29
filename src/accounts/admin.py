from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from .models import (
    Address,
    AuthAuditLog,
    Histopathologist,
    PasswordResetToken,
    User,
    Veterinarian,
    VeterinarianChangeLog,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role-based fields."""

    list_display = [
        "email",
        "username",
        "first_name",
        "last_name",
        "role",
        "email_verified",
        "is_active",
        "is_staff",
        "last_login_at",
    ]
    list_filter = [
        "role",
        "email_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
    ]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "last_login_at", "date_joined")},
        ),
        (_("Security"), {"fields": ("failed_login_attempts",)}),
        (
            _("Email Verification"),
            {
                "fields": (
                    "email_verified",
                    "email_verification_token",
                    "email_verification_sent_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "role",
                    "is_superuser",
                ),
            },
        ),
    )

    readonly_fields = [
        "last_login",
        "date_joined",
        "last_login_at",
        "email_verification_sent_at",
    ]

    actions = [
        "reset_failed_attempts",
        "lock_accounts",
        "unlock_accounts",
        "mark_email_verified",
        "resend_verification_email",
    ]

    def reset_failed_attempts(self, request, queryset):
        """Reset failed login attempts for selected users."""
        updated = queryset.update(failed_login_attempts=0)
        self.message_user(
            request,
            f"Successfully reset failed login attempts for {updated} user(s).",
        )

    reset_failed_attempts.short_description = "Reset failed login attempts"

    def lock_accounts(self, request, queryset):
        """Lock selected user accounts."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"Successfully locked {updated} account(s)."
        )

    lock_accounts.short_description = "Lock selected accounts"

    def unlock_accounts(self, request, queryset):
        """Unlock selected user accounts."""
        updated = queryset.update(is_active=True, failed_login_attempts=0)
        self.message_user(
            request, f"Successfully unlocked {updated} account(s)."
        )

    unlock_accounts.short_description = "Unlock selected accounts"

    def mark_email_verified(self, request, queryset):
        """Mark selected users as email verified."""
        updated = queryset.update(
            email_verified=True, email_verification_token=None
        )
        self.message_user(
            request,
            f"Successfully marked {updated} user(s) as email verified.",
        )

    mark_email_verified.short_description = "Mark email as verified"

    def resend_verification_email(self, request, queryset):
        """Resend verification email to selected veterinarians."""
        count = 0
        for user in queryset.filter(
            role=User.Role.VETERINARIO, email_verified=False, is_active=True
        ):
            # Generate new token
            token = user.generate_email_verification_token()

            # Build verification URL
            verification_url = request.build_absolute_uri(
                f"/accounts/verify-email/{token}/"
            )

            # Render email
            html_message = render_to_string(
                "accounts/emails/email_verification.html",
                {
                    "user": user,
                    "verification_url": verification_url,
                },
            )
            plain_message = strip_tags(html_message)

            # Send email
            send_mail(
                subject="Verifique su email - AdLab",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            # Log action
            AuthAuditLog.log(
                action=AuthAuditLog.Action.EMAIL_VERIFICATION_SENT,
                email=user.email,
                user=user,
                details="Verification email resent by admin",
            )

            count += 1

        self.message_user(
            request, f"Successfully sent {count} verification email(s)."
        )

    resend_verification_email.short_description = "Resend verification email"

    def save_model(self, request, obj, form, change):
        """
        Override save_model to automatically set is_superuser=True 
        when role is set to ADMIN.
        """
        # If role is ADMIN, automatically set is_superuser=True
        if obj.role == User.Role.ADMIN:
            obj.is_superuser = True
            obj.is_staff = True  # Also set is_staff for admin access
        
        # Call the parent save_model method
        super().save_model(request, obj, form, change)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for password reset tokens."""

    list_display = [
        "user",
        "token_preview",
        "created_at",
        "expires_at",
        "used_at",
        "is_valid_display",
    ]
    list_filter = ["created_at", "expires_at", "used_at"]
    search_fields = ["user__email", "token"]
    readonly_fields = ["token", "created_at", "expires_at", "used_at"]
    ordering = ["-created_at"]

    def token_preview(self, obj):
        """Show preview of token."""
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token

    token_preview.short_description = "Token"

    def is_valid_display(self, obj):
        """Display if token is valid."""
        return obj.is_valid()

    is_valid_display.short_description = "Valid"
    is_valid_display.boolean = True

    def has_add_permission(self, request):
        """Disable manual token creation."""
        return False


@admin.register(AuthAuditLog)
class AuthAuditLogAdmin(admin.ModelAdmin):
    """Admin for authentication audit logs."""

    list_display = ["created_at", "email", "action", "ip_address", "user"]
    list_filter = ["action", "created_at"]
    search_fields = ["email", "ip_address", "user__email"]
    readonly_fields = [
        "user",
        "email",
        "action",
        "ip_address",
        "user_agent",
        "details",
        "created_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        """Disable manual log creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make logs read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - no deletion allowed."""
        return False


# ============================================================================
# VETERINARIAN PROFILE ADMIN
# ============================================================================


class AddressInline(admin.StackedInline):
    """Inline admin for veterinarian address."""

    model = Address
    can_delete = False
    verbose_name_plural = "Address"
    fields = [
        "province",
        "locality",
        "street",
        "number",
        "floor",
        "apartment",
        "postal_code",
        "notes",
    ]


class VeterinarianChangeLogInline(admin.TabularInline):
    """Inline admin for veterinarian change log."""

    model = VeterinarianChangeLog
    can_delete = False
    extra = 0
    readonly_fields = [
        "field_name",
        "old_value",
        "new_value",
        "changed_by",
        "changed_at",
        "ip_address",
    ]
    fields = [
        "changed_at",
        "field_name",
        "old_value",
        "new_value",
        "changed_by",
    ]
    ordering = ["-changed_at"]

    def has_add_permission(self, request, obj=None):
        """Disable manual log creation."""
        return False


@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    """Admin for veterinarian profiles."""

    list_display = [
        "license_number",
        "last_name",
        "first_name",
        "dni",
        "cuil_cuit",
        "email",
        "phone",
        "is_verified",
        "verified_at",
        "created_at",
    ]
    list_filter = ["is_verified", "verified_at", "created_at"]
    search_fields = [
        "license_number",
        "last_name",
        "first_name",
        "dni",
        "cuil_cuit",
        "email",
        "phone",
    ]
    readonly_fields = [
        "user",
        "email",
        "is_verified",
        "verified_by",
        "verified_at",
        "verification_notes",
        "created_at",
        "updated_at",
        "profile_completeness_display",
    ]
    ordering = ["-created_at"]
    inlines = [AddressInline, VeterinarianChangeLogInline]

    fieldsets = (
        (
            _("Professional Information"),
            {
                "fields": (
                    "user",
                    "first_name",
                    "last_name",
                    "license_number",
                    "dni",
                    "cuil_cuit",
                    "phone",
                    "email",
                ),
            },
        ),
        (
            _("Verification Status"),
            {
                "fields": (
                    "is_verified",
                    "verified_by",
                    "verified_at",
                    "verification_notes",
                ),
            },
        ),
        (
            _("Profile Metrics"),
            {
                "fields": ("profile_completeness_display",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["verify_veterinarians", "unverify_veterinarians"]

    def profile_completeness_display(self, obj):
        """Display profile completeness percentage."""
        return f"{obj.profile_completeness}%"

    profile_completeness_display.short_description = "Profile Completeness"

    def verify_veterinarians(self, request, queryset):
        """Verify selected veterinarians."""
        count = 0
        for vet in queryset.filter(is_verified=False):
            vet.verify(
                verified_by_user=request.user, notes="Verified by admin"
            )
            count += 1

        self.message_user(
            request, f"Successfully verified {count} veterinarian(s)."
        )

    verify_veterinarians.short_description = "Verify selected veterinarians"

    def unverify_veterinarians(self, request, queryset):
        """Unverify selected veterinarians."""
        updated = queryset.update(
            is_verified=False,
            verified_by=None,
            verified_at=None,
            verification_notes="",
        )
        self.message_user(
            request, f"Successfully unverified {updated} veterinarian(s)."
        )

    unverify_veterinarians.short_description = (
        "Unverify selected veterinarians"
    )

    def has_add_permission(self, request):
        """Disable manual veterinarian creation (must be created via registration)."""
        return False


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin for veterinarian addresses."""

    list_display = [
        "veterinarian",
        "street",
        "number",
        "locality",
        "province",
        "postal_code",
    ]
    list_filter = ["province", "locality"]
    search_fields = [
        "veterinarian__first_name",
        "veterinarian__last_name",
        "veterinarian__license_number",
        "street",
        "locality",
        "province",
    ]
    readonly_fields = ["veterinarian", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            _("Veterinarian"),
            {
                "fields": ("veterinarian",),
            },
        ),
        (
            _("Address Information"),
            {
                "fields": (
                    "province",
                    "locality",
                    "street",
                    "number",
                    "floor",
                    "apartment",
                    "postal_code",
                    "notes",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Disable manual address creation (must be created with veterinarian)."""
        return False


@admin.register(VeterinarianChangeLog)
class VeterinarianChangeLogAdmin(admin.ModelAdmin):
    """Admin for veterinarian change logs."""

    list_display = [
        "changed_at",
        "veterinarian",
        "field_name",
        "changed_by",
        "ip_address",
    ]
    list_filter = ["changed_at", "field_name"]
    search_fields = [
        "veterinarian__license_number",
        "veterinarian__last_name",
        "veterinarian__first_name",
        "changed_by__email",
        "field_name",
    ]
    readonly_fields = [
        "veterinarian",
        "changed_by",
        "field_name",
        "old_value",
        "new_value",
        "changed_at",
        "ip_address",
    ]
    ordering = ["-changed_at"]

    fieldsets = (
        (
            _("Change Information"),
            {
                "fields": (
                    "veterinarian",
                    "changed_by",
                    "changed_at",
                    "ip_address",
                ),
            },
        ),
        (
            _("Change Details"),
            {
                "fields": (
                    "field_name",
                    "old_value",
                    "new_value",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        """Disable manual log creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make logs read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - no deletion allowed."""
        return False


# ============================================================================
# HISTOPATHOLOGIST ADMIN
# ============================================================================


@admin.register(Histopathologist)
class HistopathologistAdmin(admin.ModelAdmin):
    """Admin for histopathologist profiles."""

    list_display = [
        "license_number",
        "last_name",
        "first_name",
        "position",
        "is_active",
        "has_signature_display",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = [
        "license_number",
        "last_name",
        "first_name",
        "user__email",
    ]
    readonly_fields = ["created_at", "updated_at", "has_signature_display"]
    ordering = ["last_name", "first_name"]

    fieldsets = (
        (
            _("User Account"),
            {
                "fields": ("user",),
            },
        ),
        (
            _("Professional Information"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "license_number",
                    "position",
                    "specialty",
                    "phone_number",
                ),
            },
        ),
        (
            _("Signature"),
            {
                "fields": (
                    "signature_image",
                    "has_signature_display",
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": ("is_active",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["activate_histopathologists", "deactivate_histopathologists"]

    def has_signature_display(self, obj):
        """Display if histopathologist has uploaded signature."""
        return obj.has_signature()

    has_signature_display.short_description = _("Has Signature")
    has_signature_display.boolean = True

    def activate_histopathologists(self, request, queryset):
        """Activate selected histopathologists."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Successfully activated {updated} histopathologist(s).",
        )

    activate_histopathologists.short_description = (
        "Activate selected histopathologists"
    )

    def deactivate_histopathologists(self, request, queryset):
        """Deactivate selected histopathologists."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully deactivated {updated} histopathologist(s).",
        )

    deactivate_histopathologists.short_description = (
        "Deactivate selected histopathologists"
    )
