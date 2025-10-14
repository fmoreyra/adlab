"""
Report generation and management service.
"""

import logging
from typing import Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from protocols.models import (
    CassetteObservation,
    Protocol,
    ProtocolStatusHistory,
    Report,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class ReportGenerationService:
    """
    Service class for report generation and management.

    This service encapsulates all report-related business logic including
    creation, validation, status updates, and data processing.
    """

    def create_report(
        self,
        protocol: Protocol,
        histopathologist: User,
        form_data: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[Report], str]:
        """
        Create a new report for a protocol.

        Args:
            protocol: Protocol instance
            histopathologist: User creating the report
            form_data: Optional form data to populate report fields

        Returns:
            Tuple of (success, report_instance, error_message)
        """
        try:
            # Validate protocol for report creation
            is_valid, error_message = self.validate_protocol_for_report(
                protocol
            )
            if not is_valid:
                return False, None, error_message

            with transaction.atomic():
                # Create basic report first
                # Use histopathologist ID if it's an object, otherwise use as-is
                histopathologist_id = (
                    histopathologist.id
                    if hasattr(histopathologist, "id")
                    else histopathologist
                )

                report = Report.objects.create(
                    protocol=protocol,
                    veterinarian=protocol.veterinarian,
                    histopathologist_id=histopathologist_id,
                    status=Report.Status.DRAFT,
                    version=1,
                )

                # Update with form data if provided
                if form_data:
                    # Update form fields (skip histopathologist for now)
                    for field in [
                        "macroscopic_observations",
                        "microscopic_observations",
                        "diagnosis",
                        "comments",
                        "recommendations",
                    ]:
                        if field in form_data:
                            setattr(report, field, form_data[field])

                    # Save the updated report
                    report.save()

                # Log report creation
                ProtocolStatusHistory.log_status_change(
                    protocol=protocol,
                    new_status=Protocol.Status.PROCESSING,
                    changed_by=histopathologist.user,
                    description="Report created",
                )

                logger.info(
                    f"Report {report.id} created for protocol {protocol.id}"
                )
                return True, report, ""

        except Exception as e:
            logger.error(
                f"Failed to create report for protocol {protocol.id}: {e}"
            )
            return False, None, str(e)

    def validate_protocol_for_report(
        self, protocol: Protocol
    ) -> Tuple[bool, str]:
        """
        Validate that a protocol is ready for report creation.

        Args:
            protocol: Protocol instance to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check protocol status
        if protocol.status != Protocol.Status.READY:
            return False, _(
                "Protocol must be in READY status to create a report"
            )

        # Check if report already exists
        if hasattr(protocol, "report"):
            return False, _("A report already exists for this protocol")

        # Check if protocol has required data
        if not protocol.animal_identification:
            return False, _("Protocol must have animal identification")

        if not protocol.species:
            return False, _("Protocol must have species information")

        return True, ""

    def update_report_content(
        self, report: Report, content_data: Dict, updated_by: User
    ) -> Tuple[bool, str]:
        """
        Update report content with validation.

        Args:
            report: Report instance to update
            content_data: Dictionary containing report content
            updated_by: User making the update

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate report status
            if report.status not in [
                Report.Status.DRAFT,
                Report.Status.FINALIZED,
            ]:
                return False, _(
                    "Report must be in DRAFT or REVIEW status to update content"
                )

            with transaction.atomic():
                # Update report fields
                if "macroscopic_observations" in content_data:
                    report.macroscopic_observations = content_data[
                        "macroscopic_observations"
                    ]

                if "microscopic_observations" in content_data:
                    report.microscopic_observations = content_data[
                        "microscopic_observations"
                    ]

                if "diagnosis" in content_data:
                    report.diagnosis = content_data["diagnosis"]

                if "comments" in content_data:
                    report.comments = content_data["comments"]

                if "recommendations" in content_data:
                    report.recommendations = content_data["recommendations"]

                # Update cassette observations
                if "cassette_observations" in content_data:
                    self._update_cassette_observations(
                        report, content_data["cassette_observations"]
                    )

                report.save()

                # Log content update
                ProtocolStatusHistory.log_status_change(
                    protocol=report.protocol,
                    new_status=report.protocol.status,
                    changed_by=updated_by,
                    description="Report content updated",
                )

                logger.info(
                    f"Report {report.id} content updated by user {updated_by.id}"
                )
                return True, ""

        except Exception as e:
            logger.error(f"Failed to update report {report.id} content: {e}")
            return False, str(e)

    def _update_cassette_observations(
        self, report: Report, observations_data: List[Dict]
    ) -> None:
        """
        Update cassette observations for a report.

        Args:
            report: Report instance
            observations_data: List of observation dictionaries
        """
        # Clear existing observations
        report.cassette_observations.all().delete()

        # Create new observations
        for obs_data in observations_data:
            CassetteObservation.objects.create(
                report=report,
                cassette_id=obs_data["cassette_id"],
                observations=obs_data.get("observations", ""),
                partial_diagnosis=obs_data.get("partial_diagnosis", ""),
                order=obs_data.get("order", 0),
            )

    def finalize_report(
        self, report: Report, finalized_by: User
    ) -> Tuple[bool, str]:
        """
        Finalize a report and change status to FINALIZED.

        Args:
            report: Report instance to finalize
            finalized_by: User finalizing the report

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate report status
            if report.status != Report.Status.DRAFT:
                return False, _("Report must be in DRAFT status to finalize")

            # Validate required fields
            if not report.diagnosis:
                return False, _(
                    "Report must have a diagnosis before finalization"
                )

            with transaction.atomic():
                # Update report status
                report.status = Report.Status.FINALIZED
                report.save(update_fields=["status"])

                # Log finalization
                ProtocolStatusHistory.log_status_change(
                    protocol=report.protocol,
                    new_status=Protocol.Status.READY,
                    changed_by=finalized_by,
                    description="Report finalized",
                )

                # Update protocol status
                protocol = report.protocol
                protocol.status = Protocol.Status.REPORT_SENT
                protocol.save(update_fields=["status"])

                logger.info(
                    f"Report {report.id} finalized by user {finalized_by.id}"
                )
                return True, ""

        except Exception as e:
            logger.error(f"Failed to finalize report {report.id}: {e}")
            return False, str(e)

    def send_report(self, report: Report, sent_by: User) -> Tuple[bool, str]:
        """
        Mark report as sent to veterinarian.

        Args:
            report: Report instance to send
            sent_by: User sending the report

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate report status
            if report.status != Report.Status.FINALIZED:
                return False, _("Report must be finalized before sending")

            with transaction.atomic():
                # Update report status and sent date
                report.status = Report.Status.SENT
                report.sent_date = timezone.now()
                report.save(update_fields=["status", "sent_date"])

                # Log sending
                ProtocolStatusHistory.log_status_change(
                    protocol=report.protocol,
                    new_status=Protocol.Status.REPORT_SENT,
                    changed_by=sent_by,
                    description="Report sent to veterinarian",
                )

                logger.info(f"Report {report.id} sent by user {sent_by.id}")
                return True, ""

        except Exception as e:
            logger.error(f"Failed to send report {report.id}: {e}")
            return False, str(e)

    def get_report_data(self, report: Report) -> Dict:
        """
        Get comprehensive report data for display or processing.

        Args:
            report: Report instance

        Returns:
            Dictionary containing all report data
        """
        try:
            # Get basic report data
            report_data = {
                "id": report.id,
                "protocol_number": report.protocol.protocol_number,
                "report_date": report.report_date,
                "version": report.version,
                "status": report.status,
                "status_display": report.get_status_display(),
                "veterinarian": {
                    "name": report.veterinarian.get_full_name(),
                    "license": report.veterinarian.license_number,
                    "email": report.veterinarian.email,
                },
                "histopathologist": {
                    "name": report.histopathologist.get_formal_name(),
                    "license": report.histopathologist.license_number,
                },
                "patient": {
                    "species": report.protocol.species,
                    "breed": report.protocol.breed,
                    "age": report.protocol.age,
                    "sex": report.protocol.get_sex_display(),
                    "identification": report.protocol.animal_identification,
                },
                "content": {
                    "macroscopic_observations": report.macroscopic_observations,
                    "microscopic_observations": report.microscopic_observations,
                    "diagnosis": report.diagnosis,
                    "comments": report.comments,
                    "recommendations": report.recommendations,
                },
                "cassette_observations": [],
                "status_history": [],
            }

            # Get cassette observations
            for obs in report.cassette_observations.select_related(
                "cassette"
            ).order_by("order"):
                report_data["cassette_observations"].append(
                    {
                        "cassette_code": obs.cassette.codigo_cassette,
                        "observations": obs.observations,
                        "partial_diagnosis": obs.partial_diagnosis,
                        "order": obs.order,
                    }
                )

            # Get status history
            for history in report.status_history.select_related(
                "changed_by"
            ).order_by("created_at"):
                report_data["status_history"].append(
                    {
                        "status": history.status,
                        "status_display": history.get_status_display(),
                        "changed_by": history.changed_by.get_full_name(),
                        "created_at": history.created_at,
                        "description": history.description,
                    }
                )

            return report_data

        except Exception as e:
            logger.error(
                f"Failed to get report data for report {report.id}: {e}"
            )
            return {}

    def validate_report_content(
        self, content_data: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate report content data.

        Args:
            content_data: Dictionary containing report content

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not content_data.get("diagnosis", "").strip():
            errors.append(_("Diagnosis is required"))

        # Validate diagnosis length
        diagnosis = content_data.get("diagnosis", "")
        if len(diagnosis) > 1000:
            errors.append(_("Diagnosis is too long (maximum 1000 characters)"))

        # Validate observations length
        macroscopic = content_data.get("macroscopic_observations", "")
        if len(macroscopic) > 2000:
            errors.append(
                _(
                    "Macroscopic observations are too long (maximum 2000 characters)"
                )
            )

        microscopic = content_data.get("microscopic_observations", "")
        if len(microscopic) > 2000:
            errors.append(
                _(
                    "Microscopic observations are too long (maximum 2000 characters)"
                )
            )

        # Validate cassette observations
        cassette_observations = content_data.get("cassette_observations", [])
        for i, obs in enumerate(cassette_observations):
            if not obs.get("cassette_id"):
                errors.append(
                    _(f"Cassette observation {i + 1} is missing cassette ID")
                )

            if len(obs.get("observations", "")) > 1000:
                errors.append(
                    _(
                        f"Cassette observation {i + 1} observations are too long"
                    )
                )

        return len(errors) == 0, errors

    def get_reports_for_histopathologist(
        self, histopathologist: User, status_filter: Optional[str] = None
    ) -> List[Report]:
        """
        Get reports assigned to a specific histopathologist.

        Args:
            histopathologist: User instance
            status_filter: Optional status filter

        Returns:
            List of Report instances
        """
        queryset = (
            Report.objects.filter(histopathologist=histopathologist)
            .select_related(
                "protocol__veterinarian__user", "veterinarian__user"
            )
            .order_by("-created_at")
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return list(queryset)

    def get_reports_for_veterinarian(
        self, veterinarian, status_filter: Optional[str] = None
    ) -> List[Report]:
        """
        Get reports for a specific veterinarian.

        Args:
            veterinarian: Veterinarian instance
            status_filter: Optional status filter

        Returns:
            List of Report instances
        """
        queryset = (
            Report.objects.filter(veterinarian=veterinarian)
            .select_related("protocol", "histopathologist")
            .order_by("-created_at")
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return list(queryset)

    def create_report_version(
        self, report: Report, created_by: User
    ) -> Tuple[bool, Optional[Report], str]:
        """
        Create a new version of an existing report.

        Args:
            report: Original report instance
            created_by: User creating the new version

        Returns:
            Tuple of (success, new_report_instance, error_message)
        """
        try:
            # Validate original report
            if report.status not in [
                Report.Status.FINALIZED,
                Report.Status.SENT,
            ]:
                return (
                    False,
                    None,
                    _("Can only create versions of finalized or sent reports"),
                )

            with transaction.atomic():
                # Create new version
                new_report = Report.objects.create(
                    protocol=report.protocol,
                    veterinarian=report.veterinarian,
                    histopathologist=created_by,
                    status=Report.Status.DRAFT,
                    version=report.version + 1,
                    macroscopic_observations=report.macroscopic_observations,
                    microscopic_observations=report.microscopic_observations,
                    diagnosis=report.diagnosis,
                    comments=report.comments,
                    recommendations=report.recommendations,
                )

                # Copy cassette observations
                for obs in report.cassette_observations.all():
                    CassetteObservation.objects.create(
                        report=new_report,
                        cassette=obs.cassette,
                        observations=obs.observations,
                        partial_diagnosis=obs.partial_diagnosis,
                        order=obs.order,
                    )

                # Log version creation
                ProtocolStatusHistory.log_status_change(
                    protocol=new_report.protocol,
                    new_status=Protocol.Status.PROCESSING,
                    changed_by=created_by,
                    description=f"New version created from report {report.id}",
                )

                logger.info(
                    f"Report version {new_report.version} created for protocol {report.protocol.id}"
                )
                return True, new_report, ""

        except Exception as e:
            logger.error(
                f"Failed to create report version for report {report.id}: {e}"
            )
            return False, None, str(e)
