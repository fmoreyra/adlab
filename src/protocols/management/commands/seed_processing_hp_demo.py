"""Create demo histopathology protocols ready for lab processing review."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.urls import reverse

from accounts.models import Veterinarian
from accounts.test_helpers import ensure_veterinarian_profile_complete
from protocols.models import (
    HistopathologySample,
    Protocol,
    ReceptionLog,
)
from protocols.services.protocol_service import ProtocolProcessingService

User = get_user_model()

SCENARIOS = {
    "register": {
        "animal": "Luna",
        "diagnosis": "[TEST] HP recibido — probar registro unificado",
        "hint": "Sin cassettes ni slides; usar «Registrar muestra»",
    },
    "append": {
        "animal": "Bruno",
        "diagnosis": "[TEST] HP con cassettes — probar modo append de slides",
        "hint": "2 cassettes encasetados; agregar solo slides en registro",
    },
    "stages": {
        "animal": "Nala",
        "diagnosis": "[TEST] HP listo para cerrar procesamiento",
        "hint": "Cassettes y slides registrados; solo «Marcar listo para diagnóstico»",
    },
}


class Command(BaseCommand):
    """Seed received histopathology protocol(s) for manual processing QA."""

    help = (
        "Crea protocolo(s) de histopatología recibido(s) para probar "
        "registro unificado y etapas colapsadas en procesamiento."
    )

    def add_arguments(self, parser):
        """Scenario selection."""
        parser.add_argument(
            "--scenario",
            choices=["register", "append", "stages", "all"],
            default="register",
            help=(
                "register: recibido sin cassettes (default); "
                "append: cassettes sin slides; "
                "stages: cassettes + slides pendientes; "
                "all: los tres casos"
            ),
        )

    def handle(self, *args, **options):
        staff = self._get_or_create_staff()
        vet = self._get_or_create_veterinarian()
        service = ProtocolProcessingService()

        scenario_key = options["scenario"]
        keys = list(SCENARIOS) if scenario_key == "all" else [scenario_key]
        created = []

        for key in keys:
            case = SCENARIOS[key]
            protocol = self._create_received(
                vet,
                staff,
                case["animal"],
                case["diagnosis"],
            )
            if key == "append":
                self._seed_cassettes(service, protocol, staff)
            elif key == "stages":
                cassettes = self._seed_cassettes(service, protocol, staff)
                self._seed_slides(service, protocol, staff, cassettes)
            created.append((key, protocol, case["hint"]))

        self.stdout.write(
            self.style.SUCCESS("Protocolos HP para procesamiento:")
        )
        for key, protocol, hint in created:
            cassette_count = protocol.histopathology_sample.cassettes.count()
            slide_count = protocol.slides.count()
            self.stdout.write(
                f"  [{key}] {protocol.protocol_number} — "
                f"{protocol.animal_identification} "
                f"(cassettes: {cassette_count}, slides: {slide_count})"
            )
            self.stdout.write(f"           → {hint}")
            self.stdout.write(
                f"           Estado: {self._status_url(protocol.pk)}"
            )
            self.stdout.write(
                f"           Registro: {self._register_url(protocol.pk)}"
            )

        self.stdout.write(f"  Veterinario: {vet.get_full_name()}")
        self.stdout.write(f"  Login lab: {staff.email} (password de dev/test)")
        self.stdout.write("  Cola: /protocols/processing/queue/")

    def _status_url(self, protocol_pk):
        return (
            reverse("protocols:protocol_detail", kwargs={"pk": protocol_pk})
            + "#procesamiento-lab"
        )

    def _register_url(self, protocol_pk):
        return reverse(
            "protocols:sample_register",
            kwargs={"protocol_pk": protocol_pk},
        )

    def _create_received(self, vet, staff, animal, diagnosis):
        """Create submitted HP protocol and receive it."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.HISTOPATHOLOGY,
            veterinarian=vet,
            species="Canino",
            animal_identification=animal,
            presumptive_diagnosis=diagnosis,
            submission_date=date.today(),
        )
        HistopathologySample.objects.create(
            protocol=protocol,
            veterinarian=vet,
            material_submitted="Biopsia en formol — datos de demo procesamiento",
            number_of_containers=2,
            preservation="Formol 10%",
        )
        protocol.submit()
        protocol.receive(
            received_by=staff,
            sample_condition=Protocol.SampleCondition.OPTIMAL,
            reception_notes="Demo para prueba manual de procesamiento HP (Punto 2).",
        )
        ReceptionLog.log_action(
            protocol=protocol,
            action=ReceptionLog.Action.RECEIVED,
            user=staff,
            notes=protocol.reception_notes,
        )
        return protocol

    def _seed_cassettes(self, service, protocol, staff):
        """Create two encasetado cassettes via the processing service."""
        cassette_data = [
            {
                "material": "Fragmento hepático lóbulo derecho",
                "observaciones": "Demo cassette A",
            },
            {
                "material": "Ganglio mesentérico",
                "observaciones": "Demo cassette B",
            },
        ]
        success, cassettes, error = service.create_cassettes(
            protocol, cassette_data, staff
        )
        if not success:
            raise RuntimeError(f"No se pudieron crear cassettes: {error}")
        return cassettes

    def _seed_slides(self, service, protocol, staff, cassettes):
        """Create pending slides linked to demo cassettes."""
        slide_data = [
            {
                "tecnica_coloracion": "Hematoxilina-Eosina",
                "observaciones": "Slide 1 — cassette A",
                "cassette_ids": [cassettes[0].pk],
            },
            {
                "tecnica_coloracion": "Hematoxilina-Eosina",
                "observaciones": "Slide 2 — cassettes A+B",
                "cassette_ids": [cassettes[0].pk, cassettes[1].pk],
            },
        ]
        success, slides, error = service.register_histopathology_slides(
            protocol, slide_data, staff
        )
        if not success:
            raise RuntimeError(f"No se pudieron crear slides: {error}")
        return slides

    def _get_or_create_staff(self):
        """Return lab staff user, creating a demo account if needed."""
        staff = User.objects.filter(
            role=User.Role.PERSONAL_LAB, is_staff=True
        ).first()
        if staff:
            return staff

        staff = (
            User.objects.filter(is_staff=True)
            .exclude(role=User.Role.VETERINARIO)
            .first()
        )
        if staff:
            return staff

        staff, created = User.objects.get_or_create(
            email="demo.lab@adlab.local",
            defaults={
                "username": "demo_lab",
                "role": User.Role.PERSONAL_LAB,
                "is_staff": True,
                "email_verified": True,
                "first_name": "Demo",
                "last_name": "Laboratorio",
            },
        )
        if created:
            staff.set_password("demo1234")
            staff.save()
            self.stdout.write(
                "Usuario demo de laboratorio creado: demo.lab@adlab.local"
            )
        return staff

    def _get_or_create_veterinarian(self):
        """Return veterinarian, creating a demo profile if needed."""
        vet = Veterinarian.objects.first()
        if vet:
            return vet

        vet_user, created = User.objects.get_or_create(
            email="demo.vet@adlab.local",
            defaults={
                "username": "demo_vet",
                "role": User.Role.VETERINARIO,
                "is_staff": True,
                "email_verified": True,
                "first_name": "Ana",
                "last_name": "García",
            },
        )
        if created:
            vet_user.set_password("demo1234")
            vet_user.save()
            self.stdout.write(
                "Usuario demo veterinario creado: demo.vet@adlab.local"
            )

        vet, _ = Veterinarian.objects.get_or_create(
            user=vet_user,
            defaults={
                "first_name": "Ana",
                "last_name": "García",
                "license_number": "MP-DEMO-001",
                "phone": "+54 341 5550001",
                "email": "demo.vet@adlab.local",
            },
        )
        return ensure_veterinarian_profile_complete(vet)
