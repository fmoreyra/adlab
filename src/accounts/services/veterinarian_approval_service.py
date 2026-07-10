"""
Veterinarian approval, deletion, and reactivation for admin operations.
"""

from dataclasses import dataclass

from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from accounts.models import AuthAuditLog, User, Veterinarian
from accounts.services.auth_service import AuthenticationService
from protocols.emails import prepare_outbound_email, record_sent_email
from protocols.models import EmailLog, Protocol


@dataclass
class ApprovalResult:
    """Result of approving a veterinarian account."""

    success: bool
    email_sent: bool
    message: str = ""


@dataclass
class DeletionResult:
    """Result of deleting/deactivating a veterinarian account."""

    success: bool
    email_sent: bool
    mode: str = ""
    message: str = ""


@dataclass
class ReactivationResult:
    """Result of reactivating an inactive veterinarian account."""

    success: bool
    message: str = ""


def get_pending_veterinarians_count() -> int:
    """
    Count veterinarians awaiting admin approval.

    Returns:
        int: Pending veterinarians with verified email and active user
    """
    return Veterinarian.objects.filter(
        user__is_active=True,
        user__email_verified=True,
        is_verified=False,
    ).count()


def get_veterinarians_queryset(status_filter: str):
    """
    Return veterinarians filtered by admin status tab.

    Args:
        status_filter: One of pending, enabled, inactive, all

    Returns:
        QuerySet: Filtered veterinarians ordered by name
    """
    queryset = Veterinarian.objects.select_related("user").order_by(
        "last_name", "first_name"
    )

    if status_filter == "pending":
        return queryset.filter(
            user__is_active=True,
            user__email_verified=True,
            is_verified=False,
        )
    if status_filter == "enabled":
        return queryset.filter(
            user__is_active=True,
            is_verified=True,
        )
    if status_filter == "inactive":
        return queryset.filter(user__is_active=False)

    return queryset


def search_veterinarians(queryset, query: str):
    """
    Filter veterinarians by name, email, license, or CUIL.

    Args:
        queryset: Base queryset to filter
        query: Free-text search term

    Returns:
        QuerySet: Matching veterinarians
    """
    from django.db.models import Q

    query = (query or "").strip()
    if not query:
        return queryset

    return queryset.filter(
        Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(email__icontains=query)
        | Q(license_number__icontains=query)
        | Q(cuil_cuit__icontains=query)
    )


def can_delete(veterinarian: Veterinarian) -> tuple[bool, str, str]:
    """
    Determine whether a veterinarian account can be deleted/deactivated.

    Args:
        veterinarian: Veterinarian to evaluate

    Returns:
        tuple: (allowed, mode, reason) where mode is anonymize or deactivate_only
    """
    protocol_count = Protocol.objects.filter(veterinarian=veterinarian).count()
    if protocol_count > 0:
        return (
            True,
            "deactivate_only",
            (
                "Este veterinario tiene protocolos asociados. "
                "La cuenta se desactivará pero el email no quedará "
                "disponible para un nuevo registro."
            ),
        )

    return (
        True,
        "anonymize",
        (
            "La cuenta se eliminará y el email quedará disponible "
            "para un nuevo registro."
        ),
    )


class VeterinarianApprovalService:
    """Admin operations for veterinarian account lifecycle."""

    def __init__(self):
        self.auth_service = AuthenticationService()

    def approve(
        self,
        veterinarian: Veterinarian,
        approved_by: User,
        request,
        notes: str = "",
    ) -> ApprovalResult:
        """
        Enable a veterinarian for protocol creation and lab search.

        Args:
            veterinarian: Veterinarian to approve
            approved_by: Admin user performing the action
            request: HTTP request for audit/email context
            notes: Optional admin notes stored on the profile

        Returns:
            ApprovalResult: Outcome with email delivery status
        """
        if veterinarian.is_verified:
            return ApprovalResult(
                success=False,
                email_sent=False,
                message="El veterinario ya está habilitado.",
            )

        if not veterinarian.user.is_active:
            return ApprovalResult(
                success=False,
                email_sent=False,
                message="No se puede habilitar una cuenta inactiva.",
            )

        veterinarian.verify(verified_by_user=approved_by, notes=notes)
        email_sent = self._send_approved_email(veterinarian, request)

        AuthAuditLog.log(
            action=AuthAuditLog.Action.VETERINARIAN_APPROVED,
            email=veterinarian.email,
            user=veterinarian.user,
            ip_address=self.auth_service._get_client_ip(request),
            user_agent=self.auth_service._get_user_agent(request),
            details=f"Habilitado por {approved_by.email}",
        )

        message = "Veterinario habilitado correctamente."
        if not email_sent:
            message += (
                " No se pudo enviar el email de notificación; "
                "verifique la configuración SMTP."
            )

        return ApprovalResult(
            success=True, email_sent=email_sent, message=message
        )

    def delete_account(
        self,
        veterinarian: Veterinarian,
        deleted_by: User,
        request,
    ) -> DeletionResult:
        """
        Soft-delete or deactivate a veterinarian account.

        Args:
            veterinarian: Veterinarian to remove
            deleted_by: Admin user performing the action
            request: HTTP request for audit/email context

        Returns:
            DeletionResult: Outcome with deletion mode and email status
        """
        allowed, mode, reason = can_delete(veterinarian)
        if not allowed:
            return DeletionResult(
                success=False,
                email_sent=False,
                mode=mode,
                message=reason,
            )

        original_email = veterinarian.email
        email_sent = self._send_removed_email(veterinarian, request)

        with transaction.atomic():
            user = veterinarian.user
            if mode == "anonymize":
                timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
                anonymized = f"deleted+{user.pk}+{timestamp}@invalid.local"
                user.email = anonymized
                user.username = anonymized
                user.is_active = False
                user.save(update_fields=["email", "username", "is_active"])

                veterinarian.email = anonymized
                veterinarian.license_number = None
                veterinarian.save(update_fields=["email", "license_number"])
            else:
                user.is_active = False
                user.save(update_fields=["is_active"])

        AuthAuditLog.log(
            action=AuthAuditLog.Action.VETERINARIAN_DELETED,
            email=original_email,
            user=veterinarian.user,
            ip_address=self.auth_service._get_client_ip(request),
            user_agent=self.auth_service._get_user_agent(request),
            details=(
                f"Eliminado por {deleted_by.email}; modo={mode}; "
                f"email_original={original_email}"
            ),
        )

        message = "Cuenta eliminada correctamente."
        if not email_sent:
            message += (
                " No se pudo enviar el email de notificación; "
                "verifique la configuración SMTP."
            )

        return DeletionResult(
            success=True,
            email_sent=email_sent,
            mode=mode,
            message=message,
        )

    def reactivate(
        self,
        veterinarian: Veterinarian,
        reactivated_by: User,
        request,
    ) -> ReactivationResult:
        """
        Reactivate an inactive veterinarian account without anonymization.

        Args:
            veterinarian: Veterinarian to reactivate
            reactivated_by: Admin user performing the action
            request: HTTP request for audit context

        Returns:
            ReactivationResult: Outcome message
        """
        user = veterinarian.user
        if user.is_active:
            return ReactivationResult(
                success=False,
                message="La cuenta ya está activa.",
            )

        if user.email.endswith("@invalid.local"):
            return ReactivationResult(
                success=False,
                message=(
                    "No se puede reactivar una cuenta anonimizada. "
                    "El veterinario debe registrarse nuevamente."
                ),
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        AuthAuditLog.log(
            action=AuthAuditLog.Action.VETERINARIAN_REACTIVATED,
            email=veterinarian.email,
            user=user,
            ip_address=self.auth_service._get_client_ip(request),
            user_agent=self.auth_service._get_user_agent(request),
            details=f"Reactivado por {reactivated_by.email}",
        )

        return ReactivationResult(
            success=True,
            message="Cuenta reactivada correctamente.",
        )

    def _send_approved_email(self, veterinarian, request) -> bool:
        """Send account approval notification email."""
        login_url = request.build_absolute_uri("/accounts/login/")
        html_message = render_to_string(
            "accounts/emails/veterinarian_approved.html",
            {
                "veterinarian": veterinarian,
                "login_url": login_url,
            },
        )
        plain_message = strip_tags(html_message)
        subject = "Su cuenta fue habilitada - AdLab"
        delivery_email, delivery_subject = prepare_outbound_email(
            veterinarian.email,
            subject,
        )

        try:
            send_mail(
                subject=delivery_subject,
                message=plain_message,
                from_email=None,
                recipient_list=[delivery_email],
                html_message=html_message,
                fail_silently=False,
            )
            record_sent_email(
                EmailLog.EmailType.VETERINARIAN_APPROVED,
                delivery_email,
                delivery_subject,
            )
            return True
        except Exception:
            return False

    def _send_removed_email(self, veterinarian, request) -> bool:
        """Send account removal notification email."""
        html_message = render_to_string(
            "accounts/emails/veterinarian_account_removed.html",
            {"veterinarian": veterinarian},
        )
        plain_message = strip_tags(html_message)
        subject = "Su cuenta fue eliminada - AdLab"
        delivery_email, delivery_subject = prepare_outbound_email(
            veterinarian.email,
            subject,
        )

        try:
            send_mail(
                subject=delivery_subject,
                message=plain_message,
                from_email=None,
                recipient_list=[delivery_email],
                html_message=html_message,
                fail_silently=False,
            )
            record_sent_email(
                EmailLog.EmailType.VETERINARIAN_ACCOUNT_REMOVED,
                delivery_email,
                delivery_subject,
            )
            return True
        except Exception:
            return False
