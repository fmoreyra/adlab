"""Expand short signature captions to include name and license.

The free-text field is now the full PDF caption under the signature image.
Existing rows that only had the institution lines are expanded so PDFs do
not lose the professional name/matrícula after removing auto-generated lines.
"""

from django.db import migrations

INSTITUTION_DEFAULT = (
    "Laboratorio de Anatomía Patológica\n" "Facultad de Ciencias Veterinarias"
)


def _expand_caption(first_name, last_name, license_number, current):
    """Return an expanded caption when the stored text is the short default."""
    text = (current or "").strip()
    if text and text != INSTITUTION_DEFAULT:
        return None

    full_name = (
        f"{first_name or ''} {last_name or ''}".strip() or "Profesional"
    )
    lines = [f"Dr./Dra. {full_name}"]
    if license_number:
        lines.append(f"Mat. {license_number}")
    lines.extend(INSTITUTION_DEFAULT.splitlines())
    return "\n".join(lines)


def expand_short_affiliation_captions(apps, schema_editor):
    """Expand legacy 2-line affiliation captions for existing signers."""
    LaboratoryStaff = apps.get_model("accounts", "LaboratoryStaff")
    Histopathologist = apps.get_model("accounts", "Histopathologist")

    for staff in LaboratoryStaff.objects.all().iterator():
        updated = _expand_caption(
            staff.first_name,
            staff.last_name,
            staff.license_number,
            staff.signature_affiliation_text,
        )
        if updated:
            staff.signature_affiliation_text = updated
            staff.save(update_fields=["signature_affiliation_text"])

    for histo in Histopathologist.objects.all().iterator():
        updated = _expand_caption(
            histo.first_name,
            histo.last_name,
            histo.license_number,
            histo.signature_affiliation_text,
        )
        if updated:
            histo.signature_affiliation_text = updated
            histo.save(update_fields=["signature_affiliation_text"])


def noop_reverse(apps, schema_editor):
    """No reverse: expanded captions remain valid free-text values."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_signature_affiliation_text"),
    ]

    operations = [
        migrations.RunPython(expand_short_affiliation_captions, noop_reverse),
    ]
