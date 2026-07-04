"""Create demo cytology and histopathology protocols pending reception."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Veterinarian
from accounts.test_helpers import ensure_veterinarian_profile_complete
from protocols.models import (
    CytologySample,
    HistopathologySample,
    Protocol,
)

User = get_user_model()


# Casos para probar recepción: sin portaobjetos declarados (0) o con cantidad conocida.
# Los Slide solo existen tras recepcionar con number_slides_received >= 1.
CYTOLOGY_DEMO_CASES = [
    {
        "animal": "Bella",
        "species": "Canino",
        "diagnosis": "[TEST] Sin portaobjetos declarados — validar formulario",
        "technique": "Punción (PAAF)",
        "site": "Masa mamaria",
        "slides": 0,
        "hint": "Formulario precarga 0; debe ingresar ≥1 para recepcionar",
    },
    {
        "animal": "Simba",
        "species": "Felino",
        "diagnosis": "[TEST] Envío sin contar portaobjetos",
        "technique": "Impronta",
        "site": "Lesión nasal",
        "slides": 0,
        "hint": "Otro caso con 0 declarados; probar error al dejar 0 en recepción",
    },
    {
        "animal": "Toby",
        "species": "Canino",
        "diagnosis": "[TEST] Cantidad declarada vs recibida",
        "technique": "Punción (PAAF)",
        "site": "Linfonodo cervical",
        "slides": 3,
        "hint": "Declarados 3; probar recepción con 1 y documentar discrepancia",
    },
    {
        "animal": "Mía",
        "species": "Felino",
        "diagnosis": "[TEST] Un portaobjeto declarado",
        "technique": "Hisopado",
        "site": "Oído",
        "slides": 1,
        "hint": "Flujo feliz: recepcionar con 1",
    },
    {
        "animal": "Rex",
        "species": "Canino",
        "diagnosis": "[TEST] Sin declarar — solo registro en recepción",
        "technique": "Raspado",
        "site": "Piel ventral",
        "slides": 0,
        "hint": "0 declarados; recepcionar con 2 para crear 2 slides",
    },
]


class Command(BaseCommand):
    """Seed submitted protocols (cytology and/or histopathology) awaiting reception."""

    help = (
        "Crea protocolos enviados sin recepcionar con código temporal, "
        "visibles en /protocols/reception/."
    )

    def add_arguments(self, parser):
        """Optional count and sample types."""
        parser.add_argument(
            "--cytology-count",
            type=int,
            default=1,
            metavar="N",
            help="Cantidad de protocolos de citología (default: 1)",
        )
        parser.add_argument(
            "--histopathology",
            action="store_true",
            help="Incluir un protocolo de histopatología pendiente",
        )

    def handle(self, *args, **options):
        vet = self._get_or_create_veterinarian()
        cytology_count = max(0, options["cytology_count"])
        created_cytology = []

        for index in range(cytology_count):
            case = CYTOLOGY_DEMO_CASES[index % len(CYTOLOGY_DEMO_CASES)]
            protocol = self._create_submitted(
                vet,
                Protocol.AnalysisType.CYTOLOGY,
                case["animal"],
                case["species"],
                case["diagnosis"],
                lambda p, c=case: CytologySample.objects.create(
                    protocol=p,
                    veterinarian=vet,
                    technique_used=c["technique"],
                    sampling_site=c["site"],
                    number_of_slides=c["slides"],
                ),
            )
            created_cytology.append(protocol)

        created_histo = None
        if options["histopathology"]:
            created_histo = self._create_submitted(
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
        for index, protocol in enumerate(created_cytology):
            case = CYTOLOGY_DEMO_CASES[index % len(CYTOLOGY_DEMO_CASES)]
            slides = protocol.cytology_sample.number_of_slides
            has_slides = protocol.slides.exists()
            self.stdout.write(
                f"  Citología: {protocol.temporary_code} — "
                f"{protocol.animal_identification} "
                f"({slides} declarados, slides en BD: {has_slides})"
            )
            self.stdout.write(f"           → {case['hint']}")
        if created_histo:
            self.stdout.write(
                f"  Histopatología: {created_histo.temporary_code} "
                "(sin número definitivo)"
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
        return ensure_veterinarian_profile_complete(vet)
