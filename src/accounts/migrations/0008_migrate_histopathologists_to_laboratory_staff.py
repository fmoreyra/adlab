"""
Data migration to create LaboratoryStaff profiles for existing Histopathologists.

This migration ensures backward compatibility by creating LaboratoryStaff profiles
for all existing Histopathologist users in production, and optionally creates
Histopathologist profiles for LaboratoryStaff users.
"""

from django.db import migrations


def migrate_histopathologists_to_laboratory_staff(apps, schema_editor):
    """
    Create LaboratoryStaff profiles for all existing Histopathologists.
    Histopathologists can create reports by default.
    """
    Histopathologist = apps.get_model("accounts", "Histopathologist")
    LaboratoryStaff = apps.get_model("accounts", "LaboratoryStaff")

    migrated_count = 0
    skipped_count = 0

    for histo in Histopathologist.objects.select_related("user").all():
        # Check if LaboratoryStaff already exists for this user
        if LaboratoryStaff.objects.filter(user=histo.user).exists():
            skipped_count += 1
            continue

        # Create LaboratoryStaff from Histopathologist data
        LaboratoryStaff.objects.create(
            user=histo.user,
            first_name=histo.first_name,
            last_name=histo.last_name,
            license_number=histo.license_number
            if histo.license_number
            else None,
            position=histo.position,
            specialty=histo.specialty,
            signature_image=histo.signature_image,
            phone_number=histo.phone_number,
            can_create_reports=True,  # Histopathologists can create reports
            is_active=histo.is_active,
        )
        migrated_count += 1

    print(f"Migrated {migrated_count} Histopathologists to LaboratoryStaff")
    print(f"Skipped {skipped_count} (already had LaboratoryStaff)")


def migrate_laboratory_staff_to_histopathologist(apps, schema_editor):
    """
    Create Histopathologist profiles for LaboratoryStaff users who need
    backward compatibility with legacy systems.

    Only creates Histopathologist if LaboratoryStaff.can_create_reports=True.
    """
    LaboratoryStaff = apps.get_model("accounts", "LaboratoryStaff")
    Histopathologist = apps.get_model("accounts", "Histopathologist")

    migrated_count = 0
    skipped_count = 0

    for lab_staff in (
        LaboratoryStaff.objects.select_related("user")
        .filter(can_create_reports=True)
        .all()
    ):
        # Check if Histopathologist already exists
        if Histopathologist.objects.filter(user=lab_staff.user).exists():
            skipped_count += 1
            continue

        # Create Histopathologist from LaboratoryStaff data
        Histopathologist.objects.create(
            user=lab_staff.user,
            first_name=lab_staff.first_name,
            last_name=lab_staff.last_name,
            license_number=lab_staff.license_number
            if lab_staff.license_number
            else None,
            position=lab_staff.position,
            specialty=lab_staff.specialty,
            signature_image=lab_staff.signature_image,
            phone_number=lab_staff.phone_number,
            is_active=lab_staff.is_active,
        )
        migrated_count += 1

    print(
        f"Created {migrated_count} Histopathologist profiles from LaboratoryStaff"
    )
    print(f"Skipped {skipped_count} (already had Histopathologist)")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - removes LaboratoryStaff profiles created from Histopathologists.
    Note: This won't delete LaboratoryStaff that weren't created from Histopathologists.
    """
    print("Reverse migration: LaboratoryStaff profiles kept for data safety")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_laboratorystaff"),
    ]

    operations = [
        # First: Migrate Histopathologists to LaboratoryStaff
        migrations.RunPython(
            migrate_histopathologists_to_laboratory_staff,
            reverse_migration,
        ),
        # Second: Optionally create Histopathologist from LaboratoryStaff for backward compat
        migrations.RunPython(
            migrate_laboratory_staff_to_histopathologist,
            reverse_migration,
        ),
    ]
