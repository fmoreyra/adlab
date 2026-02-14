# Step 15: User Dashboards & Feature Discovery

## Problem Statement

Currently, users must navigate through the system using traditional menu structures and URL patterns. There's no centralized way for users to:

- **Discover available features** based on their role
- **Access quick actions** for common tasks
- **View personalized information** relevant to their workflow
- **Navigate efficiently** through the system's capabilities
- **Understand their role-specific workflows** and next steps

The system needs **role-specific dashboards** that serve as central hubs where users can:
- See what features are available to them
- Access quick actions for common tasks
- View relevant statistics and information
- Navigate to different system modules
- Understand their workflow and responsibilities

## Requirements

### Functional Requirements (RF15)

- **RF15.1**: Role-specific dashboard landing pages for each user type
- **RF15.2**: Feature discovery cards showing available capabilities
- **RF15.3**: Quick action buttons for common tasks
- **RF15.4**: Personalized statistics and information widgets
- **RF15.5**: Workflow guidance and next steps suggestions
- **RF15.6**: Recent activity and notifications display
- **RF15.7**: Search functionality across available features
- **RF15.8**: Responsive design for mobile and desktop access
- **RF15.9**: Customizable dashboard layout (admin configurable)
- **RF15.10**: Integration with existing system modules

### Non-Functional Requirements

- **Performance**: Dashboard load time < 2 seconds
- **Usability**: Intuitive navigation and clear feature discovery
- **Responsiveness**: Works on mobile, tablet, and desktop
- **Accessibility**: WCAG 2.1 AA compliance
- **Security**: Role-based access control for all dashboard features

## User Role Analysis

### 1. Veterinario Cliente (Veterinary Client)
**Primary Workflow**: Submit protocols → Track status → Download reports

**Available Features**:
- ✅ **Protocol Submission**: Create new cytology/histopathology protocols
- ✅ **Protocol Management**: View, edit, and track submitted protocols
- ✅ **Report Access**: Download completed reports and work orders
- ✅ **Profile Management**: Update personal and professional information
- ✅ **Status Tracking**: Monitor protocol progress through the system

**Dashboard Focus**: Protocol-centric workflow with status tracking

### 2. Personal de Laboratorio (Laboratory Staff)
**Primary Workflow**: Receive samples → Process samples → Update status

**Available Features**:
- ✅ **Sample Reception**: Confirm receipt of samples and assign protocol numbers
- ✅ **Processing Management**: Register cassettes and slides
- ✅ **Status Updates**: Update protocol processing status
- ✅ **Work Order Creation**: Generate work orders for completed protocols
- ✅ **Inventory Tracking**: Manage sample processing inventory

**Dashboard Focus**: Operational workflow with processing status

### 3. Personal de Laboratorio (Laboratory Staff)
**Primary Workflow**: Receive samples → Process samples → Generate reports → Sign documents

**Available Features**:
- ✅ **Sample Reception**: Confirm receipt and assign protocol numbers
- ✅ **Processing Management**: Track cassettes and slides through stages
- ✅ **Report Generation**: Create and finalize diagnostic reports (with permission)
- ✅ **Case Review**: Access complete case information and samples
- ✅ **Digital Signatures**: Sign reports and work orders
- ✅ **Report Management**: Edit, finalize, and send reports (with permission)
- ✅ **Quality Control**: Review and approve processing quality (with permission)
- ✅ **Work Orders**: Generate and manage billing documents

**Dashboard Focus**: Unified laboratory workflow with permission-based access to reporting functions

**Note**: Step-16 consolidates Histopathologist functionality into Laboratory Staff role with granular permissions for report creation.

### 4. Administrador (Administrator)
**Primary Workflow**: System management → User administration → Configuration

**Available Features**:
- ✅ **User Management**: Create, edit, and manage user accounts
- ✅ **System Configuration**: Configure system settings and parameters
- ✅ **Analytics & Reports**: Access system-wide analytics and reports
- ✅ **Audit Logs**: Review system activity and security logs
- ✅ **Data Management**: Manage reference data and catalogs

**Dashboard Focus**: Administrative overview with system health

## Dashboard Design

### 1. Veterinario Dashboard
```html
<!-- Veterinario Dashboard Layout -->
<div class="dashboard-container">
  <!-- Welcome Section -->
  <div class="welcome-section">
    <h1>Bienvenido, Dr. [Nombre]</h1>
    <p>Panel de control para veterinarios clientes</p>
  </div>

  <!-- Quick Actions -->
  <div class="quick-actions">
    <h2>Acciones Rápidas</h2>
    <div class="action-cards">
      <a href="{% url 'protocols:protocol_select_type' %}" class="action-card primary">
        <i class="fas fa-plus-circle"></i>
        <h3>Nuevo Protocolo</h3>
        <p>Enviar muestra para análisis</p>
      </a>
      <a href="{% url 'protocols:protocol_list' %}" class="action-card">
        <i class="fas fa-list"></i>
        <h3>Mis Protocolos</h3>
        <p>Ver estado de mis muestras</p>
      </a>
      <a href="{% url 'accounts:veterinarian_profile_detail' %}" class="action-card">
        <i class="fas fa-user"></i>
        <h3>Mi Perfil</h3>
        <p>Actualizar información</p>
      </a>
    </div>
  </div>

  <!-- Statistics Widgets -->
  <div class="stats-grid">
    <div class="stat-card">
      <h3>Protocolos Activos</h3>
      <div class="stat-number">{{ active_protocols_count }}</div>
      <p>En proceso</p>
    </div>
    <div class="stat-card">
      <h3>Reportes Listos</h3>
      <div class="stat-number">{{ ready_reports_count }}</div>
      <p>Para descargar</p>
    </div>
    <div class="stat-card">
      <h3>Este Mes</h3>
      <div class="stat-number">{{ monthly_protocols_count }}</div>
      <p>Protocolos enviados</p>
    </div>
  </div>

  <!-- Recent Activity -->
  <div class="recent-activity">
    <h2>Actividad Reciente</h2>
    <div class="activity-list">
      {% for protocol in recent_protocols %}
        <div class="activity-item">
          <div class="activity-icon">
            <i class="fas fa-file-medical"></i>
          </div>
          <div class="activity-content">
            <h4>Protocolo {{ protocol.protocol_number }}</h4>
            <p>Estado: {{ protocol.get_status_display }}</p>
            <span class="activity-time">{{ protocol.updated_at|timesince }} atrás</span>
          </div>
          <div class="activity-action">
            <a href="{% url 'protocols:protocol_detail' protocol.pk %}" class="btn btn-sm">Ver</a>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>

  <!-- Feature Discovery -->
  <div class="feature-discovery">
    <h2>Funcionalidades Disponibles</h2>
    <div class="feature-grid">
      <div class="feature-card">
        <i class="fas fa-microscope"></i>
        <h3>Análisis Citológico</h3>
        <p>Enviar muestras para análisis citológico</p>
        <a href="{% url 'protocols:protocol_create_cytology' %}" class="feature-link">Comenzar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-cut"></i>
        <h3>Análisis Histopatológico</h3>
        <p>Enviar muestras para análisis histopatológico</p>
        <a href="{% url 'protocols:protocol_create_histopathology' %}" class="feature-link">Comenzar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-download"></i>
        <h3>Descargar Reportes</h3>
        <p>Acceder a reportes completados</p>
        <a href="{% url 'protocols:report_history' %}" class="feature-link">Ver Reportes</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-receipt"></i>
        <h3>Órdenes de Trabajo</h3>
        <p>Ver y descargar órdenes de trabajo</p>
        <a href="{% url 'protocols:workorder_list' %}" class="feature-link">Ver Órdenes</a>
      </div>
    </div>
  </div>
</div>
```

### 2. Personal de Laboratorio Dashboard
```html
<!-- Personal de Laboratorio Dashboard -->
<div class="dashboard-container">
  <!-- Welcome Section -->
  <div class="welcome-section">
    <h1>Panel de Laboratorio</h1>
    <p>Gestión de recepción y procesamiento de muestras</p>
  </div>

  <!-- Quick Actions -->
  <div class="quick-actions">
    <h2>Acciones Rápidas</h2>
    <div class="action-cards">
      <a href="{% url 'protocols:reception_search' %}" class="action-card primary">
        <i class="fas fa-inbox"></i>
        <h3>Recepción de Muestras</h3>
        <p>Confirmar recepción de muestras</p>
      </a>
      <a href="{% url 'protocols:processing_dashboard' %}" class="action-card">
        <i class="fas fa-cogs"></i>
        <h3>Procesamiento</h3>
        <p>Gestionar procesamiento de muestras</p>
      </a>
      <a href="{% url 'protocols:workorder_pending_protocols' %}" class="action-card">
        <i class="fas fa-receipt"></i>
        <h3>Órdenes de Trabajo</h3>
        <p>Crear órdenes de trabajo</p>
      </a>
    </div>
  </div>

  <!-- Statistics Widgets -->
  <div class="stats-grid">
    <div class="stat-card urgent">
      <h3>Muestras Pendientes</h3>
      <div class="stat-number">{{ pending_reception_count }}</div>
      <p>Esperando recepción</p>
    </div>
    <div class="stat-card">
      <h3>En Procesamiento</h3>
      <div class="stat-number">{{ processing_count }}</div>
      <p>Muestras activas</p>
    </div>
    <div class="stat-card">
      <h3>Hoy</h3>
      <div class="stat-number">{{ today_received_count }}</div>
      <p>Muestras recibidas</p>
    </div>
  </div>

  <!-- Processing Queue -->
  <div class="processing-queue">
    <h2>Cola de Procesamiento</h2>
    <div class="queue-list">
      {% for protocol in processing_queue %}
        <div class="queue-item">
          <div class="queue-info">
            <h4>{{ protocol.protocol_number }}</h4>
            <p>{{ protocol.analysis_type_display }} - {{ protocol.veterinarian.name }}</p>
          </div>
          <div class="queue-status">
            <span class="status-badge {{ protocol.status }}">{{ protocol.get_status_display }}</span>
          </div>
          <div class="queue-actions">
            <a href="{% url 'protocols:processing_status' protocol.pk %}" class="btn btn-sm">Procesar</a>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>

  <!-- Feature Discovery -->
  <div class="feature-discovery">
    <h2>Herramientas de Laboratorio</h2>
    <div class="feature-grid">
      <div class="feature-card">
        <i class="fas fa-search"></i>
        <h3>Buscar Protocolos</h3>
        <p>Buscar protocolos por número o veterinario</p>
        <a href="{% url 'protocols:reception_search' %}" class="feature-link">Buscar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-tags"></i>
        <h3>Generar Etiquetas</h3>
        <p>Crear etiquetas para muestras</p>
        <a href="{% url 'protocols:reception_pending' %}" class="feature-link">Generar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-clipboard-list"></i>
        <h3>Registrar Cassettes</h3>
        <p>Registrar cassettes de procesamiento</p>
        <a href="{% url 'protocols:processing_queue' %}" class="feature-link">Registrar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-microscope"></i>
        <h3>Registrar Portaobjetos</h3>
        <p>Registrar portaobjetos para análisis</p>
        <a href="{% url 'protocols:processing_queue' %}" class="feature-link">Registrar</a>
      </div>
    </div>
  </div>
</div>
```

### 3. Histopatólogo Dashboard
```html
<!-- Histopatólogo Dashboard -->
<div class="dashboard-container">
  <!-- Welcome Section -->
  <div class="welcome-section">
    <h1>Panel de Histopatólogo</h1>
    <p>Generación de reportes y análisis diagnósticos</p>
  </div>

  <!-- Quick Actions -->
  <div class="quick-actions">
    <h2>Acciones Rápidas</h2>
    <div class="action-cards">
      <a href="{% url 'protocols:report_pending_list' %}" class="action-card primary">
        <i class="fas fa-clipboard-list"></i>
        <h3>Reportes Pendientes</h3>
        <p>Casos esperando reporte</p>
      </a>
      <a href="{% url 'protocols:report_history' %}" class="action-card">
        <i class="fas fa-history"></i>
        <h3>Historial de Reportes</h3>
        <p>Ver reportes completados</p>
      </a>
      <a href="{% url 'accounts:profile' %}" class="action-card">
        <i class="fas fa-signature"></i>
        <h3>Mi Firma Digital</h3>
        <p>Gestionar firma digital</p>
      </a>
    </div>
  </div>

  <!-- Statistics Widgets -->
  <div class="stats-grid">
    <div class="stat-card urgent">
      <h3>Reportes Pendientes</h3>
      <div class="stat-number">{{ pending_reports_count }}</div>
      <p>Esperando diagnóstico</p>
    </div>
    <div class="stat-card">
      <h3>Este Mes</h3>
      <div class="stat-number">{{ monthly_reports_count }}</div>
      <p>Reportes completados</p>
    </div>
    <div class="stat-card">
      <h3>Tiempo Promedio</h3>
      <div class="stat-number">{{ avg_report_time }}</div>
      <p>Días por reporte</p>
    </div>
  </div>

  <!-- Pending Reports -->
  <div class="pending-reports">
    <h2>Casos Pendientes</h2>
    <div class="reports-list">
      {% for report in pending_reports %}
        <div class="report-item">
          <div class="report-info">
            <h4>{{ report.protocol.protocol_number }}</h4>
            <p>{{ report.protocol.analysis_type_display }} - {{ report.protocol.veterinarian.name }}</p>
            <span class="report-priority {{ report.priority }}">{{ report.get_priority_display }}</span>
          </div>
          <div class="report-actions">
            <a href="{% url 'protocols:report_edit' report.pk %}" class="btn btn-primary">Continuar</a>
            <a href="{% url 'protocols:report_detail' report.pk %}" class="btn btn-outline">Ver</a>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>

  <!-- Feature Discovery -->
  <div class="feature-discovery">
    <h2>Herramientas de Diagnóstico</h2>
    <div class="feature-grid">
      <div class="feature-card">
        <i class="fas fa-edit"></i>
        <h3>Crear Reporte</h3>
        <p>Generar nuevo reporte diagnóstico</p>
        <a href="{% url 'protocols:report_pending_list' %}" class="feature-link">Comenzar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-file-pdf"></i>
        <h3>Generar PDF</h3>
        <p>Crear PDF del reporte</p>
        <a href="{% url 'protocols:report_history' %}" class="feature-link">Generar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-paper-plane"></i>
        <h3>Enviar Reporte</h3>
        <p>Enviar reporte al veterinario</p>
        <a href="{% url 'protocols:report_history' %}" class="feature-link">Enviar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-chart-line"></i>
        <h3>Estadísticas</h3>
        <p>Ver estadísticas de productividad</p>
        <a href="{% url 'protocols:analytics' %}" class="feature-link">Ver Stats</a>
      </div>
    </div>
  </div>
</div>
```

### 4. Administrador Dashboard
```html
<!-- Administrador Dashboard -->
<div class="dashboard-container">
  <!-- Welcome Section -->
  <div class="welcome-section">
    <h1>Panel de Administración</h1>
    <p>Gestión del sistema y configuración</p>
  </div>

  <!-- Quick Actions -->
  <div class="quick-actions">
    <h2>Acciones Rápidas</h2>
    <div class="action-cards">
      <a href="{% url 'admin:index' %}" class="action-card primary">
        <i class="fas fa-cog"></i>
        <h3>Administración</h3>
        <p>Panel de administración Django</p>
      </a>
      <a href="{% url 'protocols:analytics' %}" class="action-card">
        <i class="fas fa-chart-bar"></i>
        <h3>Analíticas</h3>
        <p>Reportes y estadísticas</p>
      </a>
      <a href="{% url 'accounts:user_list' %}" class="action-card">
        <i class="fas fa-users"></i>
        <h3>Usuarios</h3>
        <p>Gestionar usuarios</p>
      </a>
    </div>
  </div>

  <!-- System Health -->
  <div class="system-health">
    <h2>Estado del Sistema</h2>
    <div class="health-grid">
      <div class="health-card">
        <i class="fas fa-database"></i>
        <h3>Base de Datos</h3>
        <span class="health-status healthy">Operativa</span>
      </div>
      <div class="health-card">
        <i class="fas fa-envelope"></i>
        <h3>Email</h3>
        <span class="health-status healthy">Configurado</span>
      </div>
      <div class="health-card">
        <i class="fas fa-hdd"></i>
        <h3>Almacenamiento</h3>
        <span class="health-status warning">85% usado</span>
      </div>
      <div class="health-card">
        <i class="fas fa-users"></i>
        <h3>Usuarios Activos</h3>
        <span class="health-status healthy">{{ active_users_count }}</span>
      </div>
    </div>
  </div>

  <!-- Statistics Overview -->
  <div class="stats-overview">
    <h2>Resumen del Sistema</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Protocolos Totales</h3>
        <div class="stat-number">{{ total_protocols_count }}</div>
        <p>Este año</p>
      </div>
      <div class="stat-card">
        <h3>Reportes Completados</h3>
        <div class="stat-number">{{ completed_reports_count }}</div>
        <p>Este mes</p>
      </div>
      <div class="stat-card">
        <h3>Usuarios Registrados</h3>
        <div class="stat-number">{{ total_users_count }}</div>
        <p>En el sistema</p>
      </div>
      <div class="stat-card">
        <h3>Tiempo Promedio</h3>
        <div class="stat-number">{{ avg_tat_days }}</div>
        <p>Días TAT</p>
      </div>
    </div>
  </div>

  <!-- Recent Activity -->
  <div class="recent-activity">
    <h2>Actividad Reciente</h2>
    <div class="activity-list">
      {% for activity in recent_activities %}
        <div class="activity-item">
          <div class="activity-icon">
            <i class="fas fa-{{ activity.icon }}"></i>
          </div>
          <div class="activity-content">
            <h4>{{ activity.title }}</h4>
            <p>{{ activity.description }}</p>
            <span class="activity-time">{{ activity.timestamp|timesince }} atrás</span>
          </div>
        </div>
      {% endfor %}
    </div>
  </div>

  <!-- Feature Discovery -->
  <div class="feature-discovery">
    <h2>Herramientas de Administración</h2>
    <div class="feature-grid">
      <div class="feature-card">
        <i class="fas fa-user-plus"></i>
        <h3>Gestionar Usuarios</h3>
        <p>Crear y administrar cuentas de usuario</p>
        <a href="{% url 'admin:accounts_user_changelist' %}" class="feature-link">Gestionar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-cogs"></i>
        <h3>Configuración</h3>
        <p>Configurar parámetros del sistema</p>
        <a href="{% url 'admin:config_systemconfig_changelist' %}" class="feature-link">Configurar</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-chart-line"></i>
        <h3>Analíticas</h3>
        <p>Ver reportes y estadísticas del sistema</p>
        <a href="{% url 'protocols:analytics' %}" class="feature-link">Ver Analíticas</a>
      </div>
      <div class="feature-card">
        <i class="fas fa-shield-alt"></i>
        <h3>Seguridad</h3>
        <p>Monitorear seguridad y auditoría</p>
        <a href="{% url 'admin:accounts_authauditlog_changelist' %}" class="feature-link">Monitorear</a>
      </div>
    </div>
  </div>
</div>
```

## Implementation

### 1. Dashboard Views
```python
# pages/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from datetime import datetime, timedelta
from accounts.models import User
from protocols.models import Protocol, Report, WorkOrder

@login_required
def dashboard_view(request):
    """Main dashboard view that redirects to role-specific dashboard."""
    user = request.user
    
    if user.is_veterinarian:
        return veterinarian_dashboard(request)
    elif user.is_lab_staff:
        return lab_staff_dashboard(request)
    elif user.is_histopathologist:
        return histopathologist_dashboard(request)
    elif user.is_admin_user:
        return admin_dashboard(request)
    else:
        return render(request, 'pages/dashboard_default.html')

@login_required
def veterinarian_dashboard(request):
    """Dashboard for veterinarians."""
    user = request.user
    
    # Get veterinarian profile
    try:
        veterinarian = user.veterinarian_profile
    except:
        return redirect('accounts:complete_profile')
    
    # Get statistics
    active_protocols = Protocol.objects.filter(
        veterinarian=veterinarian,
        status__in=['submitted', 'received', 'processing', 'ready_for_report']
    ).count()
    
    ready_reports = Report.objects.filter(
        protocol__veterinarian=veterinarian,
        status='finalized'
    ).count()
    
    monthly_protocols = Protocol.objects.filter(
        veterinarian=veterinarian,
        submission_date__gte=datetime.now().replace(day=1)
    ).count()
    
    # Get recent protocols
    recent_protocols = Protocol.objects.filter(
        veterinarian=veterinarian
    ).order_by('-updated_at')[:5]
    
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
    """Dashboard for laboratory staff."""
    user = request.user
    
    # Get statistics
    pending_reception = Protocol.objects.filter(
        status='submitted'
    ).count()
    
    processing_count = Protocol.objects.filter(
        status__in=['received', 'processing']
    ).count()
    
    today_received = Protocol.objects.filter(
        status='received',
        received_date__date=datetime.now().date()
    ).count()
    
    # Get processing queue
    processing_queue = Protocol.objects.filter(
        status__in=['received', 'processing']
    ).select_related('veterinarian').order_by('received_date')[:10]
    
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
    """Dashboard for histopathologists."""
    user = request.user
    
    # Get statistics
    pending_reports = Report.objects.filter(
        status='draft'
    ).count()
    
    monthly_reports = Report.objects.filter(
        status='finalized',
        finalized_at__gte=datetime.now().replace(day=1)
    ).count()
    
    # Calculate average report time
    completed_reports = Report.objects.filter(
        status='finalized',
        finalized_at__isnull=False
    ).select_related('protocol')
    
    if completed_reports.exists():
        total_days = sum([
            (report.finalized_at - report.protocol.received_date).days
            for report in completed_reports
            if report.protocol.received_date
        ])
        avg_report_time = round(total_days / completed_reports.count(), 1)
    else:
        avg_report_time = 0
    
    # Get pending reports
    pending_reports_list = Report.objects.filter(
        status='draft'
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
    """Dashboard for administrators."""
    user = request.user
    
    # Get system statistics
    total_protocols = Protocol.objects.filter(
        submission_date__year=datetime.now().year
    ).count()
    
    completed_reports = Report.objects.filter(
        status='finalized',
        finalized_at__gte=datetime.now().replace(day=1)
    ).count()
    
    total_users = User.objects.filter(is_active=True).count()
    active_users = User.objects.filter(
        last_login_at__gte=datetime.now() - timedelta(days=30)
    ).count()
    
    # Calculate average TAT
    completed_protocols = Protocol.objects.filter(
        status='completed',
        completed_date__isnull=False
    )
    
    if completed_protocols.exists():
        total_days = sum([
            (protocol.completed_date - protocol.received_date).days
            for protocol in completed_protocols
            if protocol.received_date
        ])
        avg_tat_days = round(total_days / completed_protocols.count(), 1)
    else:
        avg_tat_days = 0
    
    # Get recent activities (simplified)
    recent_activities = [
        {
            'icon': 'user-plus',
            'title': 'Nuevo usuario registrado',
            'description': 'Veterinario registrado en el sistema',
            'timestamp': datetime.now() - timedelta(hours=2)
        },
        {
            'icon': 'file-medical',
            'title': 'Protocolo completado',
            'description': 'Reporte finalizado y enviado',
            'timestamp': datetime.now() - timedelta(hours=4)
        },
        {
            'icon': 'cog',
            'title': 'Configuración actualizada',
            'description': 'Parámetros del sistema modificados',
            'timestamp': datetime.now() - timedelta(hours=6)
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
```

### 2. URL Configuration
```python
# pages/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/veterinarian/", views.veterinarian_dashboard, name="dashboard_veterinarian"),
    path("dashboard/lab-staff/", views.lab_staff_dashboard, name="dashboard_lab_staff"),
    path("dashboard/histopathologist/", views.histopathologist_dashboard, name="dashboard_histopathologist"),
    path("dashboard/admin/", views.admin_dashboard, name="dashboard_admin"),
]
```

### 3. CSS Styling
```css
/* static/css/dashboard.css */
.dashboard-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.welcome-section {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
}

.welcome-section h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

.quick-actions {
    margin-bottom: 3rem;
}

.quick-actions h2 {
    margin-bottom: 1.5rem;
    color: #333;
}

.action-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

.action-card {
    display: block;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    text-decoration: none;
    color: inherit;
    transition: transform 0.2s, box-shadow 0.2s;
}

.action-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.action-card.primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.action-card i {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    display: block;
}

.action-card h3 {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.stat-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.stat-card.urgent {
    border-left: 4px solid #e74c3c;
}

.stat-card h3 {
    font-size: 1rem;
    color: #666;
    margin-bottom: 1rem;
}

.stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: #333;
    margin-bottom: 0.5rem;
}

.feature-discovery {
    margin-bottom: 3rem;
}

.feature-discovery h2 {
    margin-bottom: 1.5rem;
    color: #333;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.feature-card i {
    font-size: 3rem;
    color: #667eea;
    margin-bottom: 1rem;
}

.feature-card h3 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: #333;
}

.feature-card p {
    color: #666;
    margin-bottom: 1.5rem;
}

.feature-link {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: #667eea;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    transition: background 0.2s;
}

.feature-link:hover {
    background: #5a6fd8;
}

.recent-activity, .processing-queue, .pending-reports {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
}

.activity-list, .queue-list, .reports-list {
    space-y: 1rem;
}

.activity-item, .queue-item, .report-item {
    display: flex;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #eee;
}

.activity-item:last-child, .queue-item:last-child, .report-item:last-child {
    border-bottom: none;
}

.activity-icon, .queue-info, .report-info {
    margin-right: 1rem;
}

.activity-icon i {
    font-size: 1.5rem;
    color: #667eea;
}

.activity-content h4, .queue-info h4, .report-info h4 {
    margin-bottom: 0.25rem;
    color: #333;
}

.activity-content p, .queue-info p, .report-info p {
    color: #666;
    font-size: 0.9rem;
}

.activity-time {
    color: #999;
    font-size: 0.8rem;
}

.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
}

.status-badge.submitted { background: #f39c12; color: white; }
.status-badge.received { background: #3498db; color: white; }
.status-badge.processing { background: #9b59b6; color: white; }
.status-badge.ready_for_report { background: #e67e22; color: white; }
.status-badge.completed { background: #27ae60; color: white; }

.system-health {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
}

.health-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
}

.health-card {
    text-align: center;
    padding: 1.5rem;
}

.health-card i {
    font-size: 2rem;
    color: #667eea;
    margin-bottom: 1rem;
}

.health-status {
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
}

.health-status.healthy {
    background: #d4edda;
    color: #155724;
}

.health-status.warning {
    background: #fff3cd;
    color: #856404;
}

.health-status.error {
    background: #f8d7da;
    color: #721c24;
}

/* Responsive Design */
@media (max-width: 768px) {
    .dashboard-container {
        padding: 1rem;
    }
    
    .action-cards, .stats-grid, .feature-grid {
        grid-template-columns: 1fr;
    }
    
    .welcome-section h1 {
        font-size: 2rem;
    }
    
    .activity-item, .queue-item, .report-item {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .activity-icon, .queue-info, .report-info {
        margin-right: 0;
        margin-bottom: 0.5rem;
    }
}
```

## Acceptance Criteria

### ✅ Veterinario Dashboard
- [ ] Welcome section with personalized greeting
- [ ] Quick action cards for common tasks (new protocol, view protocols, profile)
- [ ] Statistics widgets (active protocols, ready reports, monthly count)
- [ ] Recent activity list showing latest protocols
- [ ] Feature discovery grid with available capabilities
- [ ] Responsive design for mobile access

### ✅ Personal de Laboratorio Dashboard
- [ ] Laboratory-focused welcome section
- [ ] Quick actions for reception, processing, and work orders
- [ ] Statistics widgets (pending reception, processing count, daily received)
- [ ] Processing queue showing protocols needing attention
- [ ] Feature discovery for laboratory tools
- [ ] Urgent items highlighted appropriately

### ✅ Histopatólogo Dashboard
- [ ] Clinical-focused welcome section
- [ ] Quick actions for pending reports, history, and digital signature
- [ ] Statistics widgets (pending reports, monthly completed, average time)
- [ ] Pending reports list with priority indicators
- [ ] Feature discovery for diagnostic tools
- [ ] Productivity metrics display

### ✅ Administrador Dashboard
- [ ] Administrative welcome section
- [ ] Quick actions for admin panel, analytics, and user management
- [ ] System health monitoring widgets
- [ ] System-wide statistics overview
- [ ] Recent activity feed
- [ ] Feature discovery for administrative tools

### ✅ Common Features
- [ ] Role-based access control
- [ ] Responsive design for all screen sizes
- [ ] Consistent styling and branding
- [ ] Fast loading times (< 2 seconds)
- [ ] Accessibility compliance
- [ ] Mobile-friendly navigation

### ✅ Integration
- [ ] Seamless integration with existing system modules
- [ ] Proper URL routing and navigation
- [ ] Consistent with existing design patterns
- [ ] No conflicts with existing functionality

## Testing Approach

### Unit Tests
- **Dashboard View Tests**: Test each role-specific dashboard view
- **Statistics Calculation Tests**: Test dashboard statistics accuracy
- **Access Control Tests**: Ensure proper role-based access
- **Template Rendering Tests**: Test dashboard template rendering

### Integration Tests
- **User Flow Tests**: Test complete user workflows from dashboard
- **Navigation Tests**: Test navigation between dashboard and other modules
- **Data Integration Tests**: Test integration with existing models
- **Responsive Tests**: Test dashboard on different screen sizes

### User Acceptance Tests
- **Role-Specific Workflows**: Test each user role's typical workflow
- **Feature Discovery**: Test that users can find and access features
- **Performance Tests**: Test dashboard loading times
- **Usability Tests**: Test intuitive navigation and clear information display

## Technical Considerations

### Performance
- **Database Queries**: Optimize queries for dashboard statistics
- **Caching**: Cache frequently accessed dashboard data
- **Lazy Loading**: Load dashboard components as needed
- **CDN Integration**: Serve static assets via CDN

### Security
- **Role-Based Access**: Ensure proper access control for each dashboard
- **Data Privacy**: Show only relevant data to each user role
- **Input Validation**: Validate all dashboard inputs
- **CSRF Protection**: Ensure all forms are CSRF protected

### Scalability
- **Modular Design**: Design dashboards to be easily extensible
- **Configuration**: Make dashboard layout configurable
- **Performance Monitoring**: Monitor dashboard performance
- **User Feedback**: Collect user feedback for improvements

## Dependencies

- **Step 01**: Authentication & User Management (for user roles)
- **Step 02**: Veterinarian Profiles (for veterinarian data)
- **Step 03**: Protocol Submission (for protocol data)
- **Step 04**: Sample Reception (for reception data)
- **Step 05**: Sample Processing (for processing data)
- **Step 06**: Report Generation (for report data)
- **Step 07**: Work Orders (for work order data)

## Estimated Effort

**Total**: 1 week (5 days)

- **Day 1**: Dashboard views and URL configuration
- **Day 2**: Veterinario and Personal de Laboratorio dashboards
- **Day 3**: Histopatólogo and Administrador dashboards
- **Day 4**: CSS styling and responsive design
- **Day 5**: Testing, integration, and documentation

## Implementation Notes

### File Structure
```
pages/
├── views.py                 # Dashboard views
├── urls.py                  # Dashboard URL configuration
├── templates/
│   └── pages/
│       ├── dashboard_veterinarian.html
│       ├── dashboard_lab_staff.html
│       ├── dashboard_histopathologist.html
│       ├── dashboard_admin.html
│       └── dashboard_default.html
└── static/
    └── css/
        └── dashboard.css    # Dashboard-specific styles
```

### Quick Start Guide

1. **Create Dashboard Views**:
   ```python
   # Add dashboard views to pages/views.py
   # Implement role-specific dashboard functions
   ```

2. **Configure URLs**:
   ```python
   # Add dashboard URLs to pages/urls.py
   # Set up role-based routing
   ```

3. **Create Templates**:
   ```html
   <!-- Create dashboard templates for each role -->
   <!-- Implement responsive design -->
   ```

4. **Add Styling**:
   ```css
   /* Create dashboard.css with responsive design */
   /* Implement consistent branding */
   ```

5. **Test Integration**:
   ```bash
   # Test dashboard functionality
   # Verify role-based access
   # Test responsive design
   ```

### Usage Examples

**Access Dashboard**:
```python
# Users are automatically redirected to their role-specific dashboard
# based on their user.role field
```

**Customize Dashboard**:
```python
# Dashboard content can be customized by modifying the view functions
# and template context data
```

**Add New Features**:
```html
<!-- New features can be added to the feature discovery grid -->
<!-- by updating the dashboard templates -->
```

This comprehensive dashboard system will provide users with a clear, intuitive way to discover and access the features available to them based on their role, significantly improving the user experience and system usability.
