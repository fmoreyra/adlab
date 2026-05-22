"""
Shared factories for Django tests.

Ensures veterinarian profiles satisfy VeterinarianProfileRequiredMiddleware and
lab staff can access report workflows (signature upload).
"""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import Address, LaboratoryStaff, User, Veterinarian

DEFAULT_CUIL_CUIT = "20-12345678-9"
DEFAULT_ADDRESS = {
    "province": "Santa Fe",
    "locality": "Rosario",
    "street": "San Martín",
    "number": "100",
}


def create_test_signature_file(name="sig.png"):
    """
    Build a minimal PNG suitable for ImageField and ReportLab.

    Returns:
        SimpleUploadedFile: PNG upload for signature_image fields.
    """
    try:
        from PIL import Image
    except ImportError:
        return SimpleUploadedFile(
            name,
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            content_type="image/png",
        )

    buffer = BytesIO()
    Image.new("RGB", (40, 20), "white").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name,
        buffer.read(),
        content_type="image/png",
    )


def ensure_veterinarian_profile_complete(
    veterinarian,
    *,
    cuil_cuit=DEFAULT_CUIL_CUIT,
    address_kwargs=None,
):
    """
    Add required fields so is_profile_complete_for_access() is True.

    Args:
        veterinarian: Veterinarian instance to complete.
        cuil_cuit: CUIL/CUIT value when missing.
        address_kwargs: Optional overrides for Address fields.

    Returns:
        Veterinarian: The same instance (refreshed from DB if updated).
    """
    update_fields = []
    if not veterinarian.cuil_cuit:
        veterinarian.cuil_cuit = cuil_cuit
        update_fields.append("cuil_cuit")
    if update_fields:
        veterinarian.save(update_fields=update_fields)

    if not Address.objects.filter(veterinarian=veterinarian).exists():
        Address.objects.create(
            veterinarian=veterinarian,
            **{**DEFAULT_ADDRESS, **(address_kwargs or {})},
        )

    return veterinarian


def create_complete_veterinarian_user(
    *,
    email="vet@example.com",
    username="vet",
    password="testpass123",
    email_verified=True,
    vet_kwargs=None,
    address_kwargs=None,
):
    """
    Create a user + veterinarian with a complete profile for middleware.

    Returns:
        tuple[User, Veterinarian]: Authenticated-ready veterinarian account.
    """
    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
        role=User.Role.VETERINARIO,
        email_verified=email_verified,
    )
    vet_data = {
        "user": user,
        "first_name": "Juan",
        "last_name": "Pérez",
        "license_number": "MP-12345",
        "phone": "+54 341 1234567",
        "email": email,
        "cuil_cuit": DEFAULT_CUIL_CUIT,
    }
    if vet_kwargs:
        vet_data.update(vet_kwargs)
    veterinarian = Veterinarian.objects.create(**vet_data)
    ensure_veterinarian_profile_complete(
        veterinarian,
        cuil_cuit=vet_data.get("cuil_cuit", DEFAULT_CUIL_CUIT),
        address_kwargs=address_kwargs,
    )
    return user, veterinarian


def create_report_capable_lab_staff(
    *,
    email="staff@example.com",
    username="staff",
    password="testpass123",
    with_signature=True,
    staff_kwargs=None,
):
    """
    Create lab staff that can access report views (signature when required).

    Returns:
        tuple[User, LaboratoryStaff]: Staff user and profile.
    """
    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
        role=User.Role.PERSONAL_LAB,
        email_verified=True,
        is_staff=True,
    )
    lab_data = {
        "user": user,
        "first_name": "Staff",
        "last_name": "Test",
        "license_number": f"LAB-{username}",
        "can_create_reports": True,
        "is_active": True,
    }
    if with_signature:
        lab_data["signature_image"] = create_test_signature_file()
    if staff_kwargs:
        lab_data.update(staff_kwargs)
    laboratory_staff = LaboratoryStaff.objects.create(**lab_data)
    return user, laboratory_staff
