"""Create demo cytology and histopathology protocols pending reception."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Veterinarian
from protocols.models import (
    CytologySample,
    HistopathologySample,
    Protocol,
)

User = get_user_model()


class Command(BaseCommand):
    """Seed two submitted protocols (cytology + histopathology) awaiting reception."""

    help = (
        "Crea dos protocolos enviados sin recepcionar (citología e histopatología) "
        "con código temporal, visibles en /protocols/reception/."
    )

    def handle(self, *args, **options):
        vet = self._get_or_create_veterinarian()

        cyto = self._create_submitted(
            vet,
            Protocol.AnalysisType.CYTOLOGY,
            "Luna",
            "Felino",
            "Citología pendiente: lesión cutánea",
            lambda protocol: CytologySample.objects.create(
                protocol=protocol,
                veterinarian=vet,
                technique_used="Impronta",
                sampling_site="Masa en dorso",
                number_of_slides=3,
            ),
        )
        histo = self._create_submitted(
            vet,
            Protocol.AnalysisType.HISTOPATHOLOGY,
            "Thor",
            "Canino",
            "Histopatología pendiente: biopsia hepática",
            lambda protocol: HistopathologySample.objects.create(
                protocol=protocol,
                veterinarian=vet,
                material_submitted="Biopsia hepática en formol",
                number_of_containers=2,
                preservation="Formol 10%",
            ),
        )

        self.stdout.write(
            self.style.SUCCESS("Protocolos pendientes de recepción:")
        )
        self.stdout.write(
            f"  Citología: {cyto.temporary_code} (sin número definitivo)"
        )
        self.stdout.write(
            f"  Histopatología: {histo.temporary_code} (sin número definitivo)"
        )
        self.stdout.write(f"  Veterinario: {vet.get_full_name()}")
        self.stdout.write("  Recepción: /protocols/reception/")

    def _create_submitted(
        self, vet, analysis_type, animal, species, diagnosis, sample_factory
    ):
        """Create protocol, sample, submit (assigns temporary_code), do not receive."""
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
        return protocol

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
