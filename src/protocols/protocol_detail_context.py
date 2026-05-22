"""
Shared context builders for protocol detail templates.
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.mixins import (
    user_can_access_work_order,
    user_can_view_protocol_processing,
)
from accounts.models import Veterinarian
from protocols.models import Protocol, Report
from protocols.services.protocol_service import ProtocolProcessingService


def _user_owns_protocol(user, protocol):
    """Return whether the authenticated user owns the protocol."""
    if not user.is_authenticated or not user.is_veterinarian:
        return False

    try:
        return user.veterinarian_profile.pk == protocol.veterinarian_id
    except Veterinarian.DoesNotExist:
        return False


def _user_can_create_reports(user):
    """Return whether the user may create pathology reports."""
    if not user.is_authenticated:
        return False

    profile = getattr(user, "lab_staff_profile", None)
    if profile:
        return profile.is_active and profile.can_create_reports

    return bool(getattr(user, "can_create_reports", False))


def build_protocol_detail_action_context(user, protocol, request=None):
    """
    Build action flags and related objects for protocol detail UI.

    Args:
        user: Authenticated user viewing the protocol.
        protocol: Protocol instance (prefetch reports when possible).
        request: Optional HttpRequest for absolute public URLs.

    Returns:
        dict: Template context keys for actions and navigation.
    """
    is_lab_staff = user.is_authenticated and user.is_lab_staff
    is_veterinarian = user.is_authenticated and user.is_veterinarian
    owns_protocol = _user_owns_protocol(user, protocol)

    if user.is_authenticated and user.is_admin_user:
        back_url = reverse("protocols:protocol_list")
        back_label = _("← Volver a todos los protocolos")
    elif is_veterinarian:
        back_url = reverse("protocols:protocol_list")
        back_label = _("← Volver a mis protocolos")
    elif is_lab_staff:
        back_url = reverse("protocols:reception")
        back_label = _("← Volver a recepción")
    else:
        back_url = reverse("home")
        back_label = _("← Volver")

    related_work_order = getattr(protocol, "work_order", None)
    if related_work_order is None:
        try:
            related_work_order = protocol.work_order
        except Exception:
            related_work_order = None

    can_view_related_work_order = (
        related_work_order is not None
        and user_can_access_work_order(user, related_work_order)
    )

    can_view_protocol_processing = user_can_view_protocol_processing(
        user, protocol
    )

    latest_report = (
        protocol.reports.order_by("-created_at").first()
        if hasattr(protocol, "reports")
        else None
    )

    can_view_report_detail = False
    can_download_report_pdf = False
    if latest_report and user.is_authenticated:
        if is_lab_staff:
            can_view_report_detail = True
            can_download_report_pdf = (
                latest_report.status != Report.Status.DRAFT
                and bool(latest_report.pdf_path)
            )
        elif owns_protocol:
            can_view_report_detail = latest_report.status in (
                Report.Status.FINALIZED,
                Report.Status.SENT,
            )
            can_download_report_pdf = can_view_report_detail and bool(
                latest_report.pdf_path
            )

    user_can_create_reports = _user_can_create_reports(user)
    processing_readiness = None
    can_mark_ready = False

    if is_lab_staff:
        processing_readiness = (
            ProtocolProcessingService().get_processing_readiness(protocol)
        )
        can_mark_ready = (
            protocol.status == Protocol.Status.PROCESSING
            and processing_readiness.get("can_mark_ready", False)
        )

    has_reports = bool(latest_report)
    can_create_report = (
        is_lab_staff
        and user_can_create_reports
        and protocol.status == Protocol.Status.READY
        and not has_reports
    )
    can_edit_report = (
        is_lab_staff
        and user_can_create_reports
        and latest_report is not None
        and latest_report.can_edit()
    )
    can_send_report = (
        is_lab_staff
        and latest_report is not None
        and latest_report.status == Report.Status.FINALIZED
    )

    can_receive_protocol = (
        is_lab_staff and protocol.status == Protocol.Status.SUBMITTED
    )
    can_resubmit_protocol = (
        is_lab_staff and protocol.status == Protocol.Status.REJECTED
    )
    can_view_reception_detail = is_lab_staff and (
        protocol.reception_date is not None
        or protocol.status == Protocol.Status.REJECTED
    )
    can_print_reception_label = is_lab_staff and bool(protocol.protocol_number)
    can_add_to_work_order = (
        is_lab_staff
        and user.is_staff
        and protocol.status == Protocol.Status.READY
        and related_work_order is None
    )

    public_detail_url = None
    if request is not None:
        public_detail_url = request.build_absolute_uri(
            reverse(
                "protocols:protocol_public_detail",
                kwargs={"external_id": protocol.external_id},
            )
        )

    return {
        "back_url": back_url,
        "back_label": back_label,
        "related_work_order": related_work_order,
        "can_view_related_work_order": can_view_related_work_order,
        "can_view_protocol_processing": can_view_protocol_processing,
        "latest_report": latest_report,
        "can_view_report_detail": can_view_report_detail,
        "can_download_report_pdf": can_download_report_pdf,
        "user_can_create_reports": user_can_create_reports,
        "processing_readiness": processing_readiness,
        "can_mark_ready": can_mark_ready,
        "can_create_report": can_create_report,
        "can_edit_report": can_edit_report,
        "can_send_report": can_send_report,
        "can_receive_protocol": can_receive_protocol,
        "can_resubmit_protocol": can_resubmit_protocol,
        "can_view_reception_detail": can_view_reception_detail,
        "can_print_reception_label": can_print_reception_label,
        "can_add_to_work_order": can_add_to_work_order,
        "public_detail_url": public_detail_url,
        "hide_veterinarian_card": is_veterinarian and owns_protocol,
        "is_protocol_owner": owns_protocol,
        "show_lab_actions": is_lab_staff,
        "show_vet_actions": is_veterinarian and owns_protocol,
    }
