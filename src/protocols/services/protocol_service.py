"""
Protocol processing service for handling protocol reception and processing logic.
"""

import logging
from typing import Dict, List, Tuple

from django.utils import timezone
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
        if protocol.status != Protocol.Status.SUBMITTED:
            if protocol.status == Protocol.Status.DRAFT:
                return False, _(
                    "No se puede recepcionar un protocolo en borrador. El protocolo debe ser enviado primero."
                )
            else:
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

            # Check if sample is rejected
            is_rejected = sample_condition == Protocol.SampleCondition.REJECTED

            slides_error = self._validate_cytology_slides_on_reception(
                protocol, form_data, is_rejected
            )
            if slides_error:
                return False, slides_error

            if is_rejected:
                # Handle rejected samples differently - don't assign protocol number
                protocol.reception_date = timezone.now()
                protocol.received_by = user
                protocol.sample_condition = sample_condition
                protocol.reception_notes = reception_notes
                protocol.discrepancies = discrepancies
                protocol.status = Protocol.Status.REJECTED
                protocol.save(
                    update_fields=[
                        "reception_date",
                        "received_by",
                        "sample_condition",
                        "reception_notes",
                        "discrepancies",
                        "status",
                    ]
                )
            else:
                # Normal reception - assign protocol number
                protocol.receive(
                    received_by=user,
                    sample_condition=sample_condition,
                    reception_notes=reception_notes,
                    discrepancies=discrepancies,
                )

            # Update sample-specific fields
            self._update_sample_specific_fields(protocol, form_data)

            # Log reception action - check for rejection first, then discrepancies
            if is_rejected:
                action = ReceptionLog.Action.REJECTED
            elif discrepancies:
                action = ReceptionLog.Action.DISCREPANCY_REPORTED
            else:
                action = ReceptionLog.Action.RECEIVED

            ReceptionLog.log_action(
                protocol=protocol,
                action=action,
                user=user,
                notes=reception_notes,
            )

            # Log status change
            new_status = (
                Protocol.Status.REJECTED
                if is_rejected
                else Protocol.Status.RECEIVED
            )
            description = (
                _("Muestra rechazada")
                if is_rejected
                else _("Muestra recibida en laboratorio")
            )

            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=new_status,
                changed_by=user,
                description=description,
            )

            if not is_rejected:
                self._create_cytology_slides_on_reception(
                    protocol, form_data, user
                )

            return True, ""

        except Exception as e:
            logger.error(
                f"Error processing reception for protocol {protocol.pk}: {e}"
            )
            return False, str(e)

    def _validate_cytology_slides_on_reception(
        self, protocol: Protocol, form_data: Dict, is_rejected: bool
    ) -> str:
        """
        Require at least one slide when receiving a cytology protocol.

        Rejected samples may be logged without slides.
        """
        if is_rejected:
            return ""
        if protocol.analysis_type != Protocol.AnalysisType.CYTOLOGY:
            return ""

        slides_received = form_data.get("number_slides_received")
        if slides_received is None and hasattr(protocol, "cytology_sample"):
            slides_received = protocol.cytology_sample.number_slides_received

        if not slides_received or int(slides_received) < 1:
            return str(
                _(
                    "Debe indicar al menos un portaobjeto recibido para "
                    "recepcionar una muestra de citología."
                )
            )
        return ""

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

    def _create_cytology_slides_on_reception(
        self, protocol: Protocol, form_data: Dict, user
    ) -> None:
        """
        Create cytology slides automatically when sample is received.

        Uses number_slides_received from reception form data.
        """
        if protocol.analysis_type != Protocol.AnalysisType.CYTOLOGY:
            return

        if not hasattr(protocol, "cytology_sample"):
            return

        slides_count = form_data.get("number_slides_received")
        if slides_count is None:
            slides_count = protocol.cytology_sample.number_slides_received

        if not slides_count or int(slides_count) < 1:
            return

        slides_count = int(slides_count)
        existing_count = protocol.slides.count()
        if existing_count >= slides_count:
            return

        slides_to_create = slides_count - existing_count
        default_staining = "Diff-Quick"

        for _slide_index in range(slides_to_create):
            slide = Slide.objects.create(
                protocol=protocol,
                cytology_sample=protocol.cytology_sample,
                tecnica_coloracion=default_staining,
                observaciones=_("Registrado automáticamente en recepción"),
                estado=Slide.Status.PENDIENTE,
            )
            ProcessingLog.log_action(
                protocol=protocol,
                etapa=ProcessingLog.Stage.MONTAJE,
                usuario=user,
                slide=slide,
                observaciones=(
                    _("Portaobjetos registrado en recepción: %(code)s")
                    % {"code": slide.codigo_portaobjetos}
                ),
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
            slide_data: Slide data containing cassette_ids or legacy keys
            protocol: Protocol instance
        """
        cassette_ids = slide_data.get("cassette_ids")
        if cassette_ids is None:
            cassette_ids = [
                slide_data[key]
                for key in ("cassette_1", "cassette_2")
                if slide_data.get(key)
            ]

        coloracion = slide_data.get("tecnica_coloracion", "")

        for cassette_id in cassette_ids:
            cassette = Cassette.objects.filter(
                id=cassette_id,
                histopathology_sample=protocol.histopathology_sample,
            ).first()
            if cassette is None:
                logger.warning(
                    "Cassette %s not found for slide %s",
                    cassette_id,
                    slide.id,
                )
                continue
            CassetteSlide.objects.create(
                cassette=cassette,
                slide=slide,
                posicion=CassetteSlide.Position.COMPLETO,
                coloracion=coloracion,
            )

    def register_histopathology_slides(
        self,
        protocol: Protocol,
        slide_data: List[Dict],
        user,
    ) -> Tuple[bool, List[Slide], str]:
        """
        Register histopathology slides with flexible cassette associations.

        Args:
            protocol: Protocol instance
            slide_data: List of slide data dicts with cassette_ids
            user: User registering the slides

        Returns:
            Tuple[bool, List[Slide], str]: (success, created_slides, error_message)
        """
        if not slide_data:
            return False, [], _("Debe registrar al menos un portaobjetos.")
        if len(slide_data) > 50:
            return (
                False,
                [],
                _("No se pueden registrar más de 50 portaobjetos a la vez."),
            )

        if not hasattr(protocol, "histopathology_sample"):
            return (
                False,
                [],
                _("El protocolo no tiene muestra de histopatología."),
            )

        if not protocol.histopathology_sample.cassettes.exists():
            return (
                False,
                [],
                _(
                    "Debe crear al menos un cassette antes de registrar slides."
                ),
            )

        normalized = []
        for row in slide_data:
            cassette_ids = row.get("cassette_ids") or []
            if not cassette_ids:
                return (
                    False,
                    [],
                    _("Cada portaobjetos debe tener al menos un cassette."),
                )
            normalized.append(
                {
                    "cassette_ids": cassette_ids,
                    "tecnica_coloracion": row.get(
                        "tecnica_coloracion", "Hematoxilina-Eosina"
                    ),
                    "observaciones": row.get("observaciones", ""),
                }
            )

        return self.register_slides(protocol, normalized, user)

    @staticmethod
    def _validate_revert_observaciones(action: str, observaciones: str) -> str:
        """
        Validate observations are present when reverting a stage.

        Returns:
            str: Error message if invalid, empty string if valid
        """
        if action != "revert":
            return ""
        if not observaciones or not observaciones.strip():
            return _("Debe indicar el motivo al revertir una etapa.")
        return ""

    @staticmethod
    def _format_log_observaciones(action: str, observaciones: str) -> str:
        """Format observations for processing log entries."""
        if action == "revert":
            return _("Corrección: %(motivo)s") % {
                "motivo": observaciones.strip()
            }
        return observaciones.strip()

    CASSETTE_STAGE_LOG = {
        "encasetado": ProcessingLog.Stage.ENCASETADO,
        "fijacion": ProcessingLog.Stage.FIJACION,
        "inclusion": ProcessingLog.Stage.INCLUSION,
        "entacado": ProcessingLog.Stage.ENTACADO,
    }

    SLIDE_STAGE_LOG = {
        "montaje": ProcessingLog.Stage.MONTAJE,
        "coloracion": ProcessingLog.Stage.COLORACION,
        "listo": ProcessingLog.Stage.COLORACION,
    }

    def update_cassette_stage(
        self, cassette: Cassette, action: str, user, observaciones: str = ""
    ) -> Tuple[bool, str]:
        """
        Advance or revert a cassette processing stage.

        Args:
            cassette: Cassette instance
            action: ``advance`` or ``revert``
            user: User performing the action
            observaciones: Required when action is ``revert``

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if action not in ("advance", "revert"):
            return False, _("Acción no válida.")

        validation_error = self._validate_revert_observaciones(
            action, observaciones
        )
        if validation_error:
            return False, validation_error

        try:
            if action == "advance":
                stage = cassette.advance_stage()
            else:
                stage = cassette.revert_last_stage()

            log_observaciones = self._format_log_observaciones(
                action, observaciones
            )
            if action == "advance" and stage == "entacado":
                collapsed_note = _(
                    "Procesado (fijación, inclusión y entacado)."
                )
                log_observaciones = (
                    f"{collapsed_note} {log_observaciones}".strip()
                    if log_observaciones
                    else collapsed_note
                )
            ProcessingLog.log_action(
                protocol=cassette.histopathology_sample.protocol,
                etapa=self.CASSETTE_STAGE_LOG[stage],
                usuario=user,
                cassette=cassette,
                observaciones=log_observaciones,
            )
            return True, ""

        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Error updating cassette {cassette.id} stage: {e}")
            return False, str(e)

    def update_slide_stage(
        self, slide: Slide, action: str, user, observaciones: str = ""
    ) -> Tuple[bool, str]:
        """
        Advance or revert a slide processing stage.

        Args:
            slide: Slide instance
            action: ``advance`` or ``revert``
            user: User performing the action
            observaciones: Required when action is ``revert``

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if action not in ("advance", "revert"):
            return False, _("Acción no válida.")

        validation_error = self._validate_revert_observaciones(
            action, observaciones
        )
        if validation_error:
            return False, validation_error

        try:
            if action == "advance":
                stage = slide.advance_stage()
            else:
                stage = slide.revert_last_stage()

            log_observaciones = self._format_log_observaciones(
                action, observaciones
            )
            if stage == "listo" and action == "advance":
                log_observaciones = log_observaciones or _(
                    "Portaobjetos listo para análisis."
                )

            ProcessingLog.log_action(
                protocol=slide.protocol,
                etapa=self.SLIDE_STAGE_LOG[stage],
                usuario=user,
                slide=slide,
                observaciones=log_observaciones,
            )
            return True, ""

        except ValueError as e:
            return False, str(e)
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

    MARK_READY_ALLOWED_STATUSES = (
        Protocol.Status.RECEIVED,
        Protocol.Status.PROCESSING,
    )

    def get_processing_readiness(self, protocol: Protocol) -> dict:
        """
        Assess whether technical processing is complete and protocol can go to READY.

        Returns:
            dict with keys: can_mark_ready, blockers, is_complete
        """
        blockers = []

        if protocol.status == Protocol.Status.READY:
            return {
                "can_mark_ready": False,
                "blockers": [],
                "is_complete": True,
                "already_ready": True,
            }

        if protocol.status == Protocol.Status.REJECTED:
            blockers.append(
                _("El protocolo está rechazado; no puede marcarse como listo.")
            )
            return {
                "can_mark_ready": False,
                "blockers": blockers,
                "is_complete": False,
                "already_ready": False,
            }

        if protocol.status not in self.MARK_READY_ALLOWED_STATUSES:
            blockers.append(
                _(
                    "El protocolo debe estar recibido o en procesamiento "
                    "para cerrar el trabajo de laboratorio."
                )
            )
            return {
                "can_mark_ready": False,
                "blockers": blockers,
                "is_complete": False,
                "already_ready": False,
            }

        slides = list(protocol.slides.all())
        if not slides:
            blockers.append(_("Debe registrar al menos un portaobjetos."))
        else:
            pending_slides = [
                s.codigo_portaobjetos
                for s in slides
                if s.estado != Slide.Status.LISTO
            ]
            if pending_slides:
                blockers.append(
                    _(
                        "Complete todas las etapas de los portaobjetos "
                        "(pendientes: %(codes)s)."
                    )
                    % {"codes": ", ".join(pending_slides)}
                )

        if protocol.analysis_type == Protocol.AnalysisType.HISTOPATHOLOGY:
            if not hasattr(protocol, "histopathology_sample"):
                blockers.append(
                    _("Este protocolo no tiene muestra de histopatología.")
                )
            else:
                cassettes = list(
                    protocol.histopathology_sample.cassettes.all()
                )
                if not cassettes:
                    blockers.append(_("Debe crear al menos un cassette."))
                else:
                    pending_cassettes = [
                        c.codigo_cassette
                        for c in cassettes
                        if c.estado != Cassette.Status.COMPLETADO
                    ]
                    if pending_cassettes:
                        blockers.append(
                            _(
                                "Complete todas las etapas de los cassettes "
                                "(pendientes: %(codes)s)."
                            )
                            % {"codes": ", ".join(pending_cassettes)}
                        )

        is_complete = len(blockers) == 0
        return {
            "can_mark_ready": is_complete,
            "blockers": blockers,
            "is_complete": is_complete,
            "already_ready": False,
        }

    def mark_ready_for_diagnosis(
        self, protocol: Protocol, user
    ) -> Tuple[bool, str]:
        """
        Mark protocol as ready for histopathological diagnosis (READY status).

        Args:
            protocol: Protocol instance
            user: Lab staff performing the action

        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        readiness = self.get_processing_readiness(protocol)

        if readiness.get("already_ready"):
            return False, _("El protocolo ya está listo para diagnóstico.")

        if not readiness["can_mark_ready"]:
            if readiness["blockers"]:
                return False, readiness["blockers"][0]
            return False, _("No se puede marcar el protocolo como listo.")

        try:
            protocol.status = Protocol.Status.READY
            protocol.save(update_fields=["status"])

            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=Protocol.Status.READY,
                changed_by=user,
                description=_(
                    "Procesamiento técnico finalizado; muestra lista para diagnóstico"
                ),
            )

            self._notify_protocol_ready(protocol)
            return True, ""

        except Exception as e:
            logger.error(
                f"Error marking protocol {protocol.pk} ready for diagnosis: {e}"
            )
            return False, str(e)

    def _notify_protocol_ready(self, protocol: Protocol) -> None:
        """Queue email and in-app notification when protocol becomes READY."""
        from protocols.emails import queue_email
        from protocols.models import EmailLog
        from protocols.services.notification_service import (
            NotificationService,
        )

        try:
            queue_email(
                email_type=EmailLog.EmailType.CUSTOM,
                recipient_email=protocol.veterinarian.email,
                subject=(
                    "Muestra lista para diagnóstico - Protocolo "
                    f"{protocol.protocol_number}"
                ),
                context={
                    "protocol": protocol,
                    "veterinarian": protocol.veterinarian,
                },
                template_name="emails/protocol_ready.html",
                protocol=protocol,
                veterinarian=protocol.veterinarian,
            )
        except Exception as e:
            logger.error(
                f"Failed to queue ready email for protocol {protocol.pk}: {e}"
            )

        try:
            NotificationService().create_for_ready(protocol)
        except Exception as e:
            logger.error(
                f"Failed to create in-app notification for protocol {protocol.pk}: {e}"
            )
