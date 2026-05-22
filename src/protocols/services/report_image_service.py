"""
Storage and validation for report microscopy images.

Uses Django's default file storage (filesystem locally, Garage/S3 in production).
"""

import logging
import os
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from protocols.report_media import ALLOWED_IMAGE_EXTENSIONS

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_REPORT_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_IMAGES_PER_REPORT = 20


class ReportImageService:
    """Validate uploads and manage stored report image files."""

    @classmethod
    def validate_upload(cls, uploaded_file: UploadedFile) -> None:
        """
        Validate an uploaded microscopy image.

        Args:
            uploaded_file: Django uploaded file

        Raises:
            ValidationError: If file type or size is not allowed
        """
        if not uploaded_file:
            raise ValidationError(_("Debe seleccionar un archivo de imagen."))

        if uploaded_file.size > MAX_REPORT_IMAGE_SIZE_BYTES:
            max_mb = MAX_REPORT_IMAGE_SIZE_BYTES // (1024 * 1024)
            raise ValidationError(
                _("La imagen no puede superar %(max)s MB.") % {"max": max_mb}
            )

        content_type = getattr(uploaded_file, "content_type", "") or ""
        if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ValidationError(
                _("Formato no permitido. Use JPG, PNG o WebP.")
            )

        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension and extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                _("Extensión no permitida. Use JPG, PNG o WebP.")
            )

    @classmethod
    def delete_storage_file(cls, storage_name: Optional[str]) -> None:
        """
        Remove a file from default storage if it exists.

        Args:
            storage_name: Stored object name/path
        """
        if not storage_name:
            return

        try:
            if default_storage.exists(storage_name):
                default_storage.delete(storage_name)
        except Exception as exc:
            logger.warning(
                "Could not delete report image from storage: %s", exc
            )

    @classmethod
    def count_active_images(cls, report) -> int:
        """Return number of images linked to a report."""
        return report.images.count()
