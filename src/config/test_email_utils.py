"""Tests for email recipient override and daily send metrics."""

from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone

from config.email_utils import (
    annotate_subject_for_override,
    build_email_quota_metrics,
    count_emails_sent_on,
    count_emails_sent_rolling_24h,
    is_smtp_quota_error,
    resolve_recipient_email,
)
from protocols.emails import queue_email
from protocols.models import EmailLog


class EmailRecipientOverrideTests(TestCase):
    """Tests for EMAIL_RECIPIENT_OVERRIDE behavior."""

    def test_resolve_without_override(self):
        """Intended recipient is used when override is unset."""
        with override_settings(EMAIL_RECIPIENT_OVERRIDE=""):
            self.assertEqual(
                resolve_recipient_email("vet@example.com"),
                "vet@example.com",
            )

    @override_settings(EMAIL_RECIPIENT_OVERRIDE="override@example.com")
    def test_resolve_with_override(self):
        """Override replaces intended recipient."""
        self.assertEqual(
            resolve_recipient_email("vet@example.com"),
            "override@example.com",
        )

    @override_settings(EMAIL_RECIPIENT_OVERRIDE="override@example.com")
    def test_subject_annotated_when_overridden(self):
        """Subject notes the logical recipient when override is active."""
        subject = annotate_subject_for_override(
            "Informe listo", "vet@example.com"
        )
        self.assertIn("vet@example.com", subject)
        self.assertIn("Informe listo", subject)

    @patch("protocols.emails.send_email.delay")
    @override_settings(EMAIL_RECIPIENT_OVERRIDE="override@example.com")
    def test_queue_email_uses_override(self, mock_delay):
        """queue_email delivers to override and logs that address."""
        mock_delay.return_value = MagicMock(id="task-1")

        log = queue_email(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="vet@example.com",
            subject="Test",
            context={},
        )

        self.assertEqual(log.recipient_email, "override@example.com")
        self.assertIn("vet@example.com", log.subject)
        mock_delay.assert_called_once()
        self.assertEqual(
            mock_delay.call_args.kwargs["recipient_email"],
            "override@example.com",
        )


class EmailDailyMetricsTests(TestCase):
    """Tests for count_emails_sent_on."""

    def test_count_sent_on_day(self):
        """Counts only SENT rows with sent_at on the given day."""
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today, time(12, 0)))

        EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="a@example.com",
            subject="OK",
            celery_task_id="sync-test-1",
            status=EmailLog.Status.SENT,
            sent_at=start,
        )
        EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="b@example.com",
            subject="Queued",
            celery_task_id="pending-test-2",
            status=EmailLog.Status.QUEUED,
        )

        metrics = count_emails_sent_on(today)

        self.assertEqual(metrics["sent"], 1)
        self.assertEqual(metrics["queued"], 1)
        self.assertEqual(metrics["limit"], 500)
        self.assertEqual(metrics["remaining"], 499)

    @override_settings(EMAIL_DAILY_LIMIT=100)
    def test_custom_daily_limit(self):
        """EMAIL_DAILY_LIMIT is reflected in metrics."""
        metrics = count_emails_sent_on(date.today())
        self.assertEqual(metrics["limit"], 100)


class SmtpQuotaErrorTests(TestCase):
    """Tests for SMTP quota error detection."""

    def test_detects_gmail_quota_code(self):
        """Recognizes Gmail 5.4.5 daily limit errors."""
        message = (
            "550 5.4.5 Daily user sending limit exceeded. " "gmail.com gsmtp"
        )
        self.assertTrue(is_smtp_quota_error(message))

    def test_ignores_unrelated_errors(self):
        """Does not flag generic SMTP failures."""
        self.assertFalse(is_smtp_quota_error("Connection refused"))


class EmailRollingMetricsTests(TestCase):
    """Tests for rolling 24-hour send metrics."""

    def test_count_sent_in_rolling_window(self):
        """Counts SENT rows in the last 24 hours only."""
        now = timezone.now()
        inside = now - timedelta(hours=2)
        outside = now - timedelta(hours=30)

        EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="recent@example.com",
            subject="Recent",
            celery_task_id="sync-recent",
            status=EmailLog.Status.SENT,
            sent_at=inside,
        )
        EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="old@example.com",
            subject="Old",
            celery_task_id="sync-old",
            status=EmailLog.Status.SENT,
            sent_at=outside,
        )
        failed_log = EmailLog.objects.create(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email="fail@example.com",
            subject="Quota",
            celery_task_id="sync-fail",
            status=EmailLog.Status.FAILED,
            error_message="550 5.4.5 Daily user sending limit exceeded",
        )
        EmailLog.objects.filter(pk=failed_log.pk).update(created_at=inside)

        metrics = count_emails_sent_rolling_24h(reference_time=timezone.now())

        self.assertEqual(metrics["sent"], 1)
        self.assertEqual(metrics["quota_failures"], 1)
        self.assertEqual(metrics["remaining"], 499)

    def test_build_email_quota_metrics_includes_both_windows(self):
        """build_email_quota_metrics returns calendar and rolling counters."""
        metrics = build_email_quota_metrics()
        self.assertIn("calendar", metrics)
        self.assertIn("rolling_24h", metrics)
        self.assertEqual(
            metrics["calendar"]["limit"], metrics["rolling_24h"]["limit"]
        )
