"""Normalize legacy PAAF cytology technique values to canonical label."""

from django.db import migrations

CANONICAL_PAAF = "Punción (PAAF)"

LEGACY_PAAF_VALUES = (
    "PAAF",
    "Punción aspiración con aguja fina (PAAF)",
)


def normalize_paaf_techniques(apps, schema_editor):
    """Map legacy PAAF strings to the canonical choice label."""
    CytologySample = apps.get_model("protocols", "CytologySample")
    CytologySample.objects.filter(
        technique_used__in=LEGACY_PAAF_VALUES
    ).update(technique_used=CANONICAL_PAAF)


class Migration(migrations.Migration):
    dependencies = [
        ("protocols", "0019_notification_link_url_charfield"),
    ]

    operations = [
        migrations.RunPython(
            normalize_paaf_techniques,
            migrations.RunPython.noop,
        ),
    ]
