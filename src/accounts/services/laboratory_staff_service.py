"""Services for laboratory staff profile management."""

from accounts.models import LaboratoryStaff


def migrate_histopathologist_to_laboratory_staff(histopathologist):
    """
    Create a LaboratoryStaff profile from a Histopathologist if missing.

    Args:
        histopathologist: Histopathologist instance to migrate.

    Returns:
        tuple[LaboratoryStaff | None, bool]: Profile and whether it was created.
    """
    user = histopathologist.user
    existing_profile = LaboratoryStaff.objects.filter(user=user).first()
    if existing_profile:
        return existing_profile, False

    lab_staff = LaboratoryStaff.objects.create(
        user=user,
        first_name=histopathologist.first_name,
        last_name=histopathologist.last_name,
        license_number=histopathologist.license_number or "",
        position=histopathologist.position,
        specialty=histopathologist.specialty,
        signature_image=histopathologist.signature_image,
        signature_affiliation_text=getattr(
            histopathologist,
            "signature_affiliation_text",
            "",
        )
        or (
            "Laboratorio de Anatomía Patológica\n"
            "Facultad de Ciencias Veterinarias"
        ),
        phone_number=histopathologist.phone_number,
        can_create_reports=True,
        is_active=histopathologist.is_active,
    )
    return lab_staff, True


def migrate_histopathologists_to_laboratory_staff(histopathologists):
    """
    Bulk-create LaboratoryStaff profiles for histopathologists.

    Args:
        histopathologists: Iterable of Histopathologist instances.

    Returns:
        dict: Counts with keys ``created`` and ``skipped``.
    """
    created = 0
    skipped = 0

    for histopathologist in histopathologists:
        _, was_created = migrate_histopathologist_to_laboratory_staff(
            histopathologist
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    return {"created": created, "skipped": skipped}
