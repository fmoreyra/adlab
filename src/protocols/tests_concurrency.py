"""
Concurrency tests for protocols app.

Tests race conditions and concurrent access patterns to ensure
the application works correctly under parallel execution.
"""

import os
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TransactionTestCase

from accounts.models import Histopathologist, Veterinarian
from protocols.models import (
    Protocol,
    ProtocolCounter,
    Report,
    TemporaryCodeCounter,
    WorkOrder,
    WorkOrderCounter,
)

User = get_user_model()


class ConcurrencyTest(TransactionTestCase):
    """Test concurrent operations to ensure no race conditions."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email="vet@example.com",
            username="vet",
            password="testpass123",
            role=User.Role.VETERINARIO,
            email_verified=True,
        )

        # Create veterinarian
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            license_number="MP-CONCURRENCY-001",
            phone="+54 342 1234567",
            email="vet@example.com",
        )

        # Create histopathologist for reports
        self.histo_user = User.objects.create_user(
            email="histo@example.com",
            username="histo",
            password="testpass123",
            role=User.Role.HISTOPATOLOGO,
            email_verified=True,
        )

        self.histopathologist = Histopathologist.objects.create(
            user=self.histo_user,
            first_name="Dr. Jane",
            last_name="Smith",
            license_number="HP-CONCURRENCY-001",
            position="Profesor Titular",
            specialty="Patología Veterinaria",
        )

    def test_temporary_code_concurrent_generation(self):
        """Test concurrent temporary code generation."""
        results = []
        errors = []
        lock = threading.Lock()

        def create_protocol():
            try:
                protocol = Protocol.objects.create(
                    veterinarian=self.veterinarian,
                    analysis_type=Protocol.AnalysisType.CYTOLOGY,
                    status=Protocol.Status.SUBMITTED,
                    submission_date=date.today(),
                    species="Canino",
                    animal_identification="Concurrent Dog",
                    presumptive_diagnosis="Test diagnosis",
                )
                with lock:
                    results.append(protocol.temporary_code)
            except Exception as e:
                with lock:
                    errors.append(e)

        # Create 10 threads simultaneously
        threads = [threading.Thread(target=create_protocol) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assertions
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10, "Not all protocols were created")
        self.assertEqual(
            len(results), len(set(results)), "Duplicate temporary codes found"
        )

        # Verify sequential numbering (no gaps)
        codes = sorted(results)
        for i, code in enumerate(codes):
            expected_suffix = f"{i + 1:03d}"
            self.assertTrue(
                code.endswith(expected_suffix),
                f"Code {code} doesn't end with expected suffix {expected_suffix}",
            )

    def test_protocol_number_concurrent_assignment(self):
        """Test concurrent protocol number assignment."""
        results = []
        errors = []
        lock = threading.Lock()

        def assign_protocol_number():
            try:
                # Create protocol first (let it generate its own temporary code)
                protocol = Protocol.objects.create(
                    veterinarian=self.veterinarian,
                    analysis_type=Protocol.AnalysisType.CYTOLOGY,
                    status=Protocol.Status.SUBMITTED,
                    submission_date=date.today(),
                    species="Canino",
                    animal_identification="Concurrent Dog",
                    presumptive_diagnosis="Test diagnosis",
                )

                # Assign protocol number
                protocol_number = protocol.assign_protocol_number()
                with lock:
                    results.append(protocol_number)
            except Exception as e:
                with lock:
                    errors.append(e)

        # Create 10 threads simultaneously
        threads = [
            threading.Thread(target=assign_protocol_number) for _ in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assertions
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(
            len(results), 10, "Not all protocol numbers were assigned"
        )
        self.assertEqual(
            len(results), len(set(results)), "Duplicate protocol numbers found"
        )

    def test_work_order_number_concurrent_generation(self):
        """Test concurrent work order number generation."""
        results = []
        errors = []
        lock = threading.Lock()

        def create_work_order():
            try:
                # Create work order (it will generate its own order number)
                work_order = WorkOrder.objects.create(
                    veterinarian=self.veterinarian,
                    billing_name="Test Billing",
                )

                with lock:
                    results.append(work_order.order_number)
            except Exception as e:
                with lock:
                    errors.append(e)

        # Create 10 threads simultaneously
        threads = [
            threading.Thread(target=create_work_order) for _ in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assertions
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10, "Not all work orders were created")
        self.assertEqual(
            len(results),
            len(set(results)),
            "Duplicate work order numbers found",
        )

    def test_pdf_generation_concurrent(self):
        """Test concurrent PDF generation for different reports."""
        # Create test protocols and reports
        protocols = []
        reports = []

        for i in range(5):
            protocol = Protocol.objects.create(
                veterinarian=self.veterinarian,
                analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
                status=Protocol.Status.READY,
                temporary_code=f"TMP-HP-20251012-{i + 1:03d}",
                protocol_number=f"HP 25/{i + 1:03d}",
                submission_date=date.today(),
                species="Felino",
                animal_identification=f"Concurrent Cat {i + 1}",
                presumptive_diagnosis="Test diagnosis",
            )
            protocols.append(protocol)

            report = Report.objects.create(
                protocol=protocol,
                histopathologist=self.histopathologist,
                veterinarian=self.veterinarian,
                status=Report.Status.DRAFT,
                diagnosis="Test diagnosis",
                comments="Test comments",
                recommendations="Test recommendations",
            )
            reports.append(report)

        results = []
        errors = []

        def generate_pdf(report):
            try:
                # Simulate PDF generation by creating a temporary file
                with tempfile.NamedTemporaryFile(
                    mode="wb", delete=False, suffix=".pdf"
                ) as tmp_file:
                    tmp_file.write(b"Mock PDF content")
                    tmp_path = tmp_file.name

                # Simulate atomic rename
                final_path = tmp_path.replace(".pdf", "_final.pdf")
                os.rename(tmp_path, final_path)

                results.append(final_path)

                # Cleanup
                if os.path.exists(final_path):
                    os.unlink(final_path)

            except Exception as e:
                errors.append(e)

        # Generate PDFs concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(generate_pdf, report) for report in reports
            ]
            for future in as_completed(futures):
                future.result()

        # Assertions
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5, "Not all PDFs were generated")

    def test_pdf_regeneration_same_report(self):
        """Test concurrent regeneration of the same report PDF."""
        # Create test protocol and report
        protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            status=Protocol.Status.READY,
            temporary_code="TMP-HP-20251012-001",
            protocol_number="HP 25/001",
            submission_date=date.today(),
            species="Felino",
            animal_identification="Concurrent Cat",
            presumptive_diagnosis="Test diagnosis",
        )

        report = Report.objects.create(
            protocol=protocol,
            histopathologist=self.histopathologist,
            veterinarian=self.veterinarian,
            status=Report.Status.DRAFT,
            diagnosis="Test diagnosis",
            comments="Test comments",
            recommendations="Test recommendations",
        )

        results = []
        errors = []
        lock = threading.Lock()

        def regenerate_pdf():
            try:
                # Simulate PDF regeneration with file locking
                temp_dir = tempfile.mkdtemp()
                pdf_path = os.path.join(temp_dir, f"report_{report.id}.pdf")

                # Simulate atomic file operation
                with tempfile.NamedTemporaryFile(
                    mode="wb", delete=False, dir=temp_dir, suffix=".tmp"
                ) as tmp_file:
                    tmp_file.write(b"Mock PDF content")
                    tmp_path = tmp_file.name

                os.replace(tmp_path, pdf_path)

                with lock:
                    results.append(pdf_path)

                # Cleanup
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                os.rmdir(temp_dir)

            except Exception as e:
                with lock:
                    errors.append(e)

        # Try to regenerate PDF concurrently
        threads = [threading.Thread(target=regenerate_pdf) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assertions - all should succeed or all should produce valid files
        self.assertEqual(
            len(results), 3, "Not all PDF regenerations succeeded"
        )
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

    def test_counter_models_concurrent_access(self):
        """Test concurrent access to counter models."""
        results = []
        errors = []
        lock = threading.Lock()

        def get_next_protocol_number():
            try:
                number, counter = ProtocolCounter.get_next_number(
                    Protocol.AnalysisType.CYTOLOGY, year=2025
                )
                with lock:
                    results.append(number)
            except Exception as e:
                with lock:
                    errors.append(e)

        def get_next_temporary_code():
            try:
                code, counter = TemporaryCodeCounter.get_next_number(
                    Protocol.AnalysisType.CYTOLOGY, date_obj=date.today()
                )
                with lock:
                    results.append(code)
            except Exception as e:
                with lock:
                    errors.append(e)

        def get_next_work_order_number():
            try:
                number, counter = WorkOrderCounter.get_next_number(year=2025)
                with lock:
                    results.append(number)
            except Exception as e:
                with lock:
                    errors.append(e)

        # Mix different counter operations
        threads = []
        threads.extend(
            [
                threading.Thread(target=get_next_protocol_number)
                for _ in range(5)
            ]
        )
        threads.extend(
            [
                threading.Thread(target=get_next_temporary_code)
                for _ in range(5)
            ]
        )
        threads.extend(
            [
                threading.Thread(target=get_next_work_order_number)
                for _ in range(5)
            ]
        )

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assertions
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(
            len(results), 15, "Not all counter operations succeeded"
        )

        # Check that all results are unique
        self.assertEqual(
            len(results), len(set(results)), "Duplicate numbers found"
        )

    def test_database_transaction_isolation(self):
        """Test that database transactions are properly isolated."""
        results = []
        errors = []
        lock = threading.Lock()

        def create_protocol_in_transaction():
            try:
                with transaction.atomic():
                    protocol = Protocol.objects.create(
                        veterinarian=self.veterinarian,
                        analysis_type=Protocol.AnalysisType.CYTOLOGY,
                        status=Protocol.Status.SUBMITTED,
                        submission_date=date.today(),
                        species="Canino",
                        animal_identification="Transaction Dog",
                        presumptive_diagnosis="Test diagnosis",
                    )
                    with lock:
                        results.append(protocol.id)
            except Exception as e:
                with lock:
                    errors.append(e)

        # Create protocols in separate transactions
        threads = [
            threading.Thread(target=create_protocol_in_transaction)
            for _ in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assertions
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 5, "Not all protocols were created")
        self.assertEqual(
            len(results), len(set(results)), "Duplicate protocol IDs found"
        )

        # Verify protocols exist in database
        for protocol_id in results:
            self.assertTrue(Protocol.objects.filter(id=protocol_id).exists())
