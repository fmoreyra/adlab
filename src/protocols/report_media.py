"""
Upload paths and constants for report microscopy images.

Kept separate from services to avoid circular imports with protocols.models.
"""

import os
import uuid

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def report_image_upload_to(instance, filename: str) -> str:
    """
    Build storage path for a report microscopy image.

    Args:
        instance: ReportImage instance (report_id may be unset on first save)
        filename: Original uploaded filename

    Returns:
        str: Relative path under the default storage backend
    """
    extension = os.path.splitext(filename)[1].lower() or ".jpg"
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        extension = ".jpg"
    unique_name = uuid.uuid4().hex
    report_id = instance.report_id or "pending"
    return f"reports/{report_id}/images/{unique_name}{extension}"
