"""
Helpers for laboratory staff delegated protocol creation.
"""

from django.db.models import Q

from accounts.models import Veterinarian

LAB_PROTOCOL_VET_SESSION_KEY = "lab_protocol_veterinarian_id"


def get_enabled_veterinarians_queryset():
    """
    Return veterinarians eligible for lab-delegated protocol creation.

    Requires verified email, active user account, and admin approval.
    """
    return (
        Veterinarian.objects.filter(
            user__is_active=True,
            user__email_verified=True,
            is_verified=True,
        )
        .exclude(email="")
        .select_related("user")
        .order_by("last_name", "first_name")
    )


def search_enabled_veterinarians(query: str):
    """
    Search enabled veterinarians by name, license, or email.

    Args:
        query: Free-text search term.

    Returns:
        QuerySet: Matching veterinarians (may be empty).
    """
    query = (query or "").strip()
    if not query:
        return Veterinarian.objects.none()

    return get_enabled_veterinarians_queryset().filter(
        Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(license_number__icontains=query)
        | Q(email__icontains=query)
    )


def get_lab_protocol_veterinarian(session):
    """
    Load the veterinarian selected for lab protocol creation from session.

    Args:
        session: Django session store.

    Returns:
        Veterinarian | None: Selected vet if still enabled, else None.
    """
    vet_id = session.get(LAB_PROTOCOL_VET_SESSION_KEY)
    if not vet_id:
        return None

    return get_enabled_veterinarians_queryset().filter(pk=vet_id).first()


def set_lab_protocol_veterinarian(session, veterinarian):
    """
    Persist the selected veterinarian for the lab create flow.

    Args:
        session: Django session store.
        veterinarian: Veterinarian instance to store.
    """
    session[LAB_PROTOCOL_VET_SESSION_KEY] = veterinarian.pk


def clear_lab_protocol_veterinarian(session):
    """Remove the lab protocol veterinarian from session."""
    session.pop(LAB_PROTOCOL_VET_SESSION_KEY, None)


def is_lab_created_protocol(protocol) -> bool:
    """
    Return whether the protocol was loaded by laboratory staff.

    Args:
        protocol: Protocol instance (optionally with created_by loaded).

    Returns:
        bool: True when created_by is lab staff.
    """
    created_by = getattr(protocol, "created_by", None)
    if created_by is None:
        return False
    return created_by.is_lab_staff
