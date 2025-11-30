"""
Email notification service for protocol-related communications.
"""

import logging
from typing import Optional

from protocols.emails import (
    build_protocol_url,
    queue_email,
    send_report_ready_notification,
    send_sample_reception_notification,
    send_work_order_notification,
)
from protocols.models import EmailLog

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service class for handling email notifications related to protocols.

    This service encapsulates all email sending logic and provides a clean
    interface for views to send notifications without dealing with the
    complexity of email queuing and error handling.
    """

    def send_reception_email(self, protocol) -> bool:
        """
        Send reception confirmation email to veterinarian asynchronously.

        Uses Celery-based email system for non-blocking delivery with
        automatic retry logic and preference checking.

        Args:
            protocol: Protocol instance that was received

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            email_log = send_sample_reception_notification(protocol)
            if email_log:
                logger.info(
                    f"Reception email queued for protocol {protocol.pk} "
                    f"(EmailLog ID: {email_log.id})"
                )
                return True
            else:
                logger.info(
                    f"Reception email skipped for protocol {protocol.pk} "
                    "(veterinarian preferences)"
                )
                return False
        except Exception as e:
            logger.error(
                f"Failed to queue reception email for protocol {protocol.pk}: {e}"
            )
            return False

    def send_rejection_email(self, protocol) -> bool:
        """
        Send rejection notification email to veterinarian.

        Args:
            protocol: Protocol instance that was rejected

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            from protocols.emails import send_sample_rejection_notification

            email_log = send_sample_rejection_notification(protocol)
            if email_log:
                logger.info(
                    f"Rejection email queued for protocol {protocol.pk} "
                    f"(EmailLog ID: {email_log.id})"
                )
                return True
            else:
                logger.info(
                    f"Rejection email skipped for protocol {protocol.pk} "
                    "(veterinarian preferences)"
                )
                return False
        except Exception as e:
            logger.error(
                f"Failed to queue rejection email for protocol {protocol.pk}: {e}"
            )
            return False

    def send_submission_confirmation_email(self, protocol) -> bool:
        """
        Send protocol submission confirmation email to veterinarian.

        Args:
            protocol: Protocol instance that was submitted

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            email_log = queue_email(
                email_type=EmailLog.EmailType.CUSTOM,
                recipient_email=protocol.veterinarian.email,
                subject=f"Protocolo {protocol.temporary_code} enviado exitosamente",
                context={
                    "protocol": protocol,
                    "veterinarian": protocol.veterinarian,
                    "protocol_url": build_protocol_url(protocol),
                },
                template_name="emails/protocol_submitted.html",
                protocol=protocol,
                veterinarian=protocol.veterinarian,
            )
            logger.info(
                f"Submission email queued for protocol {protocol.pk} "
                f"(EmailLog ID: {email_log.id})"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to queue submission email for protocol {protocol.pk}: {e}"
            )
            return False

    def send_discrepancy_alert_email(
        self, protocol, discrepancies: str, sample_condition: str
    ) -> bool:
        """
        Send discrepancy alert email when sample issues are found.

        Args:
            protocol: Protocol instance with discrepancies
            discrepancies: String describing the discrepancies found
            sample_condition: Sample condition value

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            email_log = queue_email(
                email_type=EmailLog.EmailType.CUSTOM,
                recipient_email=protocol.veterinarian.email,
                subject=f"Discrepancias encontradas - Protocolo {protocol.protocol_number}",
                context={
                    "protocol": protocol,
                    "veterinarian": protocol.veterinarian,
                    "discrepancies": discrepancies,
                    "sample_condition": protocol.get_sample_condition_display(),
                    "protocol_url": build_protocol_url(protocol),
                },
                template_name="emails/reception_discrepancies.html",
                protocol=protocol,
                veterinarian=protocol.veterinarian,
            )
            logger.info(
                f"Discrepancy alert queued for protocol {protocol.pk} "
                f"(EmailLog ID: {email_log.id})"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to queue discrepancy email for protocol {protocol.pk}: {e}"
            )
            return False

    def send_work_order_notification(self, work_order) -> bool:
        """
        Send work order notification email to veterinarian.

        Args:
            work_order: WorkOrder instance that was created

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            email_logs = send_work_order_notification(
                work_order=work_order,
                work_order_pdf_path=None,  # PDF generation can be added later
            )
            if email_logs:
                logger.info(
                    f"Work order email queued for {work_order.order_number} "
                    f"({len(email_logs)} EmailLog instances)"
                )
                return True
            else:
                logger.info(
                    f"Work order email skipped for {work_order.order_number} "
                    "(veterinarian preferences)"
                )
                return False
        except Exception as e:
            logger.error(
                f"Failed to queue work order email for {work_order.pk}: {e}"
            )
            return False

    def send_report_ready_notification(
        self, report, pdf_path: Optional[str] = None
    ) -> bool:
        """
        Send report ready notification email with PDF attachment.

        Args:
            report: Report instance that was finalized
            pdf_path: Path to the generated PDF file

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        try:
            email_log = send_report_ready_notification(
                protocol=report.protocol, report_pdf_path=pdf_path
            )
            if email_log:
                logger.info(
                    f"Report ready email queued for report {report.pk} "
                    f"(EmailLog ID: {email_log.id})"
                )
                return True
            else:
                logger.info(
                    f"Report ready email skipped for report {report.pk} "
                    "(veterinarian preferences)"
                )
                return False
        except Exception as e:
            logger.error(
                f"Failed to queue report ready email for report {report.pk}: {e}"
            )
            return False
