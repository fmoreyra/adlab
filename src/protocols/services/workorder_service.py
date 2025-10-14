"""
Work order service for handling work order creation and calculation logic.
"""

import logging
from decimal import Decimal
from typing import Dict, Tuple

from django.db import transaction

from protocols.models import (
    PricingCatalog,
    Protocol,
    WorkOrder,
    WorkOrderService,
)

logger = logging.getLogger(__name__)


class WorkOrderCalculationService:
    """
    Service class for calculating work order services and pricing.

    This service encapsulates the business logic for determining service
    types, calculating prices, and preparing service line items.
    """

    def calculate_services(self, protocols) -> Dict:
        """
        Calculate service line items for protocols.

        Args:
            protocols: QuerySet of Protocol objects

        Returns:
            dict: Service data with items, subtotal, and total
        """
        services = []
        subtotal = Decimal("0")

        for protocol in protocols:
            service_data = self._calculate_protocol_service(protocol)
            services.append(service_data)
            subtotal += service_data["subtotal"]

        return {
            "services": services,
            "subtotal": subtotal,
            "total": subtotal,
        }

    def _calculate_protocol_service(self, protocol: Protocol) -> Dict:
        """
        Calculate service data for a single protocol.

        Args:
            protocol: Protocol instance

        Returns:
            dict: Service data for the protocol
        """
        # Determine service type based on analysis type and sample details
        if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
            service_type = "histopatologia_2a5_piezas"
            description = (
                f"Análisis histopatológico - {protocol.animal_identification}"
            )
        else:  # Cytology
            service_type = "citologia"
            description = (
                f"Análisis citopatológico - {protocol.animal_identification}"
            )

        # Get current price from catalog
        unit_price = self._get_pricing_for_protocol(protocol, service_type)
        item_subtotal = unit_price * 1  # quantity = 1 per protocol

        return {
            "protocol": protocol,
            "description": description,
            "service_type": service_type,
            "quantity": 1,
            "unit_price": unit_price,
            "subtotal": item_subtotal,
            "discount": Decimal("0"),
        }

    def _get_pricing_for_protocol(
        self, protocol: Protocol, service_type: str
    ) -> Decimal:
        """
        Get pricing for a protocol's service type.

        Args:
            protocol: Protocol instance
            service_type: Service type identifier

        Returns:
            Decimal: Unit price for the service
        """
        # Get current price from catalog
        pricing = PricingCatalog.get_current_price(service_type)

        if pricing:
            return pricing.price
        else:
            # Default prices if not in catalog
            if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
                return Decimal("14.04")
            else:
                return Decimal("5.40")


class WorkOrderCreationService:
    """
    Service class for creating work orders and managing the creation process.

    This service encapsulates the business logic for validating protocols,
    creating work orders, and linking them to protocols.
    """

    def validate_protocols_for_work_order(self, protocols) -> Tuple[bool, str]:
        """
        Validate that protocols are suitable for work order creation.

        Args:
            protocols: QuerySet of protocols

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not protocols.exists():
            return False, "No se encontraron protocolos válidos."

        # Validate all from same veterinarian
        veterinarians = set(p.veterinarian for p in protocols)
        if len(veterinarians) > 1:
            return (
                False,
                "Todos los protocolos deben ser del mismo veterinario.",
            )

        # Validate all are ready for work order
        for protocol in protocols:
            if protocol.status != Protocol.Status.READY:
                return (
                    False,
                    f"Protocolo {protocol.protocol_number} no está listo para orden de trabajo.",
                )

            if protocol.work_order is not None:
                return (
                    False,
                    f"Protocolo {protocol.protocol_number} ya tiene una orden de trabajo.",
                )

        return True, ""

    @transaction.atomic
    def create_work_order_with_services(
        self, form, protocols, services_data: Dict, created_by
    ) -> WorkOrder:
        """
        Create work order and its service line items.

        Args:
            form: Validated WorkOrderCreateForm
            protocols: QuerySet of protocols
            services_data: Service calculation data
            created_by: User creating the work order

        Returns:
            WorkOrder: Created work order instance
        """
        # Create work order
        work_order = form.save(commit=False)
        work_order.total_amount = services_data["total"]
        work_order.created_by = created_by
        work_order.save()

        # Create service line items
        for service_data in services_data["services"]:
            WorkOrderService.objects.create(
                work_order=work_order,
                protocol=service_data["protocol"],
                description=service_data["description"],
                service_type=service_data["service_type"],
                quantity=service_data["quantity"],
                unit_price=service_data["unit_price"],
                discount=service_data["discount"],
            )

            # Link protocol to work order
            protocol = service_data["protocol"]
            protocol.work_order = work_order
            protocol.save(update_fields=["work_order"])

        return work_order

    def issue_work_order(self, work_order) -> Tuple[bool, str]:
        """
        Issue a work order (mark as issued).

        Args:
            work_order: WorkOrder instance

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if work_order.status != WorkOrder.Status.DRAFT:
            return (
                False,
                "Solo se pueden emitir órdenes de trabajo en borrador.",
            )

        try:
            work_order.issue()
            return True, ""
        except Exception as e:
            logger.error(f"Error issuing work order {work_order.pk}: {e}")
            return False, str(e)

    def send_work_order(self, work_order) -> Tuple[bool, str]:
        """
        Send a work order to the veterinarian.

        Args:
            work_order: WorkOrder instance

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if work_order.status not in [
            WorkOrder.Status.DRAFT,
            WorkOrder.Status.ISSUED,
        ]:
            return (
                False,
                "Solo las órdenes en borrador o emitidas pueden ser enviadas.",
            )

        try:
            work_order.mark_as_sent()
            return True, ""
        except Exception as e:
            logger.error(f"Error sending work order {work_order.pk}: {e}")
            return False, str(e)
