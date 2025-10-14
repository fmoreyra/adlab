"""
Protocol processing service for handling protocol reception and processing logic.
"""

import logging
from typing import Dict, List, Tuple

from django.utils.translation import gettext_lazy as _

from protocols.models import (
    Cassette,
    CassetteSlide,
    ProcessingLog,
    Protocol,
    ProtocolStatusHistory,
    ReceptionLog,
    Slide,
)

logger = logging.getLogger(__name__)


class ProtocolReceptionService:
    """
    Service class for handling protocol reception logic.

    This service encapsulates the complex business logic for receiving
    protocols, validating them, and updating their status and related data.
    """

    def validate_protocol_for_reception(
        self, protocol: Protocol
    ) -> Tuple[bool, str]:
        """
        Validate if a protocol can be received.

        Args:
            protocol: Protocol instance to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if protocol.status not in [
            Protocol.Status.SUBMITTED,
            Protocol.Status.DRAFT,
        ]:
            return False, _("Este protocolo ya fue procesado.")

        return True, ""

    def process_reception(
        self, protocol: Protocol, form_data: Dict, user
    ) -> Tuple[bool, str]:
        """
        Process protocol reception with all necessary updates.

        Args:
            protocol: Protocol instance to receive
            form_data: Form data containing reception information
            user: User performing the reception

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            # Extract form data
            sample_condition = form_data.get("sample_condition")
            reception_notes = form_data.get("reception_notes", "")
            discrepancies = form_data.get("discrepancies", "")

            # Update protocol
            protocol.receive(
                received_by=user,
                sample_condition=sample_condition,
                reception_notes=reception_notes,
                discrepancies=discrepancies,
            )

            # Update sample-specific fields
            self._update_sample_specific_fields(protocol, form_data)

            # Log reception action
            ReceptionLog.log_action(
                protocol=protocol,
                action=ReceptionLog.Action.RECEIVED,
                user=user,
                notes=reception_notes,
            )

            # Log status change
            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=Protocol.Status.RECEIVED,
                changed_by=user,
                description=_("Muestra recibida en laboratorio"),
            )

            return True, ""

        except Exception as e:
            logger.error(
                f"Error processing reception for protocol {protocol.pk}: {e}"
            )
            return False, str(e)

    def _update_sample_specific_fields(
        self, protocol: Protocol, form_data: Dict
    ) -> None:
        """
        Update sample-specific fields based on analysis type.

        Args:
            protocol: Protocol instance
            form_data: Form data containing sample information
        """
        # Update cytology sample fields
        if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY:
            slides_received = form_data.get("number_slides_received")
            if slides_received is not None and hasattr(
                protocol, "cytology_sample"
            ):
                protocol.cytology_sample.number_slides_received = (
                    slides_received
                )
                protocol.cytology_sample.save(
                    update_fields=["number_slides_received"]
                )

        # Update histopathology sample fields
        if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
            jars_received = form_data.get("number_jars_received")
            if jars_received is not None and hasattr(
                protocol, "histopathology_sample"
            ):
                protocol.histopathology_sample.number_jars_received = (
                    jars_received
                )
                protocol.histopathology_sample.save(
                    update_fields=["number_jars_received"]
                )


class ProtocolProcessingService:
    """
    Service class for handling protocol processing logic.

    This service encapsulates the complex business logic for creating
    cassettes, registering slides, and managing the processing workflow.
    """

    def create_cassettes(
        self, protocol: Protocol, cassette_data: List[Dict], user
    ) -> Tuple[bool, List[Cassette], str]:
        """
        Create cassettes for a histopathology protocol.

        Args:
            protocol: Protocol instance
            cassette_data: List of cassette data dictionaries
            user: User creating the cassettes

        Returns:
            Tuple[bool, List[Cassette], str]: (success, created_cassettes, error_message)
        """
        try:
            # Validate protocol
            if protocol.analysis_type != Protocol.AnalysisType.HISTOPATHOLOGY:
                return (
                    False,
                    [],
                    _(
                        "Solo los protocolos de histopatología requieren cassettes."
                    ),
                )

            if not hasattr(protocol, "histopathology_sample"):
                return (
                    False,
                    [],
                    _("Este protocolo no tiene muestra de histopatología."),
                )

            created_cassettes = []

            for data in cassette_data:
                cassette = Cassette.objects.create(
                    histopathology_sample=protocol.histopathology_sample,
                    material_incluido=data.get("material", ""),
                    tipo_cassette=data.get(
                        "tipo", Cassette.CassetteType.NORMAL
                    ),
                    color_cassette=data.get(
                        "color", Cassette.CassetteColor.BLANCO
                    ),
                    observaciones=data.get("observaciones", ""),
                )

                # Update to encasetado stage
                cassette.update_stage("encasetado")

                # Log action
                ProcessingLog.log_action(
                    protocol=protocol,
                    etapa=ProcessingLog.Stage.ENCASETADO,
                    usuario=user,
                    cassette=cassette,
                    observaciones=f"Cassette creado: {data.get('material', '')[:50]}",
                )

                created_cassettes.append(cassette)

            # Update protocol status to processing
            if protocol.status == Protocol.Status.RECEIVED:
                protocol.status = Protocol.Status.PROCESSING
                protocol.save(update_fields=["status"])

                ProtocolStatusHistory.log_status_change(
                    protocol=protocol,
                    new_status=Protocol.Status.PROCESSING,
                    changed_by=user,
                    description=f"Iniciado procesamiento - {len(created_cassettes)} cassettes creados",
                )

            return True, created_cassettes, ""

        except Exception as e:
            logger.error(
                f"Error creating cassettes for protocol {protocol.pk}: {e}"
            )
            return False, [], str(e)

    def register_slides(
        self, protocol: Protocol, slide_data: List[Dict], user
    ) -> Tuple[bool, List[Slide], str]:
        """
        Register slides for a protocol.

        Args:
            protocol: Protocol instance
            slide_data: List of slide data dictionaries
            user: User registering the slides

        Returns:
            Tuple[bool, List[Slide], str]: (success, created_slides, error_message)
        """
        try:
            created_slides = []

            for data in slide_data:
                # Create slide
                slide = Slide.objects.create(
                    protocol=protocol,
                    codigo_portaobjetos=data.get("codigo_portaobjetos", ""),
                    campo=data.get("campo"),
                    tecnica_coloracion=data.get("tecnica_coloracion", ""),
                    observaciones=data.get("observaciones", ""),
                    estado=Slide.Status.PENDIENTE,
                )

                # Handle cassette relationships for histopathology
                if (
                    protocol.analysis_type
                    == Protocol.AnalysisType.HISTOPATHOLOGY
                ):
                    self._create_cassette_slide_relationships(
                        slide, data, protocol
                    )

                # Log action
                ProcessingLog.log_action(
                    protocol=protocol,
                    etapa=ProcessingLog.Stage.MONTAJE,
                    usuario=user,
                    slide=slide,
                    observaciones=f"Slide registrado: {data.get('codigo_portaobjetos', '')}",
                )

                created_slides.append(slide)

            return True, created_slides, ""

        except Exception as e:
            logger.error(
                f"Error registering slides for protocol {protocol.pk}: {e}"
            )
            return False, [], str(e)

    def _create_cassette_slide_relationships(
        self, slide: Slide, slide_data: Dict, protocol: Protocol
    ) -> None:
        """
        Create cassette-slide relationships for histopathology protocols.

        Args:
            slide: Slide instance
            slide_data: Slide data containing cassette relationships
            protocol: Protocol instance
        """
        for pos in [1, 2]:  # Each slide can have up to 2 cassette positions
            cassette_id = slide_data.get(f"cassette_{pos}")
            if cassette_id:
                try:
                    cassette = Cassette.objects.get(
                        id=cassette_id,
                        histopathology_sample=protocol.histopathology_sample,
                    )
                    CassetteSlide.objects.create(
                        cassette=cassette,
                        slide=slide,
                        position=pos,
                    )
                except Cassette.DoesNotExist:
                    logger.warning(
                        f"Cassette {cassette_id} not found for slide {slide.id}"
                    )

    def update_slide_stage(
        self, slide: Slide, stage: str, user, observaciones: str = ""
    ) -> Tuple[bool, str]:
        """
        Update slide processing stage.

        Args:
            slide: Slide instance
            stage: New stage name
            user: User updating the stage
            observaciones: Additional observations

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            if stage in ["montaje", "coloracion"]:
                slide.update_stage(stage)

                # Log action
                etapa_mapping = {
                    "montaje": ProcessingLog.Stage.MONTAJE,
                    "coloracion": ProcessingLog.Stage.COLORACION,
                }

                ProcessingLog.log_action(
                    protocol=slide.protocol,
                    etapa=etapa_mapping[stage],
                    usuario=user,
                    slide=slide,
                    observaciones=observaciones,
                )

                return True, ""

            elif stage == "listo":
                slide.mark_ready()
                return True, ""

            else:
                return False, _("Etapa no válida.")

        except Exception as e:
            logger.error(f"Error updating slide {slide.id} stage: {e}")
            return False, str(e)

    def update_slide_quality(
        self, slide: Slide, quality: str, observaciones: str = ""
    ) -> Tuple[bool, str]:
        """
        Update slide quality assessment.

        Args:
            slide: Slide instance
            quality: Quality assessment value
            observaciones: Additional observations

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            valid_qualities = [choice[0] for choice in Slide.Quality.choices]
            if quality not in valid_qualities:
                return False, _("Calidad no válida.")

            slide.calidad = quality
            if observaciones:
                slide.observaciones = observaciones
            slide.save(update_fields=["calidad", "observaciones"])

            return True, ""

        except Exception as e:
            logger.error(f"Error updating slide {slide.id} quality: {e}")
            return False, str(e)
