"""
Helpers for pathology report access and digital signature requirements.
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.models import Histopathologist, LaboratoryStaff


def get_laboratory_staff_for_reports(user):
    """
    Return the LaboratoryStaff profile for report workflows.

    Uses a direct query to avoid conflicts with User profile properties.
    """
    if not user.is_authenticated:
        return None

    return LaboratoryStaff.objects.filter(user=user).first()


def get_report_finalizer_staff(user):
    """
    Return the LaboratoryStaff profile that will sign/finalize a report.

    Prefers an existing LaboratoryStaff row; falls back to creating one
    from legacy Histopathologist data when needed.
    """
    profile = get_laboratory_staff_for_reports(user)
    if profile:
        return profile

    return get_or_create_laboratory_staff_profile(user)


def get_lab_staff_profile_for_signature(user):
    """
    Return the active lab staff profile used for signature checks.

    Prefers LaboratoryStaff; falls back to legacy Histopathologist.
    """
    if not user.is_authenticated or not user.is_lab_staff:
        return None

    staff = LaboratoryStaff.objects.filter(user=user).first()
    if staff:
        return staff

    try:
        return user.histopathologist_profile
    except Histopathologist.DoesNotExist:
        return None


def get_or_create_laboratory_staff_profile(user):
    """
    Return LaboratoryStaff for signature upload, creating from legacy data if needed.

    Args:
        user: Authenticated lab staff or admin user.

    Returns:
        LaboratoryStaff or None if no profile source exists.
    """
    existing = LaboratoryStaff.objects.filter(user=user).first()
    if existing:
        return existing

    try:
        histo = user.histopathologist_profile
    except Histopathologist.DoesNotExist:
        histo = None

    if histo:
        return LaboratoryStaff.objects.create(
            user=user,
            first_name=histo.first_name,
            last_name=histo.last_name,
            license_number=histo.license_number or "",
            position=histo.position,
            specialty=histo.specialty,
            phone_number=histo.phone_number,
            signature_image=histo.signature_image,
            can_create_reports=True,
            is_active=histo.is_active,
        )

    # Admins may send/finalize reports without a prior LabStaff row; create one
    # so they can upload a signature before those actions.
    if user.is_admin_user:
        first_name = (user.first_name or "").strip() or user.email.split("@")[
            0
        ]
        last_name = (user.last_name or "").strip() or "Administrador"
        return LaboratoryStaff.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            license_number="",
            can_create_reports=True,
            is_active=True,
        )

    return None


def user_requires_lab_staff_signature(user):
    """
    Return whether lab staff must upload a digital signature to continue.

    Applies to all laboratory staff with an active profile, not only report authors.
    """
    profile = get_lab_staff_profile_for_signature(user)
    if (
        not user.is_authenticated
        or not user.is_lab_staff
        or user.is_admin_user
    ):
        return False

    if not profile or not profile.is_active:
        return False

    return not profile.has_signature()


def _profile_can_create_reports(profile):
    """Return whether a staff profile may create pathology reports."""
    if isinstance(profile, LaboratoryStaff):
        return profile.can_create_reports and profile.is_active

    return profile.is_active


def user_requires_report_signature(user):
    """
    Return whether the user must upload a signature before report work.

    Applies to lab staff with report permission and to admins (who can send
    or finalize reports via staff access). Missing LaboratoryStaff profile
    or missing signature image both require the upload step.
    """
    if not user.is_authenticated or not user.is_lab_staff:
        return False

    profile = get_laboratory_staff_for_reports(user)
    if not profile:
        profile = get_lab_staff_profile_for_signature(user)

    # Admins may reach send/finalize without can_create_reports; still require
    # a signable profile so the PDF workflow never proceeds unsigned.
    if user.is_admin_user:
        if not profile:
            return True
        return not profile.has_signature()

    if not profile or not _profile_can_create_reports(profile):
        return False

    return not profile.has_signature()


def get_report_signature_redirect_url():
    """URL where lab staff upload their digital signature."""
    return reverse("accounts:lab_staff_signature")


def report_signature_required_message():
    """User-facing message when a digital signature is missing."""
    return _(
        "Debe cargar su firma digital antes de elaborar, finalizar, enviar "
        "o descargar informes patológicos."
    )


def lab_staff_signature_required_message():
    """User-facing message when onboarding signature is missing."""
    return _(
        "Debe cargar su firma digital para completar su incorporación "
        "al laboratorio."
    )


def report_signer_missing_message():
    """User-facing message when a report has no assigned signer (lab staff)."""
    return _(
        "El informe no tiene un profesional asignado. Genere el PDF como "
        "firmante o contacte al administrador."
    )


def report_pdf_unavailable_for_owner_message():
    """User-facing message when a veterinarian cannot obtain the PDF yet."""
    return _(
        "El PDF del informe no está disponible todavía. "
        "Por favor contacte al laboratorio para que lo regenere."
    )


def user_can_view_report_images(user, protocol, report):
    """
    Return whether the user may view microscopy images for a report.

    Lab staff and admins may view images on any report that has them.
    Veterinarians may view images only on their own finalized or sent reports.
    """
    if not user.is_authenticated or not report:
        return False

    if not report.images.exists():
        return False

    if user.is_admin_user or user.is_lab_staff:
        return True

    if not user.is_veterinarian:
        return False

    try:
        veterinarian = user.veterinarian_profile
    except Exception:
        return False

    if protocol.veterinarian_id != veterinarian.pk:
        return False

    from protocols.models import Report

    return report.status in (Report.Status.FINALIZED, Report.Status.SENT)


def report_signer_signature_missing_message():
    """User-facing message when the assigned signer lacks a signature."""
    return _(
        "El profesional asignado al informe no tiene firma digital cargada. "
        "No se puede generar el PDF hasta completar ese dato."
    )
