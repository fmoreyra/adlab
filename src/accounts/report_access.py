"""
Helpers for pathology report access and digital signature requirements.
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from accounts.models import LaboratoryStaff


def get_laboratory_staff_for_reports(user):
    """
    Return the LaboratoryStaff profile for report workflows.

    Uses a direct query to avoid conflicts with User profile properties.
    """
    if not user.is_authenticated:
        return None

    return LaboratoryStaff.objects.filter(user=user).first()


def user_requires_report_signature(user):
    """
    Return whether the user must upload a signature before report work.

    Only applies to lab staff with report creation permission.
    """
    profile = get_laboratory_staff_for_reports(user)
    if not user.is_authenticated or not user.is_lab_staff:
        return False

    if not profile or not profile.can_create_reports or not profile.is_active:
        return False

    return not profile.has_signature()


def get_report_signature_redirect_url():
    """URL where lab staff upload their digital signature."""
    return reverse("accounts:lab_staff_signature")


def report_signature_required_message():
    """User-facing message when a digital signature is missing."""
    return _(
        "Debe cargar su firma digital antes de elaborar, finalizar o "
        "descargar informes patológicos."
    )


def report_signer_missing_message():
    """User-facing message when a report has no assigned signer."""
    return _(
        "El informe no tiene un profesional asignado. Edite el informe o "
        "contacte al administrador."
    )


def report_signer_signature_missing_message():
    """User-facing message when the assigned signer lacks a signature."""
    return _(
        "El profesional asignado al informe no tiene firma digital cargada. "
        "No se puede generar el PDF hasta completar ese dato."
    )
