"""Normalize empty string license_number / dni to NULL.

PostgreSQL unique constraints treat '' as a real value, so only one
veterinarian could omit license_number before this normalization.
Multiple NULLs are allowed under the same unique constraint.
"""

from django.db import migrations


def normalize_empty_unique_fields(apps, schema_editor):
    """Convert empty unique optional strings to NULL."""
    Veterinarian = apps.get_model("accounts", "Veterinarian")
    Veterinarian.objects.filter(license_number="").update(license_number=None)
    Veterinarian.objects.filter(dni="").update(dni=None)


def noop_reverse(apps, schema_editor):
    """No reverse: NULL is the correct representation for unset values."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_veterinarian_approval"),
    ]

    operations = [
        migrations.RunPython(normalize_empty_unique_fields, noop_reverse),
    ]
