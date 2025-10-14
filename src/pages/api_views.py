"""
Management Dashboard API Views for Step 09.

Provides real-time metrics for laboratory management including:
- Work in Progress (WIP) by stage
- Volume metrics (weekly, monthly, annual)
- Turnaround Time (TAT) metrics
- Productivity per histopathologist
- Sample aging and alerts
"""

from datetime import timedelta
from typing import Dict, List

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from accounts.models import User
from protocols.models import (
    Cassette,
    Protocol,
    Report,
    Slide,
)


class ManagementDashboardRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only management users can access dashboard APIs.

    Management users: lab staff, histopathologists, and admin users.
    """

    def test_func(self):
        """Check if user has management access."""
        user = self.request.user
        return user.is_authenticated and (
            user.is_lab_staff or user.is_histopathologist or user.is_admin_user
        )


class DashboardWIPView(
    LoginRequiredMixin, ManagementDashboardRequiredMixin, View
):
    """
    Get work-in-progress by processing stage.

    GET /api/dashboard/wip
    """

    def get(self, request, *args, **kwargs):
        """Return WIP metrics by stage for both analysis types."""
        try:
            wip_data = self._calculate_wip_metrics()
            return render(
                request,
                "pages/api/wip_widget.html",
                {
                    "histopatologia": wip_data["histopatologia"],
                    "citologia": wip_data["citologia"],
                    "timestamp": timezone.now().isoformat(),
                },
            )
        except Exception as e:
            return render(
                request,
                "pages/api/wip_widget.html",
                {"error": f"Error calculating WIP metrics: {str(e)}"},
            )

    def _calculate_wip_metrics(self) -> Dict:
        """Calculate WIP metrics for both analysis types."""
        # Get protocols by status and type
        protocols_by_status = (
            Protocol.objects.filter(
                status__in=[
                    Protocol.Status.SUBMITTED,
                    Protocol.Status.RECEIVED,
                    Protocol.Status.PROCESSING,
                    Protocol.Status.READY,
                ]
            )
            .values("analysis_type", "status")
            .annotate(count=Count("id"))
        )

        # Initialize structure
        wip_data = {
            "histopatologia": {
                "pendiente_recepcion": 0,
                "recibido": 0,
                "procesando": {
                    "encasetado": 0,
                    "fijacion": 0,
                    "corte": 0,
                    "coloracion": 0,
                },
                "listo_diagnostico": 0,
                "diagnostico": 0,
                "informe_borrador": 0,
                "listo_envio": 0,
            },
            "citologia": {
                "pendiente_recepcion": 0,
                "recibido": 0,
                "procesando": 0,
                "listo_diagnostico": 0,
                "diagnostico": 0,
                "informe_borrador": 0,
                "listo_envio": 0,
            },
        }

        # Map protocol statuses to WIP stages
        status_mapping = {
            Protocol.Status.SUBMITTED: "pendiente_recepcion",
            Protocol.Status.RECEIVED: "recibido",
            Protocol.Status.PROCESSING: "procesando",
            Protocol.Status.READY: "listo_diagnostico",
            Protocol.Status.REPORT_DRAFT: "informe_borrador",
        }

        # Populate basic counts
        for item in protocols_by_status:
            tipo = item["analysis_type"]
            status = item["status"]
            count = item["count"]

            if status in status_mapping:
                stage = status_mapping[status]
                if tipo == "histopathology":
                    if stage == "procesando":
                        # For histopathology, we need to get detailed processing stages
                        wip_data["histopatologia"][stage] = (
                            self._get_histopathology_processing_stages()
                        )
                    else:
                        wip_data["histopatologia"][stage] = count
                else:  # cytology
                    wip_data["citologia"][stage] = count

        # Get additional processing stage details for histopathology
        wip_data["histopatologia"]["procesando"] = (
            self._get_histopathology_processing_stages()
        )

        return wip_data

    def _get_histopathology_processing_stages(self) -> Dict:
        """Get detailed processing stages for histopathology."""
        # Get cassettes by processing stage
        cassette_stages = (
            Cassette.objects.filter(
                estado__in=[
                    Cassette.Status.PENDIENTE,
                    Cassette.Status.EN_PROCESO,
                    Cassette.Status.COMPLETADO,
                ]
            )
            .values("estado")
            .annotate(count=Count("id"))
        )

        # Get slides by processing stage
        slide_stages = (
            Slide.objects.filter(
                estado__in=[
                    Slide.Status.PENDIENTE,
                    Slide.Status.MONTADO,
                    Slide.Status.COLOREADO,
                    Slide.Status.LISTO,
                ]
            )
            .values("estado")
            .annotate(count=Count("id"))
        )

        stages = {"encasetado": 0, "fijacion": 0, "corte": 0, "coloracion": 0}

        # Map cassette and slide statuses to processing stages
        for item in cassette_stages:
            if item["estado"] == Cassette.Status.PENDIENTE:
                stages["encasetado"] += item["count"]
            elif item["estado"] == Cassette.Status.EN_PROCESO:
                stages["fijacion"] += item["count"]

        for item in slide_stages:
            if item["estado"] == Slide.Status.MONTADO:
                stages["corte"] += item["count"]
            elif item["estado"] == Slide.Status.COLOREADO:
                stages["coloracion"] += item["count"]

        return stages


class DashboardVolumeView(
    LoginRequiredMixin, ManagementDashboardRequiredMixin, View
):
    """
    Get volume metrics for specified period.

    GET /api/dashboard/volume?periodo=semana&tipo=ambos
    """

    def get(self, request, *args, **kwargs):
        """Return volume metrics for specified period and type."""
        try:
            periodo = request.GET.get("periodo", "mes")
            tipo = request.GET.get("tipo", "ambos")

            volume_data = self._calculate_volume_metrics(periodo, tipo)
            return render(request, "pages/api/volume_widget.html", volume_data)
        except Exception as e:
            return render(
                request,
                "pages/api/volume_widget.html",
                {"error": f"Error calculating volume metrics: {str(e)}"},
            )

    def _calculate_volume_metrics(self, periodo: str, tipo: str) -> Dict:
        """Calculate volume metrics for specified period and type."""
        now = timezone.now()

        # Calculate date range based on period
        if periodo == "semana":
            date_from = now - timedelta(days=7)
            date_to = now
        elif periodo == "mes":
            date_from = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            date_to = now
        elif periodo == "año":
            date_from = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            date_to = now
        else:
            date_from = now - timedelta(days=30)
            date_to = now

        # Build query filters
        protocol_filter = Q(submission_date__gte=date_from.date())
        report_filter = Q(
            updated_at__gte=date_from, status=Report.Status.FINALIZED
        )

        if tipo != "ambos":
            protocol_filter &= Q(analysis_type=tipo)
            report_filter &= Q(protocol__analysis_type=tipo)

        # Get protocol counts by type
        protocol_counts = (
            Protocol.objects.filter(protocol_filter)
            .values("analysis_type")
            .annotate(count=Count("id"))
        )

        # Get report counts by type
        report_counts = (
            Report.objects.filter(report_filter)
            .values("protocol__analysis_type")
            .annotate(count=Count("id"))
        )

        # Initialize result structure
        result = {
            "periodo": periodo,
            "fecha_desde": date_from.date().isoformat(),
            "fecha_hasta": date_to.date().isoformat(),
            "histopatologia": {
                "protocolos_recibidos": 0,
                "informes_enviados": 0,
                "promedio_dia": 0.0,
            },
            "citologia": {
                "protocolos_recibidos": 0,
                "informes_enviados": 0,
                "promedio_dia": 0.0,
            },
            "total": {"protocolos_recibidos": 0, "informes_enviados": 0},
        }

        # Populate protocol counts
        for item in protocol_counts:
            analysis_type = item["analysis_type"]
            count = item["count"]
            if analysis_type == "histopathology":
                result["histopatologia"]["protocolos_recibidos"] = count
            elif analysis_type == "cytology":
                result["citologia"]["protocolos_recibidos"] = count
            result["total"]["protocolos_recibidos"] += count

        # Populate report counts
        for item in report_counts:
            analysis_type = item["protocol__analysis_type"]
            count = item["count"]
            if analysis_type == "histopathology":
                result["histopatologia"]["informes_enviados"] = count
            elif analysis_type == "cytology":
                result["citologia"]["informes_enviados"] = count
            result["total"]["informes_enviados"] += count

        # Calculate daily averages
        days = (date_to - date_from).days + 1
        for tipo_analisis in ["histopatologia", "citologia"]:
            if days > 0:
                result[tipo_analisis]["promedio_dia"] = round(
                    result[tipo_analisis]["protocolos_recibidos"] / days, 1
                )

        return result


class DashboardTATView(
    LoginRequiredMixin, ManagementDashboardRequiredMixin, View
):
    """
    Get turnaround time metrics.

    GET /api/dashboard/tat
    """

    def get(self, request, *args, **kwargs):
        """Return TAT metrics for both analysis types."""
        try:
            tat_data = self._calculate_tat_metrics()
            return render(request, "pages/api/tat_widget.html", tat_data)
        except Exception as e:
            return render(
                request,
                "pages/api/tat_widget.html",
                {"error": f"Error calculating TAT metrics: {str(e)}"},
            )

    def _calculate_tat_metrics(self) -> Dict:
        """Calculate TAT metrics for both analysis types."""
        # Get completed reports from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)

        completed_reports = Report.objects.filter(
            status=Report.Status.FINALIZED,
            updated_at__gte=thirty_days_ago,
            protocol__reception_date__isnull=False,
        ).select_related("protocol")

        result = {
            "histopatologia": {
                "tat_promedio_dias": 0.0,
                "tat_mediana_dias": 0,
                "tat_minimo_dias": 0,
                "tat_maximo_dias": 0,
                "dentro_objetivo": 0,
            },
            "citologia": {
                "tat_promedio_dias": 0.0,
                "tat_mediana_dias": 0,
                "tat_minimo_dias": 0,
                "tat_maximo_dias": 0,
                "dentro_objetivo": 0,
            },
        }

        # Calculate TAT for each analysis type
        for analysis_type in ["histopathology", "cytology"]:
            reports = completed_reports.filter(
                protocol__analysis_type=analysis_type
            )

            if not reports.exists():
                continue

            # Calculate TAT in days for each report
            tat_days = []
            for report in reports:
                if report.protocol.reception_date:
                    tat = (
                        report.updated_at.date()
                        - report.protocol.reception_date
                    ).days
                    tat_days.append(tat)

            if tat_days:
                tat_days.sort()
                n = len(tat_days)

                # Map analysis type to result key
                result_key = (
                    "histopatologia"
                    if analysis_type == "histopathology"
                    else "citologia"
                )

                # Calculate metrics
                result[result_key]["tat_promedio_dias"] = round(
                    sum(tat_days) / n, 1
                )
                result[result_key]["tat_mediana_dias"] = tat_days[n // 2]
                result[result_key]["tat_minimo_dias"] = min(tat_days)
                result[result_key]["tat_maximo_dias"] = max(tat_days)

                # Calculate percentage within target (7 days for histopathology, 3 days for cytology)
                target_days = 7 if analysis_type == "histopathology" else 3
                within_target = sum(
                    1 for days in tat_days if days <= target_days
                )
                result[result_key]["dentro_objetivo"] = round(
                    (within_target / n) * 100
                )

        return result


class DashboardProductivityView(
    LoginRequiredMixin, ManagementDashboardRequiredMixin, View
):
    """
    Get productivity metrics per histopathologist.

    GET /api/dashboard/productivity?periodo=mes
    """

    def get(self, request, *args, **kwargs):
        """Return productivity metrics per histopathologist."""
        try:
            periodo = request.GET.get("periodo", "mes")
            productivity_data = self._calculate_productivity_metrics(periodo)
            return render(
                request,
                "pages/api/productivity_widget.html",
                productivity_data,
            )
        except Exception as e:
            return render(
                request,
                "pages/api/productivity_widget.html",
                {"error": f"Error calculating productivity metrics: {str(e)}"},
            )

    def _calculate_productivity_metrics(self, periodo: str) -> Dict:
        """Calculate productivity metrics per histopathologist."""
        now = timezone.now()

        # Calculate date range based on period
        if periodo == "semana":
            date_from = now - timedelta(days=7)
        elif periodo == "mes":
            date_from = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif periodo == "año":
            date_from = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            date_from = now - timedelta(days=30)

        # Get histopathologists with their completed reports
        histopathologists = User.objects.filter(
            is_histopathologist=True, is_active=True
        ).prefetch_related("report_set")

        histopathologist_data = []
        total_reports = 0

        for histo in histopathologists:
            # Get completed reports in period
            completed_reports = Report.objects.filter(
                histopathologist=histo,
                status=Report.Status.FINALIZED,
                updated_at__gte=date_from,
            ).select_related("protocol")

            if not completed_reports.exists():
                continue

            report_count = completed_reports.count()
            total_reports += report_count

            # Calculate average TAT for this histopathologist
            tat_days = []
            for report in completed_reports:
                if report.protocol.reception_date:
                    tat = (
                        report.updated_at.date()
                        - report.protocol.reception_date
                    ).days
                    tat_days.append(tat)

            avg_tat = (
                round(sum(tat_days) / len(tat_days), 1) if tat_days else 0
            )

            # Calculate weekly average
            weeks = max(1, (now - date_from).days / 7)
            weekly_avg = round(report_count / weeks, 2)

            histopathologist_data.append(
                {
                    "nombre": histo.get_full_name() or histo.email,
                    "informes_enviados": report_count,
                    "promedio_por_semana": weekly_avg,
                    "tat_promedio_dias": avg_tat,
                }
            )

        # Sort by number of reports (descending)
        histopathologist_data.sort(
            key=lambda x: x["informes_enviados"], reverse=True
        )

        return {
            "periodo": periodo,
            "histopatologos": histopathologist_data,
            "total_informes": total_reports,
        }


class DashboardAgingView(
    LoginRequiredMixin, ManagementDashboardRequiredMixin, View
):
    """
    Get sample aging metrics and overdue samples.

    GET /api/dashboard/aging
    """

    def get(self, request, *args, **kwargs):
        """Return sample aging metrics and overdue samples."""
        try:
            aging_data = self._calculate_aging_metrics()
            return render(request, "pages/api/aging_widget.html", aging_data)
        except Exception as e:
            return render(
                request,
                "pages/api/aging_widget.html",
                {"error": f"Error calculating aging metrics: {str(e)}"},
            )

    def _calculate_aging_metrics(self) -> Dict:
        """Calculate sample aging metrics and identify overdue samples."""
        now = timezone.now().date()

        # Get active protocols with reception dates
        active_protocols = Protocol.objects.filter(
            status__in=[
                Protocol.Status.RECEIVED,
                Protocol.Status.PROCESSING,
                Protocol.Status.READY,
            ],
            reception_date__isnull=False,
        ).select_related("veterinarian__user")

        # Calculate aging buckets
        aging_buckets = {
            "0_3_dias": 0,
            "4_7_dias": 0,
            "8_14_dias": 0,
            "mas_14_dias": 0,
        }

        overdue_protocols = []

        for protocol in active_protocols:
            reception_date = protocol.reception_date
            if hasattr(reception_date, "date"):
                reception_date = reception_date.date()
            days_since_reception = (now - reception_date).days

            # Categorize by age
            if days_since_reception <= 3:
                aging_buckets["0_3_dias"] += 1
            elif days_since_reception <= 7:
                aging_buckets["4_7_dias"] += 1
            elif days_since_reception <= 14:
                aging_buckets["8_14_dias"] += 1
            else:
                aging_buckets["mas_14_dias"] += 1

            # Identify overdue samples (beyond target TAT)
            target_days = (
                7 if protocol.analysis_type == "histopathology" else 3
            )
            if days_since_reception > target_days:
                overdue_protocols.append(
                    {
                        "protocolo_numero": protocol.protocol_number,
                        "animal": f"{protocol.animal_identification} - {protocol.species}",
                        "dias_desde_recepcion": days_since_reception,
                        "estado": protocol.get_status_display(),
                        "veterinario": protocol.veterinarian.get_full_name()
                        or protocol.veterinarian.user.email,
                    }
                )

        # Sort overdue protocols by days (most overdue first)
        overdue_protocols.sort(
            key=lambda x: x["dias_desde_recepcion"], reverse=True
        )

        return {
            "por_rango": aging_buckets,
            "protocolos_vencidos": overdue_protocols[:10],  # Limit to top 10
        }


class DashboardAlertsView(
    LoginRequiredMixin, ManagementDashboardRequiredMixin, View
):
    """
    Get system alerts for overdue samples and bottlenecks.

    GET /api/dashboard/alerts
    """

    def get(self, request, *args, **kwargs):
        """Return system alerts and bottlenecks."""
        try:
            alerts_data = self._calculate_alerts()
            return render(request, "pages/api/alerts_widget.html", alerts_data)
        except Exception as e:
            return render(
                request,
                "pages/api/alerts_widget.html",
                {"error": f"Error calculating alerts: {str(e)}"},
            )

    def _calculate_alerts(self) -> Dict:
        """Calculate system alerts and bottlenecks."""
        alerts = []

        # Check for TAT exceeded alerts
        tat_alerts = self._check_tat_alerts()
        if tat_alerts:
            alerts.extend(tat_alerts)

        # Check for bottleneck alerts
        bottleneck_alerts = self._check_bottleneck_alerts()
        if bottleneck_alerts:
            alerts.extend(bottleneck_alerts)

        return {"alerts": alerts}

    def _check_tat_alerts(self) -> List[Dict]:
        """Check for protocols exceeding target TAT."""
        now = timezone.now().date()
        alerts = []

        # Get overdue protocols
        overdue_protocols = Protocol.objects.filter(
            status__in=[
                Protocol.Status.RECEIVED,
                Protocol.Status.PROCESSING,
                Protocol.Status.READY,
                Protocol.Status.REPORT_DRAFT,
            ],
            reception_date__isnull=False,
        ).select_related("veterinarian__user")

        histo_overdue = []
        cyto_overdue = []

        for protocol in overdue_protocols:
            days_since_reception = (now - protocol.reception_date).days
            target_days = (
                7 if protocol.analysis_type == "histopathology" else 3
            )

            if days_since_reception > target_days:
                if protocol.analysis_type == "histopathology":
                    histo_overdue.append(protocol.protocol_number)
                else:
                    cyto_overdue.append(protocol.protocol_number)

        # Create alerts for each type
        if histo_overdue:
            alerts.append(
                {
                    "tipo": "tat_excedido",
                    "severidad": "alta",
                    "mensaje": f"{len(histo_overdue)} protocolos de histopatología exceden TAT objetivo",
                    "protocolos": histo_overdue[:5],  # Limit to 5
                }
            )

        if cyto_overdue:
            alerts.append(
                {
                    "tipo": "tat_excedido",
                    "severidad": "alta",
                    "mensaje": f"{len(cyto_overdue)} protocolos de citología exceden TAT objetivo",
                    "protocolos": cyto_overdue[:5],  # Limit to 5
                }
            )

        return alerts

    def _check_bottleneck_alerts(self) -> List[Dict]:
        """Check for processing bottlenecks."""
        alerts = []

        # Check for samples waiting for diagnosis
        ready_for_diagnosis = Protocol.objects.filter(
            status=Protocol.Status.READY
        ).count()

        if ready_for_diagnosis > 5:
            alerts.append(
                {
                    "tipo": "cuello_botella",
                    "severidad": "media",
                    "mensaje": f"{ready_for_diagnosis} muestras esperando diagnóstico",
                    "etapa": "listo_diagnostico",
                }
            )

        # Check for samples in processing for too long
        long_processing = Protocol.objects.filter(
            status=Protocol.Status.PROCESSING,
            updated_at__lt=timezone.now() - timedelta(days=3),
        ).count()

        if long_processing > 3:
            alerts.append(
                {
                    "tipo": "cuello_botella",
                    "severidad": "media",
                    "mensaje": f"{long_processing} muestras en procesamiento por más de 3 días",
                    "etapa": "procesamiento",
                }
            )

        return alerts
