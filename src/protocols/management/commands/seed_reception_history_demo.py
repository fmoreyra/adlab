"""Create demo cytology and histopathology protocols for reception history."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Veterinarian
from protocols.models import (
    CytologySample,
    HistopathologySample,
    Protocol,
    ReceptionLog,
)

User = get_user_model()


class Command(BaseCommand):
    """Seed two received protocols (cytology + histopathology) with reception logs."""

    help = (
        "Crea dos protocolos recibidos (citología e histopatología) "
        "con registros en el historial de recepción."
    )

    def handle(self, *args, **options):
        staff = self._get_or_create_staff()
        vet = self._get_or_create_veterinarian()

        cyto = self._create_received(
            vet,
            staff,
            Protocol.AnalysisType.CYTOLOGY,
            "Michi",
            "Felino",
            "Citología: linfadenopatía",
            lambda protocol: CytologySample.objects.create(
                protocol=protocol,
                veterinarian=vet,
                technique_used="Punción (PAAF)",
                sampling_site="Ganglio cervical",
                number_of_slides=2,
            ),
        )
        histo = self._create_received(
            vet,
            staff,
            Protocol.AnalysisType.HISTOPATHOLOGY,
            "Rocky",
            "Canino",
            "Histopatología: masa cutánea",
            lambda protocol: HistopathologySample.objects.create(
                protocol=protocol,
                veterinarian=vet,
                material_submitted="Fragmento de piel 2x1 cm",
                number_of_containers=1,
                preservation="Formol 10%",
            ),
        )

        self.stdout.write(self.style.SUCCESS("Protocolos creados:"))
        self.stdout.write(
            f"  Citología: {cyto.temporary_code} → {cyto.protocol_number}"
        )
        self.stdout.write(
            f"  Histopatología: {histo.temporary_code} → {histo.protocol_number}"
        )
        self.stdout.write(f"  Recibidos por: {staff.email}")
        self.stdout.write("  Historial: /protocols/reception/history/")

    def _create_received(
        self,
        vet,
        staff,
        analysis_type,
        animal,
        species,
        diagnosis,
        sample_factory,
    ):
        protocol = Protocol.objects.create(
            analysis_type=analysis_type,
            veterinarian=vet,
            species=species,
            animal_identification=animal,
            presumptive_diagnosis=diagnosis,
            submission_date=date.today(),
        )
        sample_factory(protocol)
        protocol.submit()
        protocol.receive(
            received_by=staff,
            sample_condition=Protocol.SampleCondition.OPTIMAL,
            reception_notes="Datos de demo para historial de recepción.",
        )
        ReceptionLog.log_action(
            protocol=protocol,
            action=ReceptionLog.Action.RECEIVED,
            user=staff,
            notes=protocol.reception_notes,
        )
        return protocol

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
        return vet
