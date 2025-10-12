"""
Tests for work order functionality.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Veterinarian
from protocols.models import (
    PricingCatalog,
    Protocol,
    WorkOrder,
    WorkOrderCounter,
    WorkOrderService,
)

User = get_user_model()


class PricingCatalogModelTest(TestCase):
    """Tests for PricingCatalog model."""

    def setUp(self):
        """Set up test data."""
        self.today = date.today()
        self.pricing = PricingCatalog.objects.create(
            service_type="histopatologia_2a5_piezas",
            description="Histopatología 2-5 piezas",
            price=Decimal("14.04"),
            valid_from=self.today,
        )

    def test_pricing_catalog_creation(self):
        """Test pricing catalog creation."""
        self.assertEqual(
            self.pricing.service_type, "histopatologia_2a5_piezas"
        )
        self.assertEqual(self.pricing.price, Decimal("14.04"))
        self.assertTrue(self.pricing.is_valid())

    def test_get_current_price(self):
        """Test getting current price for a service."""
        price = PricingCatalog.get_current_price("histopatologia_2a5_piezas")
        self.assertIsNotNone(price)
        self.assertEqual(price.price, Decimal("14.04"))

    def test_get_current_price_not_found(self):
        """Test getting price for non-existent service."""
        price = PricingCatalog.get_current_price("non_existent_service")
        self.assertIsNone(price)

    def test_pricing_validity_dates(self):
        """Test pricing validity with date ranges."""
        # Create expired pricing
        expired = PricingCatalog.objects.create(
            service_type="old_service",
            description="Old Service",
            price=Decimal("10.00"),
            valid_from=self.today - timedelta(days=30),
            valid_until=self.today - timedelta(days=1),
        )
        self.assertFalse(expired.is_valid())
        self.assertFalse(expired.is_valid(self.today))

    def test_pricing_str_method(self):
        """Test string representation."""
        expected = f"{self.pricing.description} - ${self.pricing.price}"
        self.assertEqual(str(self.pricing), expected)


class WorkOrderCounterModelTest(TestCase):
    """Tests for WorkOrderCounter model."""

    def test_counter_creation(self):
        """Test counter creation."""
        counter = WorkOrderCounter.objects.create(
            year=2024,
            last_number=0,
        )
        self.assertEqual(counter.year, 2024)
        self.assertEqual(counter.last_number, 0)

    def test_get_next_number(self):
        """Test getting next work order number."""
        formatted_number, counter = WorkOrderCounter.get_next_number(year=2024)

        self.assertEqual(formatted_number, "OT-2024-001")
        self.assertEqual(counter.last_number, 1)

        # Get second number
        formatted_number2, counter2 = WorkOrderCounter.get_next_number(
            year=2024
        )
        self.assertEqual(formatted_number2, "OT-2024-002")
        self.assertEqual(counter2.last_number, 2)

    def test_counter_different_years(self):
        """Test counters for different years are independent."""
        num1, _ = WorkOrderCounter.get_next_number(year=2024)
        num2, _ = WorkOrderCounter.get_next_number(year=2025)

        self.assertEqual(num1, "OT-2024-001")
        self.assertEqual(num2, "OT-2025-001")

    def test_counter_str_method(self):
        """Test string representation."""
        counter = WorkOrderCounter.objects.create(year=2024, last_number=5)
        self.assertEqual(str(counter), "OT 2024: 5")


class WorkOrderModelTest(TestCase):
    """Tests for WorkOrder model."""

    def setUp(self):
        """Set up test data."""
        # Create user and veterinarian
        self.user = User.objects.create_user(
            email="vet@test.com",
            username="vettest",
            password="testpass123",
            first_name="Test",
            last_name="Vet",
            role="veterinarian",
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            license_number="MP-12345",
        )

        # Create work order
        self.work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("100.00"),
            advance_payment=Decimal("30.00"),
        )

    def test_work_order_creation(self):
        """Test work order creation with auto-generated fields."""
        self.assertIsNotNone(self.work_order.order_number)
        self.assertTrue(self.work_order.order_number.startswith("OT-"))
        self.assertEqual(self.work_order.balance_due, Decimal("70.00"))
        self.assertEqual(
            self.work_order.payment_status, WorkOrder.PaymentStatus.PARTIAL
        )
        self.assertEqual(self.work_order.status, WorkOrder.Status.DRAFT)

    def test_work_order_payment_status_pending(self):
        """Test payment status is pending when no advance."""
        wo = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("100.00"),
            advance_payment=Decimal("0.00"),
        )
        self.assertEqual(wo.payment_status, WorkOrder.PaymentStatus.PENDING)

    def test_work_order_payment_status_paid(self):
        """Test payment status is paid when fully paid."""
        wo = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("100.00"),
            advance_payment=Decimal("100.00"),
        )
        self.assertEqual(wo.payment_status, WorkOrder.PaymentStatus.PAID)
        self.assertEqual(wo.balance_due, Decimal("0.00"))

    def test_work_order_can_edit(self):
        """Test can_edit method."""
        self.assertTrue(self.work_order.can_edit())

        self.work_order.status = WorkOrder.Status.ISSUED
        self.work_order.save()
        self.assertFalse(self.work_order.can_edit())

    def test_work_order_can_delete(self):
        """Test can_delete method."""
        self.assertTrue(self.work_order.can_delete())

        self.work_order.status = WorkOrder.Status.ISSUED
        self.work_order.save()
        self.assertFalse(self.work_order.can_delete())

    def test_work_order_issue(self):
        """Test issuing a work order."""
        self.work_order.issue()
        self.assertEqual(self.work_order.status, WorkOrder.Status.ISSUED)

    def test_work_order_issue_invalid_status(self):
        """Test issuing non-draft work order raises error."""
        self.work_order.status = WorkOrder.Status.ISSUED
        self.work_order.save()

        with self.assertRaises(ValueError):
            self.work_order.issue()

    def test_work_order_mark_as_sent(self):
        """Test marking work order as sent."""
        self.work_order.mark_as_sent()
        self.assertEqual(self.work_order.status, WorkOrder.Status.SENT)
        self.assertIsNotNone(self.work_order.sent_date)

    def test_work_order_mark_as_invoiced(self):
        """Test marking work order as invoiced."""
        self.work_order.status = WorkOrder.Status.SENT
        self.work_order.save()

        self.work_order.mark_as_invoiced()
        self.assertEqual(self.work_order.status, WorkOrder.Status.INVOICED)
        self.assertIsNotNone(self.work_order.invoiced_date)

    def test_work_order_get_billing_name(self):
        """Test getting billing name."""
        # Default: use veterinarian name
        self.assertEqual(self.work_order.get_billing_name(), "Test Vet")

        # With custom billing name
        self.work_order.billing_name = "Custom Billing Name"
        self.assertEqual(
            self.work_order.get_billing_name(), "Custom Billing Name"
        )

    def test_work_order_calculate_total(self):
        """Test calculating total from services."""
        # Create protocol for services
        protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            species="Canino",
            animal_identification="Test-001",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )

        # Create services
        WorkOrderService.objects.create(
            work_order=self.work_order,
            protocol=protocol,
            description="Service 1",
            service_type="histopatologia",
            quantity=1,
            unit_price=Decimal("50.00"),
            discount=Decimal("0.00"),
        )
        WorkOrderService.objects.create(
            work_order=self.work_order,
            protocol=protocol,
            description="Service 2",
            service_type="citologia",
            quantity=2,
            unit_price=Decimal("25.00"),
            discount=Decimal("10.00"),
        )

        total = self.work_order.calculate_total()
        # (50*1 - 0) + (25*2 - 10) = 50 + 40 = 90
        self.assertEqual(total, Decimal("90.00"))

    def test_work_order_generate_pdf_filename(self):
        """Test PDF filename generation."""
        self.work_order.order_number = "OT-2024-123"
        filename = self.work_order.generate_pdf_filename()
        self.assertEqual(filename, "OT_2024_123.pdf")

    def test_work_order_str_method(self):
        """Test string representation."""
        self.work_order.order_number = "OT-2024-001"
        expected = f"OT-2024-001 - {self.veterinarian}"
        self.assertEqual(str(self.work_order), expected)


class WorkOrderServiceModelTest(TestCase):
    """Tests for WorkOrderService model."""

    def setUp(self):
        """Set up test data."""
        # Create user and veterinarian
        self.user = User.objects.create_user(
            email="vet@test.com",
            username="vettest",
            password="testpass123",
            first_name="Test",
            last_name="Vet",
            role="veterinarian",
        )
        self.veterinarian = Veterinarian.objects.create(
            user=self.user,
            license_number="MP-12345",
        )

        # Create work order
        self.work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("100.00"),
        )

        # Create protocol
        self.protocol = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            species="Canino",
            animal_identification="Test-001",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )

    def test_service_creation(self):
        """Test service creation with auto-calculated subtotal."""
        service = WorkOrderService.objects.create(
            work_order=self.work_order,
            protocol=self.protocol,
            description="Test Service",
            service_type="histopatologia",
            quantity=3,
            unit_price=Decimal("25.50"),
            discount=Decimal("0.00"),
        )

        self.assertEqual(service.subtotal, Decimal("76.50"))

    def test_service_subtotal_calculation(self):
        """Test subtotal is auto-calculated on save."""
        service = WorkOrderService.objects.create(
            work_order=self.work_order,
            protocol=self.protocol,
            description="Test Service",
            service_type="histopatologia",
            quantity=2,
            unit_price=Decimal("15.00"),
        )

        self.assertEqual(service.subtotal, Decimal("30.00"))

        # Update quantity
        service.quantity = 5
        service.save()
        self.assertEqual(service.subtotal, Decimal("75.00"))

    def test_service_str_method(self):
        """Test string representation."""
        service = WorkOrderService.objects.create(
            work_order=self.work_order,
            protocol=self.protocol,
            description="Test Service",
            service_type="histopatologia",
            quantity=1,
            unit_price=Decimal("10.00"),
        )

        expected = f"{self.work_order.order_number} - Test Service"
        self.assertEqual(str(service), expected)


class WorkOrderIntegrationTest(TestCase):
    """Integration tests for work order workflow."""

    def setUp(self):
        """Set up test data."""
        # Create staff user
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            username="stafftest",
            password="testpass123",
            first_name="Lab",
            last_name="Staff",
            role="laboratory_staff",
            is_staff=True,
        )

        # Create veterinarian
        vet_user = User.objects.create_user(
            email="vet@test.com",
            username="vettest2",
            password="testpass123",
            first_name="Test",
            last_name="Vet",
            role="veterinarian",
        )
        self.veterinarian = Veterinarian.objects.create(
            user=vet_user,
            license_number="MP-12345",
        )

        # Create pricing
        PricingCatalog.objects.create(
            service_type="histopatologia_2a5_piezas",
            description="Histopatología 2-5 piezas",
            price=Decimal("14.04"),
            valid_from=date.today(),
        )

        # Create protocols
        self.protocol1 = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            species="Canino",
            animal_identification="Dog-001",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        # Assign protocol number
        self.protocol1.protocol_number = "HP 24/001"
        self.protocol1.save()

        self.protocol2 = Protocol.objects.create(
            veterinarian=self.veterinarian,
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            species="Felino",
            animal_identification="Cat-001",
            presumptive_diagnosis="Test",
            submission_date=date.today(),
            status=Protocol.Status.READY,
        )
        # Assign protocol number
        self.protocol2.protocol_number = "HP 24/002"
        self.protocol2.save()

    def test_complete_workflow(self):
        """Test complete work order workflow."""
        # 1. Create work order
        work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("0.00"),  # Will be calculated
            created_by=self.staff_user,
        )

        # 2. Add services
        WorkOrderService.objects.create(
            work_order=work_order,
            protocol=self.protocol1,
            description="HP - Dog-001",
            service_type="histopatologia_2a5_piezas",
            quantity=1,
            unit_price=Decimal("14.04"),
        )

        WorkOrderService.objects.create(
            work_order=work_order,
            protocol=self.protocol2,
            description="HP - Cat-001",
            service_type="histopatologia_2a5_piezas",
            quantity=1,
            unit_price=Decimal("14.04"),
        )

        # 3. Calculate and update total
        total = work_order.calculate_total()
        work_order.total_amount = total
        work_order.save()

        self.assertEqual(work_order.total_amount, Decimal("28.08"))

        # 4. Issue work order
        work_order.issue()
        self.assertEqual(work_order.status, WorkOrder.Status.ISSUED)

        # 5. Send work order
        work_order.mark_as_sent()
        self.assertEqual(work_order.status, WorkOrder.Status.SENT)
        self.assertIsNotNone(work_order.sent_date)

        # 6. Mark as invoiced
        work_order.mark_as_invoiced()
        self.assertEqual(work_order.status, WorkOrder.Status.INVOICED)
        self.assertIsNotNone(work_order.invoiced_date)

    def test_protocol_grouping(self):
        """Test grouping multiple protocols in one work order."""
        # Create work order with multiple protocols
        work_order = WorkOrder.objects.create(
            veterinarian=self.veterinarian,
            total_amount=Decimal("28.08"),
        )

        # Add both protocols
        WorkOrderService.objects.create(
            work_order=work_order,
            protocol=self.protocol1,
            description="Service 1",
            service_type="histopatologia_2a5_piezas",
            quantity=1,
            unit_price=Decimal("14.04"),
        )

        WorkOrderService.objects.create(
            work_order=work_order,
            protocol=self.protocol2,
            description="Service 2",
            service_type="histopatologia_2a5_piezas",
            quantity=1,
            unit_price=Decimal("14.04"),
        )

        # Link protocols to work order
        self.protocol1.work_order = work_order
        self.protocol1.save()
        self.protocol2.work_order = work_order
        self.protocol2.save()

        # Verify grouping
        self.assertEqual(work_order.services.count(), 2)
        self.assertEqual(work_order.protocols.count(), 2)
        self.assertIn(self.protocol1, work_order.protocols.all())
        self.assertIn(self.protocol2, work_order.protocols.all())
