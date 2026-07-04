"""
Storage and validation for report microscopy images.

Uses Django's default file storage (filesystem locally, Garage/S3 in production).
"""

import io
import logging
import os
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from protocols.report_media import ALLOWED_IMAGE_EXTENSIONS

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_REPORT_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_IMAGES_PER_REPORT = 20
# Longest edge for PDF embedding (keeps ReportLab fast and memory-safe)
PDF_IMAGE_MAX_EDGE_PX = 1600
PDF_JPEG_QUALITY = 85


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

        # Ensure the payload is a real image (catches corrupt uploads early)
        try:
            uploaded_file.seek(0)
            with PILImage.open(uploaded_file) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError(
                _("El archivo no es una imagen válida.")
            ) from exc
        finally:
            uploaded_file.seek(0)

    @classmethod
    def open_for_pdf(cls, report_image) -> io.BytesIO:
        """
        Load a report image as JPEG bytes suitable for ReportLab.

        Converts WebP/PNG and downscales large photos so PDF generation
        stays reliable and reasonably fast.

        Args:
            report_image: ReportImage instance with an image file

        Returns:
            io.BytesIO: JPEG buffer positioned at start

        Raises:
            ValueError: If the image cannot be opened or converted
        """
        if not report_image.image:
            raise ValueError("Report image has no file")

        try:
            with (
                report_image.image.open("rb") as img_file,
                PILImage.open(img_file) as image,
            ):
                if image.mode not in ("RGB", "L") or image.mode == "L":
                    image = image.convert("RGB")

                max_edge = max(image.size)
                if max_edge > PDF_IMAGE_MAX_EDGE_PX:
                    ratio = PDF_IMAGE_MAX_EDGE_PX / max_edge
                    new_size = (
                        max(1, int(image.width * ratio)),
                        max(1, int(image.height * ratio)),
                    )
                    image = image.resize(new_size, PILImage.Resampling.LANCZOS)

                buffer = io.BytesIO()
                image.save(
                    buffer,
                    format="JPEG",
                    quality=PDF_JPEG_QUALITY,
                    optimize=True,
                )
                buffer.seek(0)
                return buffer
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError(
                f"Cannot prepare report image {report_image.pk} for PDF"
            ) from exc

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
