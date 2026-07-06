"""
Management command: wipe protocol/workflow data, keep users and profiles.
"""

from django.core.management.base import BaseCommand

from accounts.models import User, Veterinarian
from protocols.models import NotificationPreference, Protocol
from protocols.services.reset_business_data_service import (
    count_business_rows,
    reset_business_data,
)


class Command(BaseCommand):
    """Remove operational data; preserve accounts, profiles, and audit logs."""

    help = (
        "Elimina protocolos, informes, órdenes de trabajo y contadores. "
        "Conserva usuarios, perfiles (veterinarios, staff), preferencias "
        "de notificación y AuthAuditLog."
    )

    def add_arguments(self, parser):
        """CLI flags."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar conteos sin borrar datos.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="No pedir confirmación interactiva.",
        )
        parser.add_argument(
            "--clear-pricing",
            action="store_true",
            help="También eliminar filas de PricingCatalog.",
        )
        parser.add_argument(
            "--no-clear-media",
            action="store_true",
            help="No borrar archivos en media/reports/.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        keep_pricing = not options["clear_pricing"]
        clear_media = not options["no_clear_media"]

        counts = count_business_rows(include_pricing=keep_pricing)
        total_rows = sum(counts.values())

        self.stdout.write("Datos operativos que se eliminarían:")
        for label, count in counts.items():
            self.stdout.write(f"  {label}: {count}")
        self.stdout.write(f"  Total filas: {total_rows}")
        self.stdout.write("")
        self.stdout.write("Se conservan:")
        self.stdout.write(f"  users: {User.objects.count()}")
        self.stdout.write(f"  veterinarians: {Veterinarian.objects.count()}")
        self.stdout.write(
            f"  notification preferences: {NotificationPreference.objects.count()}"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry-run — no se modificó la base.")
            )
            return

        if total_rows == 0 and not clear_media:
            self.stdout.write(
                self.style.WARNING("No hay datos operativos para borrar.")
            )
            return

        if not options["no_input"]:
            confirm = input("¿Continuar? [y/N] ")
            if confirm.strip().lower() not in {"y", "yes", "s", "si", "sí"}:
                self.stdout.write("Operación cancelada.")
                return

        deleted = reset_business_data(
            keep_pricing=keep_pricing,
            clear_media=clear_media,
        )

        self.stdout.write(self.style.SUCCESS("Reset completado."))
        for label, count in deleted.items():
            self.stdout.write(f"  {label}: {count}")

        remaining_protocols = Protocol.objects.count()
        if remaining_protocols:
            self.stdout.write(
                self.style.ERROR(
                    f"Advertencia: quedan {remaining_protocols} protocolo(s)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Usuarios intactos: {User.objects.count()} | "
                    f"Protocolos restantes: 0"
                )
            )
