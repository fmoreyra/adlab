import os
from datetime import timedelta

from django import get_version
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from protocols.models import Protocol, Report

User = get_user_model()


def home(request):
    """Landing page for AdLab Laboratory System."""
    
    # Get some statistics for the dashboard
    total_protocols = Protocol.objects.count()
    total_users = User.objects.count()
    total_veterinarians = User.objects.filter(role=User.Role.VETERINARIO).count()
    
    # Get recent protocols
    recent_protocols = Protocol.objects.select_related('veterinarian').order_by('-created_at')[:5]
    
    context = {
        "debug": settings.DEBUG,
        "django_ver": get_version(),
        "python_ver": os.environ["PYTHON_VERSION"],
        "total_protocols": total_protocols,
        "total_users": total_users,
        "total_veterinarians": total_veterinarians,
        "recent_protocols": recent_protocols,
    }

    return render(request, "pages/landing.html", context)


@login_required
def dashboard_view(request):
    """
    Main dashboard view that redirects to role-specific dashboard.
    
    Args:
        request: HTTP request
        
    Returns:
        HttpResponse: Redirect to role-specific dashboard
    """
    user = request.user
    
    if user.is_veterinarian:
        return veterinarian_dashboard(request)
    elif user.is_histopathologist:
        return histopathologist_dashboard(request)
    elif user.is_lab_staff:
        return lab_staff_dashboard(request)
    elif user.is_admin_user:
        return admin_dashboard(request)
    
    # Default fallback
    return render(request, 'pages/dashboard_default.html', {'user': user})


@login_required
def veterinarian_dashboard(request):
    """
    Dashboard for veterinarians showing their protocols and statistics.
    
    Args:
        request: HTTP request
        
    Returns:
        HttpResponse: Rendered veterinarian dashboard
    """
    user = request.user
    
    # Early return if not veterinarian
    if not user.is_veterinarian:
        return redirect('pages:dashboard')
    
    # Get veterinarian profile
    try:
        veterinarian = user.veterinarian_profile
    except Exception:
        return redirect('accounts:complete_profile')
    
    # Get statistics
    active_protocols = Protocol.objects.filter(
        veterinarian=veterinarian,
        status__in=[
            Protocol.Status.SUBMITTED,
            Protocol.Status.RECEIVED,
            Protocol.Status.PROCESSING,
            Protocol.Status.READY,
        ]
    ).count()
    
    ready_reports = Report.objects.filter(
        protocol__veterinarian=veterinarian,
        status=Report.Status.FINALIZED
    ).count()
    
    # Get current month start
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_protocols = Protocol.objects.filter(
        veterinarian=veterinarian,
        submission_date__gte=month_start.date()
    ).count()
    
    # Get recent protocols
    recent_protocols = Protocol.objects.filter(
        veterinarian=veterinarian
    ).select_related('veterinarian').order_by('-updated_at')[:5]
    
    context = {
        'user': user,
        'veterinarian': veterinarian,
        'active_protocols_count': active_protocols,
        'ready_reports_count': ready_reports,
        'monthly_protocols_count': monthly_protocols,
        'recent_protocols': recent_protocols,
    }
    
    return render(request, 'pages/dashboard_veterinarian.html', context)


@login_required
def lab_staff_dashboard(request):
    """
    Dashboard for laboratory staff showing processing queue and statistics.
    
    Args:
        request: HTTP request
        
    Returns:
        HttpResponse: Rendered lab staff dashboard
    """
    user = request.user
    
    # Early return if not lab staff
    if not user.is_lab_staff:
        return redirect('pages:dashboard')
    
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
        reception_date__date=today
    ).count()
    
    # Get processing queue
    processing_queue = Protocol.objects.filter(
        status__in=[Protocol.Status.RECEIVED, Protocol.Status.PROCESSING]
    ).select_related('veterinarian').order_by('reception_date')[:10]
    
    context = {
        'user': user,
        'pending_reception_count': pending_reception,
        'processing_count': processing_count,
        'today_received_count': today_received,
        'processing_queue': processing_queue,
    }
    
    return render(request, 'pages/dashboard_lab_staff.html', context)


@login_required
def histopathologist_dashboard(request):
    """
    Dashboard for histopathologists showing pending reports and statistics.
    
    Args:
        request: HTTP request
        
    Returns:
        HttpResponse: Rendered histopathologist dashboard
    """
    user = request.user
    
    # Early return if not histopathologist
    if not user.is_histopathologist:
        return redirect('pages:dashboard')
    
    # Get statistics
    pending_reports = Report.objects.filter(
        status=Report.Status.DRAFT
    ).count()
    
    # Get current month start
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_reports = Report.objects.filter(
        status=Report.Status.FINALIZED,
        updated_at__gte=month_start
    ).count()
    
    # Calculate average report time (simplified)
    avg_report_time = 0
    completed_reports = Report.objects.filter(
        status=Report.Status.FINALIZED
    ).select_related('protocol')[:100]
    
    if completed_reports:
        total_days = 0
        count = 0
        for report in completed_reports:
            if report.protocol.reception_date and report.updated_at:
                days = (report.updated_at.date() - report.protocol.reception_date.date()).days
                if days >= 0:
                    total_days += days
                    count += 1
        
        if count > 0:
            avg_report_time = round(total_days / count, 1)
    
    # Get pending reports
    pending_reports_list = Report.objects.filter(
        status=Report.Status.DRAFT
    ).select_related('protocol__veterinarian').order_by('created_at')[:10]
    
    context = {
        'user': user,
        'pending_reports_count': pending_reports,
        'monthly_reports_count': monthly_reports,
        'avg_report_time': avg_report_time,
        'pending_reports': pending_reports_list,
    }
    
    return render(request, 'pages/dashboard_histopathologist.html', context)


@login_required
def admin_dashboard(request):
    """
    Dashboard for administrators showing system statistics and health.
    
    Args:
        request: HTTP request
        
    Returns:
        HttpResponse: Rendered admin dashboard
    """
    user = request.user
    
    # Early return if not admin
    if not user.is_admin_user:
        return redirect('pages:dashboard')
    
    # Get current year and month
    now = timezone.now()
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get system statistics
    total_protocols = Protocol.objects.filter(
        submission_date__gte=year_start.date()
    ).count()
    
    completed_reports = Report.objects.filter(
        status=Report.Status.FINALIZED,
        updated_at__gte=month_start
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
        status=Protocol.Status.REPORT_SENT,
        reception_date__isnull=False
    ).order_by('-updated_at')[:100]
    
    if completed_protocols:
        total_days = 0
        count = 0
        for protocol in completed_protocols:
            if protocol.reception_date:
                days = (protocol.updated_at.date() - protocol.reception_date.date()).days
                if days >= 0:
                    total_days += days
                    count += 1
        
        if count > 0:
            avg_tat_days = round(total_days / count, 1)
    
    # Get recent activities (simplified)
    recent_activities = [
        {
            'icon': 'file-text',
            'title': 'Protocolos este año',
            'description': f'{total_protocols} protocolos registrados',
            'timestamp': year_start
        },
        {
            'icon': 'check-circle',
            'title': 'Reportes este mes',
            'description': f'{completed_reports} reportes completados',
            'timestamp': month_start
        },
        {
            'icon': 'users',
            'title': 'Usuarios activos',
            'description': f'{active_users} usuarios en los últimos 30 días',
            'timestamp': thirty_days_ago
        }
    ]
    
    context = {
        'user': user,
        'total_protocols_count': total_protocols,
        'completed_reports_count': completed_reports,
        'total_users_count': total_users,
        'active_users_count': active_users,
        'avg_tat_days': avg_tat_days,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'pages/dashboard_admin.html', context)
