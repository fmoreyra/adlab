"""Helpers for report turnaround-time (TAT) calculations."""

from datetime import timedelta

from django.db.models import Case, DateField, DurationField, F, When
from django.db.models.functions import Cast

from protocols.models import Report


def report_tat_duration_expression():
    """
    Return finalized report TAT as a DurationField expression.

    PostgreSQL returns date differences as intervals; DurationField lets Django
    aggregate them safely before converting to days in Python.
    """
    return Case(
        When(
            status=Report.Status.FINALIZED,
            protocol__reception_date__isnull=False,
            then=F("updated_at__date")
            - Cast(F("protocol__reception_date"), DateField()),
        ),
        default=None,
        output_field=DurationField(),
    )


def report_tat_duration_expression_or_zero():
    """Per-row TAT expression with zero-day default for annotations."""
    return Case(
        When(
            protocol__reception_date__isnull=False,
            then=F("updated_at__date")
            - Cast(F("protocol__reception_date"), DateField()),
        ),
        default=timedelta(0),
        output_field=DurationField(),
    )


def tat_duration_to_days(value, *, default=0):
    """Convert aggregated or annotated TAT values to whole days."""
    if value is None:
        return default
    if isinstance(value, timedelta):
        return value.days
    return value
