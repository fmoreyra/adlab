"""
Reset operational data while preserving user accounts and profiles.

Used before domain migration to start with a clean protocol workflow
while keeping veterinarians, lab staff, and admin accounts intact.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import transaction

from accounts.models import PasswordResetToken
from pages.models import DashboardAnnouncement, ServerStatsSnapshot
from protocols.models import (
    Cassette,
    CassetteObservation,
    CassetteSlide,
    EmailLog,
    InAppNotification,
    ProcessingLog,
    Protocol,
    ProtocolCounter,
    ProtocolStatusHistory,
    ReceptionLog,
    Report,
    ReportImage,
    Slide,
    TemporaryCodeCounter,
    WorkOrder,
    WorkOrderCounter,
    WorkOrderService,
)

if TYPE_CHECKING:
    from django.db.models import Model


@dataclass(frozen=True)
class DeletionStep:
    """One bulk-delete step with a human-readable label."""

    label: str
    model: type[Model]


# Order matters: PROTECT FKs on Protocol must be cleared before Protocol rows.
DELETION_STEPS: tuple[DeletionStep, ...] = (
    DeletionStep("report images", ReportImage),
    DeletionStep("cassette observations", CassetteObservation),
    DeletionStep("reports", Report),
    DeletionStep("cassette-slide links", CassetteSlide),
    DeletionStep("processing logs", ProcessingLog),
    DeletionStep("slides", Slide),
    DeletionStep("cassettes", Cassette),
    DeletionStep("email logs", EmailLog),
    DeletionStep("in-app notifications", InAppNotification),
    DeletionStep("protocol status history", ProtocolStatusHistory),
    DeletionStep("reception logs", ReceptionLog),
    DeletionStep("work order services", WorkOrderService),
    DeletionStep("work orders", WorkOrder),
    DeletionStep("protocols", Protocol),
    DeletionStep("protocol counters", ProtocolCounter),
    DeletionStep("temporary code counters", TemporaryCodeCounter),
    DeletionStep("work order counters", WorkOrderCounter),
)


def count_business_rows(*, include_pricing: bool) -> dict[str, int]:
    """
    Return row counts for models removed by reset_business_data.

    Args:
        include_pricing: When False, include PricingCatalog in counts.

    Returns:
        dict mapping label to queryset count.
    """
    from protocols.models import PricingCatalog

    counts = {
        step.label: step.model.objects.count() for step in DELETION_STEPS
    }
    counts["password reset tokens"] = PasswordResetToken.objects.count()
    counts["dashboard announcements"] = DashboardAnnouncement.objects.count()
    counts["server stats snapshots"] = ServerStatsSnapshot.objects.count()
    counts["sessions"] = Session.objects.count()
    if not include_pricing:
        counts["pricing catalog"] = PricingCatalog.objects.count()
    return counts


def clear_report_media_files() -> bool:
    """
    Remove uploaded report PDFs and microscopy images from storage.

    Signature files under signatures/ are preserved.

    Returns:
        True if any report media was removed.
    """
    if getattr(settings, "USE_S3_STORAGE", False):
        return _clear_report_media_s3()

    reports_path = os.path.join(settings.MEDIA_ROOT, "reports")
    if not os.path.isdir(reports_path):
        return False

    shutil.rmtree(reports_path)
    return True


def _clear_report_media_s3() -> bool:
    """Delete objects under the reports/ prefix in object storage."""
    from django.core.files.storage import default_storage

    removed = False
    try:
        _dirs, files = default_storage.listdir("reports")
    except FileNotFoundError:
        return False
    except OSError:
        return False

    for name in files:
        default_storage.delete(os.path.join("reports", name))
        removed = True

    for directory in _dirs:
        prefix = os.path.join("reports", directory)
        for path in _iter_storage_paths(prefix):
            default_storage.delete(path)
            removed = True

    return removed


def _iter_storage_paths(prefix: str) -> list[str]:
    """Recursively list storage paths under prefix."""
    from django.core.files.storage import default_storage

    paths: list[str] = []
    try:
        directories, files = default_storage.listdir(prefix)
    except (FileNotFoundError, OSError):
        return paths

    for name in files:
        paths.append(os.path.join(prefix, name))
    for directory in directories:
        paths.extend(_iter_storage_paths(os.path.join(prefix, directory)))
    return paths


@transaction.atomic
def reset_business_data(
    *, keep_pricing: bool = True, clear_media: bool = True
) -> dict[str, int]:
    """
    Delete operational data and reset counters; keep user accounts and profiles.

    Args:
        keep_pricing: When True, retain PricingCatalog rows.
        clear_media: When True, delete media/reports/ from storage.

    Returns:
        dict mapping label to number of rows deleted per step.
    """
    deleted: dict[str, int] = {}

    for step in DELETION_STEPS:
        count, _ = step.model.objects.all().delete()
        deleted[step.label] = count

    from protocols.models import PricingCatalog

    deleted["password reset tokens"] = _delete_all(PasswordResetToken)
    deleted["dashboard announcements"] = _delete_all(DashboardAnnouncement)
    deleted["server stats snapshots"] = _delete_all(ServerStatsSnapshot)
    deleted["sessions"] = Session.objects.all().delete()[0]

    if not keep_pricing:
        deleted["pricing catalog"] = _delete_all(PricingCatalog)

    if clear_media:
        deleted["report media cleared"] = int(clear_report_media_files())

    return deleted


def _delete_all(model: type[Model]) -> int:
    """Delete all rows for model; return deleted count."""
    count, _ = model.objects.all().delete()
    return count
