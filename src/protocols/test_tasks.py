"""
Tests for Celery tasks in protocols.tasks module.
"""

from datetime import date

from django.test import TestCase

from accounts.models import User, Veterinarian
from protocols import tasks
from protocols.models import CytologySample, Protocol


class CeleryTaskTest(TestCase):
    """Test Celery background tasks."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.veterinarian_user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            is_active=True,
        )

        # Create veterinarian profile
        self.veterinarian = Veterinarian.objects.create(
            user=self.veterinarian_user,
            first_name="Dr. Juan",
            last_name="Pérez",
            license_number="VET123",
            phone="123456789",
            email="vet@example.com",
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            status=Protocol.Status.SUBMITTED,
            temporary_code="C 25/003",
            protocol_number="C 25/003",
            submission_date=date.today(),
        )

        # Create cytology sample
        self.cytology_sample = CytologySample.objects.create(
            protocol=self.protocol,
            veterinarian=self.veterinarian,
            technique_used="PAAF",
            sampling_site="Test site",
            number_of_slides=2,
        )

    def test_send_email_task_retry_configuration(self):
        """Test that send_email task has correct retry configuration."""
        # Get the task function
        task_func = tasks.send_email

        # Check task attributes
        self.assertTrue(hasattr(task_func, "max_retries"))
        self.assertTrue(hasattr(task_func, "default_retry_delay"))
        self.assertTrue(hasattr(task_func, "autoretry_for"))
        self.assertTrue(hasattr(task_func, "retry_backoff"))
        self.assertTrue(hasattr(task_func, "retry_backoff_max"))
        self.assertTrue(hasattr(task_func, "retry_jitter"))

        # Check retry configuration values
        self.assertEqual(task_func.max_retries, 3)
        self.assertEqual(task_func.default_retry_delay, 60)  # 1 minute
        self.assertEqual(task_func.retry_backoff_max, 600)  # 10 minutes
        self.assertTrue(task_func.retry_backoff)
        self.assertTrue(task_func.retry_jitter)

    def test_send_email_task_is_shared_task(self):
        """Test that send_email is properly configured as a shared task."""
        # Check that the task is a Celery task
        self.assertTrue(hasattr(tasks.send_email, "delay"))
        self.assertTrue(hasattr(tasks.send_email, "apply_async"))
        self.assertTrue(hasattr(tasks.send_email, "run"))

        # Check that it's bound (has self parameter)
        # Note: The 'self' parameter is added by Celery at runtime, so it's not visible in the signature
        # but we can check that the task is bound
        self.assertTrue(tasks.send_email.bind)

    def test_send_email_task_signature(self):
        """Test that send_email task has correct function signature."""
        import inspect

        sig = inspect.signature(tasks.send_email)
        params = list(sig.parameters.keys())

        # Expected parameters: email_type, recipient_email, subject, context, template_name, attachment_path, email_log_id
        # Note: 'self' parameter is added by Celery at runtime, so it's not visible in the signature
        expected_params = [
            "email_type",
            "recipient_email",
            "subject",
            "context",
            "template_name",
            "attachment_path",
            "email_log_id",
        ]
        self.assertEqual(params, expected_params)

    def test_send_email_task_docstring(self):
        """Test that send_email task has proper documentation."""
        docstring = tasks.send_email.__doc__
        self.assertIsNotNone(docstring)
        self.assertIn("email_type", docstring)
        self.assertIn("recipient_email", docstring)
        self.assertIn("subject", docstring)
        self.assertIn("context", docstring)
        self.assertIn("Returns", docstring)

    def test_send_email_task_import(self):
        """Test that send_email task can be imported and is callable."""
        # Test that the task can be imported
        from protocols.tasks import send_email

        self.assertIsNotNone(send_email)
        self.assertTrue(callable(send_email))

        # Test that it's the same function
        self.assertEqual(send_email, tasks.send_email)

    def test_send_email_task_attributes(self):
        """Test that send_email task has required Celery attributes."""
        task = tasks.send_email

        # Check Celery task attributes
        self.assertTrue(hasattr(task, "name"))
        self.assertTrue(hasattr(task, "run"))
        self.assertTrue(hasattr(task, "delay"))
        self.assertTrue(hasattr(task, "apply_async"))

        # Check that it's bound
        self.assertTrue(task.bind)

    def test_send_email_task_autoretry_configuration(self):
        """Test that send_email task has correct autoretry configuration."""
        task = tasks.send_email

        # Check autoretry configuration
        self.assertEqual(task.autoretry_for, (Exception,))
        self.assertTrue(task.retry_backoff)
        self.assertTrue(task.retry_jitter)
        self.assertEqual(task.retry_backoff_max, 600)

    def test_send_email_task_max_retries(self):
        """Test that send_email task has correct max retries."""
        task = tasks.send_email
        self.assertEqual(task.max_retries, 3)

    def test_send_email_task_retry_delay(self):
        """Test that send_email task has correct retry delay."""
        task = tasks.send_email
        self.assertEqual(task.default_retry_delay, 60)

    def test_send_email_task_bind_configuration(self):
        """Test that send_email task is bound."""
        task = tasks.send_email
        self.assertTrue(task.bind)

    def test_send_email_task_name(self):
        """Test that send_email task has correct name."""
        task = tasks.send_email
        self.assertEqual(task.name, "protocols.tasks.send_email")
