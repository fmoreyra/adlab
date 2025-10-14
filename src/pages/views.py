import os
from datetime import timedelta

from django import get_version
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import TemplateView, View

from protocols.models import Protocol, Report

User = get_user_model()


class HomeView(TemplateView):
    """
    Landing page for AdLab Laboratory System.
    """

    template_name = "pages/landing.html"

    def get_context_data(self, **kwargs):
        """Add statistics and system information to context."""
        context = super().get_context_data(**kwargs)

        # Get some statistics for the dashboard
        total_protocols = Protocol.objects.count()
        total_users = User.objects.count()
        total_veterinarians = User.objects.filter(
            role=User.Role.VETERINARIO
        ).count()

        # Get recent protocols
        recent_protocols = Protocol.objects.select_related(
            "veterinarian"
        ).order_by("-created_at")[:5]

        context.update(
            {
                "debug": settings.DEBUG,
                "django_ver": get_version(),
                "python_ver": os.environ["PYTHON_VERSION"],
                "total_protocols": total_protocols,
                "total_users": total_users,
                "total_veterinarians": total_veterinarians,
                "recent_protocols": recent_protocols,
            }
        )

        return context


class DashboardView(LoginRequiredMixin, View):
    """
    Main dashboard view that renders role-specific dashboard.
    """

    def get(self, request, *args, **kwargs):
        """Render role-specific dashboard."""
        user = request.user

        if user.is_veterinarian:
            return VeterinarianDashboardView.as_view()(
                request, *args, **kwargs
            )
        elif user.is_histopathologist:
            return HistopathologistDashboardView.as_view()(
                request, *args, **kwargs
            )
        elif user.is_lab_staff:
            return LabStaffDashboardView.as_view()(request, *args, **kwargs)
        elif user.is_admin_user:
            return AdminDashboardView.as_view()(request, *args, **kwargs)

        # Default fallback
        return render(request, "pages/dashboard_default.html", {"user": user})


class VeterinarianDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for veterinarians showing their protocols and statistics.
    """

    template_name = "pages/dashboard_veterinarian.html"

    def get(self, request, *args, **kwargs):
        """Handle GET request with permission checks."""
        user = request.user

        # Early return if not veterinarian
        if not user.is_veterinarian:
            return redirect("pages:dashboard")

        # Get veterinarian profile
        try:
            self.veterinarian = user.veterinarian_profile
        except Exception:
            return redirect("accounts:complete_profile")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add veterinarian-specific context data."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        veterinarian = self.veterinarian

        # Get statistics
        active_protocols = Protocol.objects.filter(
            veterinarian=veterinarian,
            status__in=[
                Protocol.Status.SUBMITTED,
                Protocol.Status.RECEIVED,
                Protocol.Status.PROCESSING,
                Protocol.Status.READY,
            ],
        ).count()

        ready_reports = Report.objects.filter(
            protocol__veterinarian=veterinarian, status=Report.Status.FINALIZED
        ).count()

        # Get current month start
        now = timezone.now()
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        monthly_protocols = Protocol.objects.filter(
            veterinarian=veterinarian, submission_date__gte=month_start.date()
        ).count()

        # Get recent protocols
        recent_protocols = (
            Protocol.objects.filter(veterinarian=veterinarian)
            .select_related("veterinarian")
            .order_by("-updated_at")[:5]
        )

        context.update(
            {
                "user": user,
                "veterinarian": veterinarian,
                "active_protocols_count": active_protocols,
                "ready_reports_count": ready_reports,
                "monthly_protocols_count": monthly_protocols,
                "recent_protocols": recent_protocols,
            }
        )

        return context


class LabStaffDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for laboratory staff showing processing queue and statistics.
    """

    template_name = "pages/dashboard_lab_staff.html"

    def get(self, request, *args, **kwargs):
        """Handle GET request with permission checks."""
        user = request.user

        # Early return if not lab staff
        if not user.is_lab_staff:
            return redirect("pages:dashboard")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add lab staff-specific context data."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get statistics
        pending_reception = Protocol.objects.filter(
            status=Protocol.Status.SUBMITTED
        ).count()

        processing_count = Protocol.objects.filter(
            status__in=[Protocol.Status.RECEIVED, Protocol.Status.PROCESSING]
        ).count()

        # Get today's received protocols
        today = timezone.now().date()
        today_received = Protocol.objects.filter(
            status__in=[Protocol.Status.RECEIVED, Protocol.Status.PROCESSING],
            reception_date__date=today,
        ).count()

        # Get processing queue
        processing_queue = (
            Protocol.objects.filter(
                status__in=[
                    Protocol.Status.RECEIVED,
                    Protocol.Status.PROCESSING,
                ]
            )
            .select_related("veterinarian")
            .order_by("reception_date")[:10]
        )

        context.update(
            {
                "user": user,
                "pending_reception_count": pending_reception,
                "processing_count": processing_count,
                "today_received_count": today_received,
                "processing_queue": processing_queue,
            }
        )

        return context


class HistopathologistDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for histopathologists showing pending reports and statistics.
    """

    template_name = "pages/dashboard_histopathologist.html"

    def get(self, request, *args, **kwargs):
        """Handle GET request with permission checks."""
        user = request.user

        # Early return if not histopathologist
        if not user.is_histopathologist:
            return redirect("pages:dashboard")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add histopathologist-specific context data - OPTIMIZED VERSION."""
        from django.core.cache import cache
        from django.db.models import Avg, F, Case, When, IntegerField
        
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Cache dashboard data for 2 minutes
        cache_key = f"histopathologist_dashboard_{user.id}"
        dashboard_data = cache.get(cache_key)
        
        if dashboard_data is None:
            # OPTIMIZED: Single query to get all statistics
            now = timezone.now()
            month_start = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            # Get all statistics in one query using aggregation
            stats = (
                Report.objects
                .aggregate(
                    pending_count=Count('id', filter=Q(status=Report.Status.DRAFT)),
                    monthly_count=Count(
                        'id', 
                        filter=Q(
                            status=Report.Status.FINALIZED, 
                            updated_at__gte=month_start
                        )
                    ),
                    avg_tat=Avg(
                        Case(
                            When(
                                status=Report.Status.FINALIZED,
                                protocol__reception_date__isnull=False,
                                then=F('updated_at__date') - F('protocol__reception_date')
                            ),
                            default=None,
                            output_field=IntegerField()
                        )
                    )
                )
            )

            # Get pending reports list
            pending_reports_list = (
                Report.objects.filter(status=Report.Status.DRAFT)
                .select_related("protocol__veterinarian")
                .order_by("created_at")[:10]
            )

            dashboard_data = {
                'pending_reports_count': stats['pending_count'] or 0,
                'monthly_reports_count': stats['monthly_count'] or 0,
                'avg_report_time': round(stats['avg_tat'] or 0, 1),
                'pending_reports_list': list(pending_reports_list),
            }
            
            cache.set(cache_key, dashboard_data, 120)  # Cache for 2 minutes

        context.update(
            {
                "user": user,
                "pending_reports_count": dashboard_data['pending_reports_count'],
                "monthly_reports_count": dashboard_data['monthly_reports_count'],
                "avg_report_time": dashboard_data['avg_report_time'],
                "pending_reports": dashboard_data['pending_reports_list'],
            }
        )

        return context


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard for administrators showing system statistics and health.
    """

    template_name = "pages/dashboard_admin.html"

    def get(self, request, *args, **kwargs):
        """Handle GET request with permission checks."""
        user = request.user

        # Early return if not admin
        if not user.is_admin_user:
            return redirect("pages:dashboard")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add admin-specific context data."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get current year and month
        now = timezone.now()
        year_start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Get system statistics
        total_protocols = Protocol.objects.filter(
            submission_date__gte=year_start.date()
        ).count()

        completed_reports = Report.objects.filter(
            status=Report.Status.FINALIZED, updated_at__gte=month_start
        ).count()

        total_users = User.objects.filter(is_active=True).count()

        # Get active users (logged in last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        active_users = User.objects.filter(
            last_login_at__gte=thirty_days_ago
        ).count()

        # Calculate average TAT (simplified)
        avg_tat_days = 0
        completed_protocols = Protocol.objects.filter(
            status=Protocol.Status.REPORT_SENT, reception_date__isnull=False
        ).order_by("-updated_at")[:100]

        if completed_protocols:
            total_days = 0
            count = 0
            for protocol in completed_protocols:
                if protocol.reception_date:
                    days = (
                        protocol.updated_at.date()
                        - protocol.reception_date.date()
                    ).days
                    if days >= 0:
                        total_days += days
                        count += 1

            if count > 0:
                avg_tat_days = round(total_days / count, 1)

        # Get recent activities (simplified)
        recent_activities = [
            {
                "icon": "file-text",
                "title": "Protocolos este año",
                "description": f"{total_protocols} protocolos registrados",
                "timestamp": year_start,
            },
            {
                "icon": "check-circle",
                "title": "Reportes este mes",
                "description": f"{completed_reports} reportes completados",
                "timestamp": month_start,
            },
            {
                "icon": "users",
                "title": "Usuarios activos",
                "description": f"{active_users} usuarios en los últimos 30 días",
                "timestamp": thirty_days_ago,
            },
        ]

        context.update(
            {
                "user": user,
                "total_protocols_count": total_protocols,
                "completed_reports_count": completed_reports,
                "total_users_count": total_users,
                "active_users_count": active_users,
                "avg_tat_days": avg_tat_days,
                "recent_activities": recent_activities,
            }
        )

        return context


class ManagementDashboardView(LoginRequiredMixin, TemplateView):
    """
    Management dashboard for laboratory oversight and KPIs.

    Accessible by: lab staff, histopathologists, and admin users.
    """

    template_name = "pages/management_dashboard.html"

    def get(self, request, *args, **kwargs):
        """Handle GET request with permission checks."""
        user = request.user

        # Early return if not management user
        if not (
            user.is_lab_staff or user.is_histopathologist or user.is_admin_user
        ):
            return redirect("pages:dashboard")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add management dashboard context data."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Add user information
        context.update(
            {
                "user": user,
                "is_management_user": True,
            }
        )

        return context
