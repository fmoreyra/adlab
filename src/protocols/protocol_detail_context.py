"""
Shared context builders for protocol detail templates.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.mixins import user_can_view_protocol_processing
from accounts.models import Veterinarian
from accounts.report_access import (
    get_report_signature_redirect_url,
    user_can_view_report_images,
    user_requires_report_signature,
)
from protocols.lab_protocol import is_lab_created_protocol
from protocols.models import Cassette, Protocol, Report, Slide
from protocols.services.protocol_service import ProtocolProcessingService

_PROCESSING_ACTIVE_STATUSES = frozenset(
    {
        Protocol.Status.RECEIVED,
        Protocol.Status.PROCESSING,
        Protocol.Status.READY,
    }
)

_LAB_STATUSES_FOR_VET = frozenset(
    {
        Protocol.Status.PROCESSING,
        Protocol.Status.READY,
    }
)


@dataclass
class StatusHistoryDisplay:
    """Presentation row for the protocol status timeline."""

    status: str
    label: str
    changed_at: datetime
    description: str = ""
    changed_by: Optional[object] = None


def build_veterinarian_status_history(protocol) -> list[StatusHistoryDisplay]:
    """
    Collapse internal lab milestones for veterinarian-facing timeline.

    ``processing`` and ``ready`` become a single ``En laboratorio`` entry
    (timestamp of the first lab milestone). Internal descriptions and staff
    authors are omitted for that row.

    Args:
        protocol: Protocol instance with status_history relation

    Returns:
        list[StatusHistoryDisplay]: Newest-first timeline rows
    """
    entries = list(
        protocol.status_history.all()
        .select_related("changed_by")
        .order_by("changed_at")
    )
    result: list[StatusHistoryDisplay] = []
    lab_entry_added = False

    for entry in entries:
        if entry.status in _LAB_STATUSES_FOR_VET:
            if lab_entry_added:
                continue
            result.append(
                StatusHistoryDisplay(
                    status=Protocol.Status.PROCESSING,
                    label=str(_("En laboratorio")),
                    changed_at=entry.changed_at,
                    description="",
                    changed_by=None,
                )
            )
            lab_entry_added = True
            continue

        result.append(
            StatusHistoryDisplay(
                status=entry.status,
                label=str(
                    dict(Protocol.Status.choices).get(
                        entry.status, entry.status
                    )
                ),
                changed_at=entry.changed_at,
                description=entry.description or "",
                changed_by=entry.changed_by,
            )
        )

    result.reverse()
    return result


def build_staff_status_history(protocol) -> list[StatusHistoryDisplay]:
    """
    Full status timeline for laboratory staff and admins.

    Args:
        protocol: Protocol instance with status_history relation

    Returns:
        list[StatusHistoryDisplay]: Newest-first timeline rows
    """
    entries = (
        protocol.status_history.all()
        .select_related("changed_by")
        .order_by("-changed_at")
    )
    return [
        StatusHistoryDisplay(
            status=entry.status,
            label=entry.get_status_display(),
            changed_at=entry.changed_at,
            description=entry.description or "",
            changed_by=entry.changed_by,
        )
        for entry in entries
    ]


def build_status_history_for_user(
    user, protocol
) -> list[StatusHistoryDisplay]:
    """
    Return the status timeline appropriate for the viewing user.

    Args:
        user: Authenticated user
        protocol: Protocol instance

    Returns:
        list[StatusHistoryDisplay]: Newest-first timeline rows
    """
    is_vet_owner = (
        user.is_authenticated
        and user.is_veterinarian
        and _user_owns_protocol(user, protocol)
    )
    if is_vet_owner:
        return build_veterinarian_status_history(protocol)
    return build_staff_status_history(protocol)


def build_sample_registration_context(protocol):
    """
    Build context for the inline histopathology registration form.

    Args:
        protocol: Protocol instance with histopathology_sample

    Returns:
        dict: existing cassettes/slides and append mode flag
    """
    existing_cassettes = []
    if hasattr(protocol, "histopathology_sample"):
        existing_cassettes = Cassette.sort_for_display(
            list(protocol.histopathology_sample.cassettes.all())
        )
    existing_slides = Slide.sort_for_display(
        list(
            protocol.slides.all().prefetch_related("cassette_slides__cassette")
        )
    )
    return {
        "existing_cassettes": existing_cassettes,
        "existing_slides": existing_slides,
        "is_append_mode": bool(existing_cassettes),
        "protocol_number": protocol.protocol_number or "",
        "next_cassette_number": Cassette.next_sequence_number(
            protocol.histopathology_sample
        )
        if hasattr(protocol, "histopathology_sample")
        else 1,
        "next_slide_number": Slide.next_sequence_number(protocol),
    }


def sample_register_url(protocol):
    """Return URL for the dedicated cassette/slide registration view."""
    return reverse(
        "protocols:sample_register",
        kwargs={"protocol_pk": protocol.pk},
    )


def build_protocol_processing_context(user, protocol):
    """
    Build lab processing section context for protocol detail.

    Args:
        user: Authenticated user
        protocol: Protocol instance

    Returns:
        dict: Processing lists, readiness, and registration link flags
    """
    if not user_can_view_protocol_processing(user, protocol):
        return {"show_protocol_processing": False}

    if protocol.status not in _PROCESSING_ACTIVE_STATUSES:
        return {"show_protocol_processing": False}

    processing_service = ProtocolProcessingService()
    readiness = processing_service.get_processing_readiness(protocol)

    cassettes = []
    if (
        protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
        and hasattr(protocol, "histopathology_sample")
    ):
        cassettes = Cassette.sort_for_display(
            list(protocol.histopathology_sample.cassettes.all())
        )

    slides = Slide.sort_for_display(
        list(
            protocol.slides.all().prefetch_related("cassette_slides__cassette")
        )
    )

    can_register_samples = (
        protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY
        and protocol.status
        in (
            Protocol.Status.RECEIVED,
            Protocol.Status.PROCESSING,
        )
    )

    return {
        "show_protocol_processing": True,
        "processing_cassettes": cassettes,
        "processing_slides": slides,
        "processing_readiness": readiness,
        "can_register_samples": can_register_samples,
        "sample_register_url": sample_register_url(protocol)
        if can_register_samples
        else "",
    }


def protocol_detail_processing_url(protocol):
    """Return protocol detail URL anchored to the lab processing section."""
    return (
        reverse("protocols:protocol_detail", kwargs={"pk": protocol.pk})
        + "#procesamiento-lab"
    )


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


def _get_latest_report(protocol):
    """Return the most recent report for a protocol, if any."""
    if not hasattr(protocol, "reports"):
        return None

    return protocol.reports.order_by("-created_at").first()


def _get_report_images_preview(latest_report, limit=4):
    """
    Return ordered report images for protocol detail preview.

    Args:
        latest_report: Report instance or None
        limit: Maximum thumbnails to include

    Returns:
        list: ReportImage instances
    """
    if not latest_report:
        return []

    return list(
        latest_report.images.select_related("cassette", "slide").order_by(
            "order", "created_at"
        )[:limit]
    )


def build_protocol_report_images_context(user, protocol, latest_report=None):
    """
    Build context for report microscopy images on protocol detail.

    Args:
        user: Authenticated user
        protocol: Protocol instance
        latest_report: Optional pre-fetched latest report

    Returns:
        dict: Image preview flags and URLs
    """
    if latest_report is None:
        latest_report = _get_latest_report(protocol)

    can_view_report_images = user_can_view_report_images(
        user, protocol, latest_report
    )
    report_image_count = latest_report.images.count() if latest_report else 0
    report_images_preview = (
        _get_report_images_preview(latest_report)
        if can_view_report_images
        else []
    )

    report_images_gallery_url = ""
    if can_view_report_images and report_image_count:
        report_images_gallery_url = reverse(
            "protocols:protocol_report_images",
            kwargs={"pk": protocol.pk},
        )

    return {
        "can_view_report_images": can_view_report_images,
        "report_image_count": report_image_count,
        "report_images_preview": report_images_preview,
        "report_images_gallery_url": report_images_gallery_url,
    }


def build_protocol_report_action_context(user, protocol):
    """
    Build report workflow flags for laboratory staff with report permission.

    Used on protocol detail and processing status when the case is ready
    for diagnosis or report follow-up.
    """
    is_lab_staff = user.is_authenticated and user.is_lab_staff
    user_can_create_reports = _user_can_create_reports(user)
    needs_report_signature = user_requires_report_signature(user)
    latest_report = _get_latest_report(protocol)
    report_actions_enabled = (
        user_can_create_reports and not needs_report_signature
    )

    can_create_report = (
        is_lab_staff
        and report_actions_enabled
        and protocol.status == Protocol.Status.READY
        and latest_report is None
    )
    can_edit_report = (
        is_lab_staff
        and report_actions_enabled
        and latest_report is not None
        and latest_report.can_edit()
    )
    can_send_report = (
        is_lab_staff
        and report_actions_enabled
        and latest_report is not None
        and latest_report.status == Report.Status.FINALIZED
    )
    can_view_report_detail = bool(
        is_lab_staff and report_actions_enabled and latest_report is not None
    )
    can_download_report_pdf = bool(
        latest_report
        and latest_report.status != Report.Status.DRAFT
        and is_lab_staff
        and report_actions_enabled
        and latest_report.signer_has_signature()
    )

    show_report_workflow = (
        is_lab_staff
        and user_can_create_reports
        and (
            protocol.status
            in (Protocol.Status.READY, Protocol.Status.REPORT_SENT)
            or latest_report is not None
        )
    )

    report_primary_label = ""
    report_primary_url = ""
    if can_edit_report and latest_report:
        report_primary_label = _("Continuar elaboración del informe")
        report_primary_url = reverse(
            "protocols:report_edit", kwargs={"pk": latest_report.pk}
        )
    elif can_create_report:
        report_primary_label = _("Elaborar informe")
        report_primary_url = reverse(
            "protocols:report_create", kwargs={"protocol_id": protocol.pk}
        )
    elif can_send_report and latest_report:
        report_primary_label = _("Enviar informe al veterinario")
        report_primary_url = reverse(
            "protocols:report_send", kwargs={"pk": latest_report.pk}
        )
    elif can_view_report_detail and latest_report:
        report_primary_label = _("Ver informe")
        report_primary_url = reverse(
            "protocols:report_detail", kwargs={"pk": latest_report.pk}
        )

    return {
        "latest_report": latest_report,
        "user_can_create_reports": user_can_create_reports,
        "needs_report_signature": needs_report_signature,
        "lab_staff_signature_url": get_report_signature_redirect_url(),
        "can_create_report": can_create_report,
        "can_edit_report": can_edit_report,
        "can_send_report": can_send_report,
        "can_view_report_detail": can_view_report_detail,
        "can_download_report_pdf": can_download_report_pdf,
        "show_report_workflow": show_report_workflow,
        "report_primary_label": report_primary_label,
        "report_primary_url": report_primary_url,
    }


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

    can_view_protocol_processing = user_can_view_protocol_processing(
        user, protocol
    )

    report_context = build_protocol_report_action_context(user, protocol)
    latest_report = report_context["latest_report"]
    images_context = build_protocol_report_images_context(
        user, protocol, latest_report
    )
    user_can_create_reports = report_context["user_can_create_reports"]
    needs_report_signature = report_context["needs_report_signature"]
    lab_staff_signature_url = report_context["lab_staff_signature_url"]
    can_create_report = report_context["can_create_report"]
    can_edit_report = report_context["can_edit_report"]
    can_send_report = report_context["can_send_report"]
    can_view_report_detail = report_context["can_view_report_detail"]
    can_download_report_pdf = report_context["can_download_report_pdf"]
    show_report_workflow = report_context["show_report_workflow"]
    report_primary_label = report_context["report_primary_label"]
    report_primary_url = report_context["report_primary_url"]

    if latest_report and owns_protocol:
        can_view_report_detail = latest_report.status in (
            Report.Status.FINALIZED,
            Report.Status.SENT,
        )
        can_download_report_pdf = can_view_report_detail and bool(
            latest_report.pdf_path
        )
        show_report_workflow = False

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

    can_lab_manage_draft = (
        is_lab_staff and protocol.status == Protocol.Status.DRAFT
    )
    lab_created_protocol = is_lab_created_protocol(protocol)

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
        "can_view_protocol_processing": can_view_protocol_processing,
        "latest_report": latest_report,
        "can_view_report_detail": can_view_report_detail,
        "can_download_report_pdf": can_download_report_pdf,
        "user_can_create_reports": user_can_create_reports,
        "needs_report_signature": needs_report_signature,
        "lab_staff_signature_url": lab_staff_signature_url,
        "processing_readiness": processing_readiness,
        "can_mark_ready": can_mark_ready,
        "can_create_report": can_create_report,
        "can_edit_report": can_edit_report,
        "can_send_report": can_send_report,
        "can_receive_protocol": can_receive_protocol,
        "can_resubmit_protocol": can_resubmit_protocol,
        "can_view_reception_detail": can_view_reception_detail,
        "can_print_reception_label": can_print_reception_label,
        "can_lab_manage_draft": can_lab_manage_draft,
        "lab_created_protocol": lab_created_protocol,
        "public_detail_url": public_detail_url,
        "hide_veterinarian_card": is_veterinarian and owns_protocol,
        "is_protocol_owner": owns_protocol,
        "show_lab_actions": is_lab_staff,
        "show_vet_actions": is_veterinarian and owns_protocol,
        "show_report_workflow": show_report_workflow,
        "report_primary_label": report_primary_label,
        "report_primary_url": report_primary_url,
        **images_context,
    }
