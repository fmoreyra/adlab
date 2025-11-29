# Step 18: Monitoring and Metrics

## Overview

This step implements a comprehensive self-hosted monitoring and metrics system for the laboratory management system. The solution provides centralized logging, searchable log analysis, and domain-specific dashboards for laboratory operations.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django App    │    │   Celery        │    │   PostgreSQL    │
│   (Logs)        │───▶│   (Tasks)       │───▶│   (Metrics)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Loki (Log Aggregation)                      │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Grafana (Dashboards & Visualization)         │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Prometheus (Metrics Collection)              │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Structure

### Recommended: Separate Monitoring Infrastructure Repository

For production deployments and multi-application monitoring, we recommend using a **separate repository** for the monitoring infrastructure. This allows you to:

- **Reuse the monitoring stack** across multiple applications
- **Centralize infrastructure management** in one place
- **Scale efficiently** by monitoring multiple apps from a single stack
- **Maintain separation** between infrastructure and application code

### Architecture

```
monitoring-infrastructure/          # Separate repository (shared)
├── docker-compose.yml              # Core stack (Loki, Prometheus, Grafana)
├── loki-config.yaml                # Loki base configuration
├── prometheus-base.yml            # Prometheus base configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   └── dashboards/
│   └── dashboards/                # Shared/common dashboards
├── rules/                          # Base alert rules
├── setup.sh                       # Setup script
├── README.md                       # Infrastructure documentation
└── .env.example                    # Environment template

laboratory-system/                  # Application repository (this repo)
├── monitoring/                     # App-specific configurations only
│   ├── prometheus-scrape.yml       # Scrape config for THIS app
│   ├── promtail-app.yml           # Log collection config for THIS app
│   ├── grafana-dashboards/        # App-specific dashboards
│   └── README.md                  # Connection instructions
└── src/config/settings.py         # Django metrics integration
```

### What Goes Where

#### **Monitoring Infrastructure Repository** (Shared)
- Core Docker Compose configuration
- Loki base configuration
- Prometheus base configuration
- Grafana base setup and provisioning
- Node Exporter and cAdvisor services
- Base/global alert rules
- Common/shared dashboards
- Infrastructure documentation

#### **Application Repository** (This Repository)
- Prometheus scrape configuration for this specific app
- Promtail configuration for this app's logs
- App-specific Grafana dashboards
- Django metrics integration code (`django-prometheus` setup)
- App-specific alert rules
- Connection documentation

### Implementation Strategy

#### Step 1: Create Monitoring Infrastructure Repository

```bash
# Create new repository
mkdir monitoring-infrastructure
cd monitoring-infrastructure
git init

# Structure
mkdir -p grafana/provisioning/{datasources,dashboards}
mkdir -p grafana/dashboards
mkdir -p rules
mkdir -p apps  # For app-specific configs (optional)

# Copy base configurations from this step
# - docker-compose.yml
# - loki-config.yaml
# - prometheus-base.yml
# - grafana provisioning configs
```

#### Step 2: Configure Monitoring Infrastructure for Multi-App

Update `prometheus-base.yml` to support multiple apps:

```yaml
# monitoring-infrastructure/prometheus-base.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"
  - "apps/*/rules/*.yml"  # Load app-specific rules

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # cAdvisor
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # Load app-specific scrape configs
  # These will be mounted from application repositories
  - job_name: 'laboratory-system'
    file_sd_configs:
      - files:
          - '/etc/prometheus/configs/laboratory-system/scrape.yml'
        refresh_interval: 30s
```

Update Docker Compose to mount app configs:

```yaml
# monitoring-infrastructure/docker-compose.yml
services:
  prometheus:
    volumes:
      - ./prometheus-base.yml:/etc/prometheus/prometheus.yml
      - ./rules:/etc/prometheus/rules
      - prometheus-configs:/etc/prometheus/configs  # Mount point for app configs
      - prometheus-data:/prometheus
    # ... rest of config

  promtail:
    volumes:
      - ./promtail-base.yml:/etc/promtail/config.yml
      - promtail-configs:/etc/promtail/configs  # Mount point for app configs
      # ... rest of config
```

#### Step 3: Add App-Specific Configs to Application Repository

Create `monitoring/` directory in this repository:

```bash
# In laboratory-system repository
mkdir -p monitoring/grafana-dashboards
```

**`monitoring/prometheus-scrape.yml`**:
```yaml
# Prometheus scrape configuration for Laboratory System
# This file gets mounted into the monitoring infrastructure's Prometheus

- targets:
    - 'host.docker.internal:8000'  # Local development
    # - 'laboratory-system:8000'    # Production (if on same network)
  labels:
    job: 'laboratory-system'
    service: 'laboratory-system'
    environment: 'production'
```

**`monitoring/promtail-app.yml`**:
```yaml
# Promtail configuration for Laboratory System logs
# This file gets mounted into the monitoring infrastructure's Promtail

- job_name: laboratory-system-django
  static_configs:
    - targets:
        - localhost
      labels:
        job: django-app
        service: laboratory-system
        app: laboratory-system
        __path__: /app/logs/django/*.log

- job_name: laboratory-system-celery
  static_configs:
    - targets:
        - localhost
      labels:
        job: celery-worker
        service: laboratory-system
        app: laboratory-system
        __path__: /app/logs/celery/*.log
```

**`monitoring/README.md`**:
```markdown
# Monitoring Integration - Laboratory System

This directory contains application-specific monitoring configurations that connect to the shared monitoring infrastructure.

## Setup

1. **Ensure monitoring infrastructure is running**
   ```bash
   cd /path/to/monitoring-infrastructure
   docker compose up -d
   ```

2. **Mount these configs into monitoring stack**
   - Copy `prometheus-scrape.yml` to monitoring infrastructure's Prometheus configs
   - Copy `promtail-app.yml` to monitoring infrastructure's Promtail configs
   - Or use volume mounts/symlinks

3. **Verify connection**
   - Check Prometheus targets: http://localhost:9090/targets
   - Check Loki logs: http://localhost:3100/ready
   - View dashboards: http://localhost:3000

## Metrics Endpoint

The application exposes metrics at `/metrics` endpoint:
- Development: http://localhost:8000/metrics
- Production: https://yourdomain.com/metrics

## Log Locations

- Django logs: `/app/logs/django/*.log`
- Celery logs: `/app/logs/celery/*.log`

## Custom Dashboards

App-specific dashboards are in `grafana-dashboards/` directory.
Import these into Grafana after connecting to the monitoring infrastructure.
```

### Connection Methods

#### Method 1: Volume Mounts (Recommended for Production)

```bash
# On monitoring server
# Clone both repositories
git clone <monitoring-infrastructure-repo> /opt/monitoring
git clone <laboratory-system-repo> /opt/apps/laboratory-system

# Mount app configs via docker-compose
# Update monitoring-infrastructure/docker-compose.yml:
volumes:
  - /opt/apps/laboratory-system/monitoring/prometheus-scrape.yml:/etc/prometheus/configs/laboratory-system/scrape.yml
  - /opt/apps/laboratory-system/monitoring/promtail-app.yml:/etc/promtail/configs/laboratory-system/config.yml
```

#### Method 2: Git Submodules (Good for Versioning)

```bash
# In monitoring-infrastructure repository
git submodule add <laboratory-system-repo> apps/laboratory-system

# Reference configs from submodule
volumes:
  - ./apps/laboratory-system/monitoring/prometheus-scrape.yml:/etc/prometheus/configs/laboratory-system/scrape.yml
```

#### Method 3: Config Management (Advanced)

Use a configuration management tool (Ansible, Terraform, etc.) to:
- Pull configs from application repositories
- Deploy to monitoring infrastructure
- Manage versions and updates

### Versioning Strategy

#### Monitoring Infrastructure
- **Versioning**: Semantic versioning (`v1.0.0`, `v1.1.0`)
- **Changes**: Stack updates, new features, infrastructure improvements
- **Releases**: Tagged releases for stability

#### Application Configs
- **Versioning**: Tied to application version
- **Changes**: App-specific metrics, logs, dashboards
- **Updates**: Updated with application deployments

### Benefits of This Structure

1. **Reusability**: One monitoring stack for multiple applications
2. **Maintainability**: Infrastructure changes don't affect app code
3. **Scalability**: Easy to add new applications
4. **Cost Efficiency**: Shared resources across all apps
5. **Separation of Concerns**: Infrastructure vs application code
6. **Centralized View**: Single Grafana instance for all apps

### Migration Path

If you start with everything in one repository:

1. **Phase 1**: Keep everything in `monitoring/` directory (for initial setup/testing)
2. **Phase 2**: Extract infrastructure to separate repo when ready
3. **Phase 3**: Keep only app-specific configs in application repo

### Quick Start for Separate Repo Setup

```bash
# 1. Create monitoring infrastructure repo
git init monitoring-infrastructure
cd monitoring-infrastructure
# Copy docker-compose.yml, base configs from this step

# 2. In application repo, create app-specific configs
mkdir -p monitoring
# Create prometheus-scrape.yml, promtail-app.yml, README.md

# 3. Connect them (choose one method above)
# 4. Start monitoring stack
cd monitoring-infrastructure
docker compose up -d

# 5. Verify connection
curl http://localhost:9090/targets
curl http://localhost:3100/ready
```

## Components

### 1. **Loki** - Log Aggregation
- Self-hosted log aggregation system
- Efficient log storage and indexing
- Powerful query language (LogQL)
- Integrates seamlessly with Grafana

### 2. **Prometheus** - Metrics Collection
- Time-series metrics database
- Pull-based metrics collection
- Built-in alerting capabilities
- Extensive ecosystem

### 3. **Grafana** - Visualization & Dashboards
- Rich dashboard creation
- Multiple data source support
- Alerting and notifications
- User management and access control

### 4. **Promtail** - Log Shipping
- Lightweight log shipper
- Automatic service discovery
- Label extraction and parsing
- Ships logs to Loki

## Implementation Plan

> **Note**: This implementation plan assumes you're setting up the monitoring infrastructure in a **separate repository** (recommended). If you prefer to start with everything in the application repository, you can adapt these instructions by creating a `monitoring/` directory in this repository instead.

### Phase 1: Infrastructure Setup (2-3 hours)

#### 1.1 Docker Compose Configuration

Create `monitoring-infrastructure/docker-compose.yml` (or `monitoring/docker-compose.yml` if keeping in app repo):

```yaml
version: '3.8'

services:
  # Loki - Log Aggregation
  loki:
    image: grafana/loki:2.9.0
    container_name: loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki
    networks:
      - monitoring
    restart: unless-stopped

  # Promtail - Log Shipper
  promtail:
    image: grafana/promtail:2.9.0
    container_name: promtail
    volumes:
      - ./promtail-config.yaml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./logs:/app/logs:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring
    restart: unless-stopped
    depends_on:
      - loki

  # Prometheus - Metrics Collection
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./rules:/etc/prometheus/rules
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    networks:
      - monitoring
    restart: unless-stopped

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:10.0.0
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - monitoring
    restart: unless-stopped
    depends_on:
      - loki
      - prometheus

  # Node Exporter - System Metrics
  node-exporter:
    image: prom/node-exporter:v1.6.0
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring
    restart: unless-stopped

  # cAdvisor - Container Metrics
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg
    networks:
      - monitoring
    restart: unless-stopped

volumes:
  loki-data:
  prometheus-data:
  grafana-data:

networks:
  monitoring:
    driver: bridge
```

#### 1.2 Loki Configuration

Create `monitoring/loki-config.yaml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_scheduler:
  max_outstanding_requests_per_tenant: 2048

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  max_cache_freshness_per_query: 10m
  split_queries_by_interval: 15m
  max_query_parallelism: 32
  max_streams_per_user: 0
  max_line_size: 256000

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

compactor:
  working_directory: /loki
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

analytics:
  reporting_enabled: false
```

#### 1.3 Promtail Configuration

**For Monitoring Infrastructure Repository**: Create `monitoring-infrastructure/promtail-base.yml` (base configuration).

**For Application Repository**: Create `monitoring/promtail-app.yml` (app-specific log collection config).

**Base configuration** (`monitoring-infrastructure/promtail-base.yml`):

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Django Application Logs
  - job_name: django-app
    static_configs:
      - targets:
          - localhost
        labels:
          job: django-app
          service: laboratory-system
          __path__: /app/logs/django/*.log

  # Celery Worker Logs
  - job_name: celery-worker
    static_configs:
      - targets:
          - localhost
        labels:
          job: celery-worker
          service: laboratory-system
          __path__: /app/logs/celery/*.log

  # Nginx Access Logs
  - job_name: nginx-access
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx-access
          service: laboratory-system
          __path__: /var/log/nginx/access.log

  # Nginx Error Logs
  - job_name: nginx-error
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx-error
          service: laboratory-system
          __path__: /var/log/nginx/error.log

  # System Logs
  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          service: system
          __path__: /var/log/syslog

  # Docker Container Logs
  - job_name: docker-containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/?(.*)'
        target_label: 'container_name'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'logstream'
      - source_labels: ['__meta_docker_container_label_logging']
        target_label: 'logging'
```

#### 1.4 Prometheus Configuration

**For Monitoring Infrastructure Repository**: Create `monitoring-infrastructure/prometheus-base.yml` (base configuration).

**For Application Repository**: Create `monitoring/prometheus-scrape.yml` (app-specific scrape config - see Repository Structure section above).

**Base configuration** (`monitoring-infrastructure/prometheus-base.yml`):

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"
  - "apps/*/rules/*.yml"  # Load app-specific rules (if using separate repo structure)

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter - System Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # cAdvisor - Container Metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # App-specific scrape configs will be loaded from application repositories
  # See monitoring/prometheus-scrape.yml in application repo
  # Or use file_sd_configs to dynamically load from mounted configs:
  # - job_name: 'laboratory-system'
  #   file_sd_configs:
  #     - files:
  #         - '/etc/prometheus/configs/laboratory-system/scrape.yml'
  #       refresh_interval: 30s

  # PostgreSQL Metrics (if using postgres_exporter)
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s
```

**Note**: The Django and Celery application metrics will be configured in the application repository's `monitoring/prometheus-scrape.yml` file (see Repository Structure section above).

### Phase 2: Django Application Integration (1-2 hours)

#### 2.1 Install Required Packages

Add to `requirements.txt`:

```txt
# Monitoring and Metrics
django-prometheus==2.3.1
django-extensions==3.2.3
celery[redis]==5.3.0
flower==2.0.1
```

#### 2.2 Django Settings Configuration

Add to `src/config/settings.py`:

```python
# Monitoring and Metrics
INSTALLED_APPS = [
    # ... existing apps ...
    'django_prometheus',
    'django_extensions',
]

# Prometheus Metrics
PROMETHEUS_EXPORT_MIGRATIONS = False

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django', 'django.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'celery', 'celery.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_django', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'protocols': {
            'handlers': ['file_django', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['file_celery', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery.task': {
            'handlers': ['file_celery', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory
import os
logs_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(os.path.join(logs_dir, 'django'), exist_ok=True)
os.makedirs(os.path.join(logs_dir, 'celery'), exist_ok=True)
```

#### 2.3 URL Configuration

Add to `src/config/urls.py`:

```python
from django_prometheus import exports

urlpatterns = [
    # ... existing patterns ...
    path('metrics/', exports.ExportToDjangoView, name='prometheus-django-metrics'),
]
```

#### 2.4 Custom Metrics

Create `src/protocols/metrics.py`:

```python
"""
Custom metrics for laboratory system monitoring.
"""

from django_prometheus.models import MetricsModelMixin
from django.db import models
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# Protocol Metrics
protocol_created_total = Counter(
    'protocols_created_total',
    'Total number of protocols created',
    ['species', 'analysis_type']
)

protocol_status_changes_total = Counter(
    'protocol_status_changes_total',
    'Total number of protocol status changes',
    ['from_status', 'to_status']
)

# Report Metrics
reports_finalized_total = Counter(
    'reports_finalized_total',
    'Total number of reports finalized',
    ['histopathologist']
)

report_generation_duration = Histogram(
    'report_generation_duration_seconds',
    'Time spent generating reports',
    ['report_type']
)

# Work Order Metrics
work_orders_created_total = Counter(
    'work_orders_created_total',
    'Total number of work orders created',
    ['veterinarian']
)

work_order_pdf_generation_duration = Histogram(
    'work_order_pdf_generation_duration_seconds',
    'Time spent generating work order PDFs'
)

# Email Metrics
emails_sent_total = Counter(
    'emails_sent_total',
    'Total number of emails sent',
    ['email_type', 'status']
)

email_sending_duration = Histogram(
    'email_sending_duration_seconds',
    'Time spent sending emails',
    ['email_type']
)

# System Metrics
active_users_gauge = Gauge(
    'active_users_current',
    'Current number of active users'
)

database_connections_gauge = Gauge(
    'database_connections_current',
    'Current number of database connections'
)

# Celery Task Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status']
)

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Time spent executing Celery tasks',
    ['task_name']
)

# Custom Model Mixin for Metrics
class MetricsMixin(MetricsModelMixin):
    """Mixin to add metrics to Django models."""
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Add custom metrics here if needed
        pass
```

#### 2.5 Model Integration

Update models to include metrics:

```python
# In src/protocols/models.py
from .metrics import MetricsMixin, protocol_created_total, protocol_status_changes_total

class Protocol(MetricsMixin, models.Model):
    # ... existing fields ...
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = Protocol.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Protocol.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Record metrics
        if is_new:
            protocol_created_total.labels(
                species=self.species,
                analysis_type=self.analysis_type
            ).inc()
        
        if old_status and old_status != self.status:
            protocol_status_changes_total.labels(
                from_status=old_status,
                to_status=self.status
            ).inc()
```

#### 2.6 View Metrics Decorator

Create `src/protocols/decorators.py`:

```python
"""
Custom decorators for metrics collection.
"""

from functools import wraps
from django_prometheus import metrics
import time

def track_view_metrics(view_name):
    """Decorator to track view metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            
            try:
                response = func(request, *args, **kwargs)
                metrics.VIEWS_TOTAL.labels(
                    method=request.method,
                    view=view_name,
                    status_code=response.status_code
                ).inc()
                return response
            except Exception as e:
                metrics.VIEWS_TOTAL.labels(
                    method=request.method,
                    view=view_name,
                    status_code=500
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                metrics.VIEW_DURATION_SECONDS.labels(
                    method=request.method,
                    view=view_name
                ).observe(duration)
        
        return wrapper
    return decorator

def track_celery_task_metrics(task_name):
    """Decorator to track Celery task metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                celery_tasks_total.labels(
                    task_name=task_name,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                celery_tasks_total.labels(
                    task_name=task_name,
                    status='failure'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                celery_task_duration.labels(
                    task_name=task_name
                ).observe(duration)
        
        return wrapper
    return decorator
```

### Phase 3: Grafana Dashboards (2-3 hours)

#### 3.1 Dashboard Provisioning

Create `monitoring/grafana/provisioning/dashboards/dashboard.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'laboratory-system'
    orgId: 1
    folder: 'Laboratory System'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

#### 3.2 Data Source Provisioning

Create `monitoring/grafana/provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
```

#### 3.3 Laboratory System Dashboard

Create `monitoring/grafana/dashboards/laboratory-system.json`:

```json
{
  "dashboard": {
    "id": null,
    "title": "Laboratory System Overview",
    "tags": ["laboratory", "django", "celery"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Protocols Created Today",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(protocols_created_total[24h]))",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 10},
                {"color": "red", "value": 50}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Reports Finalized Today",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(increase(reports_finalized_total[24h]))",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 5},
                {"color": "red", "value": 20}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users_current",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 10},
                {"color": "red", "value": 50}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
      },
      {
        "id": 4,
        "title": "Email Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(emails_sent_total{status=\"success\"}[5m])) / sum(rate(emails_sent_total[5m])) * 100",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 80},
                {"color": "green", "value": 95}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
      },
      {
        "id": 5,
        "title": "Protocol Status Changes",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(protocol_status_changes_total[5m])) by (to_status)",
            "refId": "A",
            "legendFormat": "To {{to_status}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "drawStyle": "line",
              "lineInterpolation": "linear",
              "barAlignment": 0,
              "lineWidth": 1,
              "fillOpacity": 10,
              "gradientMode": "none",
              "spanNulls": false,
              "insertNulls": false,
              "showPoints": "never",
              "pointSize": 5,
              "stacking": {
                "mode": "none",
                "group": "A"
              },
              "axisPlacement": "auto",
              "axisLabel": "",
              "scaleDistribution": {
                "type": "linear"
              },
              "hideFrom": {
                "legend": false,
                "tooltip": false,
                "vis": false
              },
              "thresholdsStyle": {
                "mode": "off"
              }
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 6,
        "title": "Report Generation Duration",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(report_generation_duration_seconds_bucket[5m]))",
            "refId": "A",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(report_generation_duration_seconds_bucket[5m]))",
            "refId": "B",
            "legendFormat": "50th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 7,
        "title": "Celery Task Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(celery_tasks_total) by (status)",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 16}
      },
      {
        "id": 8,
        "title": "System Resources",
        "type": "timeseries",
        "targets": [
          {
            "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "refId": "A",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "100 - ((node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100)",
            "refId": "B",
            "legendFormat": "Memory Usage %"
          }
        ],
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 16}
      },
      {
        "id": 9,
        "title": "Database Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "database_connections_current",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 10},
                {"color": "red", "value": 20}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 16}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

#### 3.4 Log Analysis Dashboard

Create `monitoring/grafana/dashboards/log-analysis.json`:

```json
{
  "dashboard": {
    "id": null,
    "title": "Log Analysis",
    "tags": ["logs", "loki"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Error Logs",
        "type": "logs",
        "targets": [
          {
            "expr": "{job=\"django-app\"} |= \"ERROR\"",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 12, "w": 24, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Celery Task Logs",
        "type": "logs",
        "targets": [
          {
            "expr": "{job=\"celery-worker\"}",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 12, "w": 24, "x": 0, "y": 12}
      },
      {
        "id": 3,
        "title": "Nginx Access Logs",
        "type": "logs",
        "targets": [
          {
            "expr": "{job=\"nginx-access\"}",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 12, "w": 24, "x": 0, "y": 24}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### Phase 4: Alerting Rules (1 hour)

#### 4.1 Prometheus Alert Rules

Create `monitoring/rules/laboratory-system.yml`:

```yaml
groups:
  - name: laboratory-system
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: sum(rate(django_http_requests_total{status=~"5.."}[5m])) / sum(rate(django_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High Response Time
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # Celery Task Failures
      - alert: CeleryTaskFailures
        expr: sum(rate(celery_tasks_total{status="failure"}[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Celery task failure rate"
          description: "Celery task failure rate is {{ $value }} failures per second"

      # Email Delivery Failures
      - alert: EmailDeliveryFailures
        expr: sum(rate(emails_sent_total{status="failure"}[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High email delivery failure rate"
          description: "Email delivery failure rate is {{ $value }} failures per second"

      # Database Connection Issues
      - alert: DatabaseConnectionsHigh
        expr: database_connections_current > 15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connection count"
          description: "Database connections: {{ $value }}"

      # Disk Space Low
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk space is {{ $value | humanizePercentage }} full"

      # Memory Usage High
      - alert: MemoryUsageHigh
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
```

### Phase 5: Deployment and Configuration (1 hour)

#### 5.1 Setup Script

Create `monitoring/setup.sh`:

```bash
#!/bin/bash

# Create necessary directories
mkdir -p logs/django
mkdir -p logs/celery
mkdir -p grafana/dashboards
mkdir -p grafana/provisioning/dashboards
mkdir -p grafana/provisioning/datasources
mkdir -p rules

# Set permissions
chmod 755 logs/django
chmod 755 logs/celery
chmod 755 grafana/dashboards

# Start monitoring stack
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check service health
echo "Checking service health..."
curl -f http://localhost:3000/api/health || echo "Grafana not ready"
curl -f http://localhost:9090/-/healthy || echo "Prometheus not ready"
curl -f http://localhost:3100/ready || echo "Loki not ready"

echo "Monitoring stack setup complete!"
echo "Access Grafana at: http://localhost:3000 (admin/admin123)"
echo "Access Prometheus at: http://localhost:9090"
echo "Access Loki at: http://localhost:3100"
```

#### 5.2 Nginx Configuration

Add to your main nginx configuration:

```nginx
# Monitoring endpoints
location /monitoring/ {
    proxy_pass http://localhost:3000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /prometheus/ {
    proxy_pass http://localhost:9090/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

#### 5.3 Environment Variables

Add to your `.env` file:

```bash
# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password
PROMETHEUS_RETENTION=30d
LOKI_RETENTION=30d
```

## Domain-Specific Metrics Implementation

### **Complete Metrics List**

The following metrics should be implemented to provide comprehensive monitoring of the laboratory system:

#### **Protocol Management Metrics**
```python
# Protocol Creation and Processing
protocols_created_total = Counter('protocols_created_total', 'Total protocols created', ['species', 'analysis_type', 'veterinarian'])
protocols_submitted_total = Counter('protocols_submitted_total', 'Total protocols submitted', ['species', 'analysis_type'])
protocols_received_total = Counter('protocols_received_total', 'Total protocols received', ['received_by', 'sample_condition'])
protocols_processing_duration = Histogram('protocols_processing_duration_seconds', 'Time from submission to completion', ['species', 'analysis_type'])

# Protocol Status Tracking
protocol_status_changes_total = Counter('protocol_status_changes_total', 'Protocol status changes', ['from_status', 'to_status', 'changed_by'])
protocols_by_status_gauge = Gauge('protocols_by_status_current', 'Current protocols by status', ['status'])
protocol_age_days = Histogram('protocol_age_days', 'Age of protocols in current status', ['status'])

# Sample Processing
samples_processed_total = Counter('samples_processed_total', 'Total samples processed', ['sample_type', 'processing_stage'])
sample_processing_duration = Histogram('sample_processing_duration_seconds', 'Sample processing time', ['sample_type', 'stage'])
sample_quality_issues_total = Counter('sample_quality_issues_total', 'Sample quality issues', ['issue_type', 'severity'])
```

#### **Report Generation Metrics**
```python
# Report Creation and Management
reports_created_total = Counter('reports_created_total', 'Total reports created', ['histopathologist', 'report_type'])
reports_finalized_total = Counter('reports_finalized_total', 'Total reports finalized', ['histopathologist', 'complexity'])
reports_sent_total = Counter('reports_sent_total', 'Total reports sent', ['histopathologist', 'delivery_method'])

# Report Performance
report_generation_duration = Histogram('report_generation_duration_seconds', 'Report generation time', ['report_type', 'cassette_count'])
report_pdf_generation_duration = Histogram('report_pdf_generation_duration_seconds', 'PDF generation time', ['report_size'])
report_revision_count = Histogram('report_revision_count', 'Number of revisions per report', ['histopathologist'])

# Report Quality
report_accuracy_score = Histogram('report_accuracy_score', 'Report accuracy scores', ['histopathologist'])
report_feedback_rating = Histogram('report_feedback_rating', 'Client feedback ratings', ['histopathologist'])
```

#### **Work Order Metrics**
```python
# Work Order Processing
work_orders_created_total = Counter('work_orders_created_total', 'Total work orders created', ['veterinarian', 'order_type'])
work_orders_completed_total = Counter('work_orders_completed_total', 'Total work orders completed', ['veterinarian'])
work_order_processing_duration = Histogram('work_order_processing_duration_seconds', 'Work order processing time', ['order_type', 'service_count'])

# Financial Metrics
work_order_revenue_total = Counter('work_order_revenue_total', 'Total work order revenue', ['veterinarian', 'service_type'])
work_order_payment_status = Gauge('work_order_payment_status_current', 'Work orders by payment status', ['payment_status'])
average_order_value = Histogram('work_order_average_value', 'Average work order value', ['veterinarian', 'time_period'])
```

#### **User Activity Metrics**
```python
# User Engagement
user_sessions_total = Counter('user_sessions_total', 'Total user sessions', ['user_type', 'login_method'])
user_actions_total = Counter('user_actions_total', 'Total user actions', ['user_type', 'action_type', 'module'])
active_users_gauge = Gauge('active_users_current', 'Currently active users', ['user_type'])
user_session_duration = Histogram('user_session_duration_seconds', 'User session duration', ['user_type'])

# User Performance
user_productivity_score = Histogram('user_productivity_score', 'User productivity metrics', ['user_type', 'role'])
user_error_rate = Histogram('user_error_rate', 'User error rates', ['user_type', 'action_type'])
user_satisfaction_score = Histogram('user_satisfaction_score', 'User satisfaction ratings', ['user_type'])
```

#### **Email and Communication Metrics**
```python
# Email Performance
emails_sent_total = Counter('emails_sent_total', 'Total emails sent', ['email_type', 'status', 'recipient_type'])
email_delivery_duration = Histogram('email_delivery_duration_seconds', 'Email delivery time', ['email_type', 'size'])
email_bounce_rate = Histogram('email_bounce_rate', 'Email bounce rates', ['email_type', 'time_period'])
email_open_rate = Histogram('email_open_rate', 'Email open rates', ['email_type', 'time_period'])

# Notification Effectiveness
notifications_sent_total = Counter('notifications_sent_total', 'Total notifications sent', ['notification_type', 'channel'])
notification_response_rate = Histogram('notification_response_rate', 'Notification response rates', ['notification_type'])
```

#### **System Performance Metrics**
```python
# Application Performance
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint', 'status'])
request_rate = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
database_query_duration = Histogram('database_query_duration_seconds', 'Database query duration', ['query_type', 'table'])
database_connections_gauge = Gauge('database_connections_current', 'Current database connections', ['state'])

# File Operations
file_uploads_total = Counter('file_uploads_total', 'Total file uploads', ['file_type', 'size_category'])
file_downloads_total = Counter('file_downloads_total', 'Total file downloads', ['file_type'])
file_storage_usage = Gauge('file_storage_usage_bytes', 'File storage usage', ['storage_type'])
```

#### **Business Intelligence Metrics**
```python
# Laboratory Operations
daily_throughput = Gauge('daily_throughput_protocols', 'Daily protocol throughput', ['date'])
monthly_revenue = Gauge('monthly_revenue_total', 'Monthly revenue', ['month', 'year'])
client_retention_rate = Histogram('client_retention_rate', 'Client retention rates', ['time_period'])
average_turnaround_time = Histogram('average_turnaround_time_days', 'Average turnaround time', ['analysis_type', 'time_period'])

# Quality Metrics
quality_control_passed = Counter('quality_control_passed_total', 'Quality control checks passed', ['check_type', 'result'])
rework_required_total = Counter('rework_required_total', 'Total rework required', ['work_type', 'reason'])
client_complaints_total = Counter('client_complaints_total', 'Total client complaints', ['complaint_type', 'severity'])
```

#### **Security and Compliance Metrics**
```python
# Security Events
security_events_total = Counter('security_events_total', 'Total security events', ['event_type', 'severity'])
failed_login_attempts = Counter('failed_login_attempts_total', 'Failed login attempts', ['user_type', 'ip_address'])
password_resets_total = Counter('password_resets_total', 'Total password resets', ['user_type', 'method'])

# Compliance
data_access_audit_total = Counter('data_access_audit_total', 'Data access audit events', ['user_type', 'data_type', 'action'])
compliance_violations_total = Counter('compliance_violations_total', 'Compliance violations', ['violation_type', 'severity'])
```

#### **Resource Utilization Metrics**
```python
# System Resources
cpu_usage_percent = Gauge('cpu_usage_percent', 'CPU usage percentage', ['core'])
memory_usage_bytes = Gauge('memory_usage_bytes', 'Memory usage in bytes', ['type'])
disk_usage_bytes = Gauge('disk_usage_bytes', 'Disk usage in bytes', ['mountpoint', 'filesystem'])
network_traffic_bytes = Counter('network_traffic_bytes_total', 'Network traffic', ['interface', 'direction'])

# Application Resources
celery_queue_length = Gauge('celery_queue_length', 'Celery queue length', ['queue_name'])
celery_worker_count = Gauge('celery_worker_count', 'Active Celery workers', ['worker_type'])
cache_hit_rate = Histogram('cache_hit_rate', 'Cache hit rates', ['cache_type'])
```

### **Implementation Priority**

#### **Phase 1: Critical Business Metrics (Week 1)**
- Protocol creation and status tracking
- Report generation performance
- Work order processing
- Basic system performance

#### **Phase 2: User Experience Metrics (Week 2)**
- User activity and engagement
- Email delivery performance
- File operation metrics
- Error tracking

#### **Phase 3: Business Intelligence (Week 3)**
- Revenue and financial metrics
- Quality control metrics
- Client satisfaction tracking
- Operational efficiency

#### **Phase 4: Advanced Analytics (Week 4)**
- Security and compliance
- Resource utilization
- Predictive analytics
- Custom business metrics

### **Metric Naming Conventions**

```python
# Format: {domain}_{entity}_{metric_type}_{unit}
# Examples:
protocols_created_total
reports_generation_duration_seconds
work_orders_revenue_total
users_active_current
emails_delivery_duration_seconds
```

### **Label Guidelines**

```python
# Use consistent label names across metrics
# Common labels:
- user_type: ['veterinarian', 'histopathologist', 'staff', 'admin']
- analysis_type: ['cytology', 'histopathology']
- species: ['canine', 'feline', 'equine', 'bovine', 'other']
- status: ['draft', 'submitted', 'received', 'processing', 'completed']
- severity: ['low', 'medium', 'high', 'critical']
```

## Usage Guide

### 1. **Starting the Monitoring Stack**

**If using separate repository** (recommended):
```bash
cd monitoring-infrastructure
chmod +x setup.sh
./setup.sh
```

**If keeping everything in application repository**:
```bash
cd monitoring
chmod +x setup.sh
./setup.sh
```

### 2. **Accessing Dashboards**

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### 3. **Log Search Examples**

#### Search for errors in Django logs:
```logql
{job="django-app"} |= "ERROR"
```

#### Search for specific protocol operations:
```logql
{job="django-app"} |= "protocol" |= "created"
```

#### Search for Celery task failures:
```logql
{job="celery-worker"} |= "ERROR" |= "task"
```

#### Search for slow database queries:
```logql
{job="django-app"} |= "slow query" | json | duration > 1000
```

### 4. **Custom Metrics Queries**

#### Protocols by species:
```promql
sum(protocols_created_total) by (species)
```

#### Report generation performance:
```promql
histogram_quantile(0.95, rate(report_generation_duration_seconds_bucket[5m]))
```

#### Email success rate:
```promql
sum(rate(emails_sent_total{status="success"}[5m])) / sum(rate(emails_sent_total[5m])) * 100
```

### 5. **Creating Custom Dashboards**

1. Access Grafana at http://localhost:3000
2. Click "Create" → "Dashboard"
3. Add panels with Prometheus or Loki queries
4. Save dashboard to `/var/lib/grafana/dashboards/`

## Maintenance

### 1. **Log Rotation**

The system automatically rotates logs when they reach 15MB, keeping 10 backup files.

### 2. **Data Retention**

- **Prometheus**: 30 days (configurable)
- **Loki**: 30 days (configurable)
- **Grafana**: Persistent (stored in Docker volume)

### 3. **Backup**

```bash
# Backup Grafana dashboards
docker cp grafana:/var/lib/grafana/dashboards ./backup/

# Backup Prometheus data
docker cp prometheus:/prometheus ./backup/

# Backup Loki data
docker cp loki:/loki ./backup/
```

### 4. **Updates**

```bash
# Update monitoring stack
cd monitoring
docker-compose pull
docker-compose up -d
```

## Security Considerations

### 1. **Access Control**

- Change default Grafana admin password
- Use reverse proxy with authentication
- Restrict network access to monitoring ports

### 2. **Data Privacy**

- Logs may contain sensitive information
- Implement log filtering for PII
- Use secure storage for log data

### 3. **Network Security**

- Use internal Docker networks
- Expose only necessary ports
- Implement firewall rules

## Testing Implementation

### **Service-Based Testing Architecture**

To enable comprehensive testing with mockable calls, we'll implement a service-based architecture that abstracts the monitoring functionality:

#### **1. Metrics Service Interface**

Create `src/protocols/services/metrics_service.py`:

```python
"""
Metrics service interface for testing and production.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricData:
    """Data structure for metric information."""
    name: str
    value: float
    labels: Dict[str, str]
    metric_type: MetricType
    timestamp: Optional[float] = None


class MetricsServiceInterface(ABC):
    """Abstract interface for metrics services."""
    
    @abstractmethod
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1.0) -> None:
        """Increment a counter metric."""
        pass
    
    @abstractmethod
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric value."""
        pass
    
    @abstractmethod
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a histogram metric."""
        pass
    
    @abstractmethod
    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricData]:
        """Get a metric value."""
        pass
    
    @abstractmethod
    def get_metrics_by_prefix(self, prefix: str) -> List[MetricData]:
        """Get all metrics with a given prefix."""
        pass
    
    @abstractmethod
    def clear_metrics(self) -> None:
        """Clear all metrics (for testing)."""
        pass


class PrometheusMetricsService(MetricsServiceInterface):
    """Production Prometheus metrics service."""
    
    def __init__(self):
        from prometheus_client import Counter, Gauge, Histogram, Summary
        self._counters = {}
        self._gauges = {}
        self._histograms = {}
        self._summaries = {}
    
    def _get_or_create_counter(self, name: str, labels: List[str] = None):
        """Get or create a counter metric."""
        if name not in self._counters:
            self._counters[name] = Counter(name, f'{name} metric', labels or [])
        return self._counters[name]
    
    def _get_or_create_gauge(self, name: str, labels: List[str] = None):
        """Get or create a gauge metric."""
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, f'{name} metric', labels or [])
        return self._gauges[name]
    
    def _get_or_create_histogram(self, name: str, labels: List[str] = None):
        """Get or create a histogram metric."""
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, f'{name} metric', labels or [])
        return self._histograms[name]
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1.0) -> None:
        """Increment a counter metric."""
        counter = self._get_or_create_counter(name, list(labels.keys()) if labels else [])
        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric value."""
        gauge = self._get_or_create_gauge(name, list(labels.keys()) if labels else [])
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a histogram metric."""
        histogram = self._get_or_create_histogram(name, list(labels.keys()) if labels else [])
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)
    
    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricData]:
        """Get a metric value (Prometheus doesn't support direct retrieval)."""
        # In production, this would query Prometheus API
        return None
    
    def get_metrics_by_prefix(self, prefix: str) -> List[MetricData]:
        """Get all metrics with a given prefix."""
        # In production, this would query Prometheus API
        return []
    
    def clear_metrics(self) -> None:
        """Clear all metrics (not supported in production)."""
        raise NotImplementedError("Cannot clear metrics in production")


class MockMetricsService(MetricsServiceInterface):
    """Mock metrics service for testing."""
    
    def __init__(self):
        self._metrics: Dict[str, MetricData] = {}
        self._metric_history: List[MetricData] = []
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1.0) -> None:
        """Increment a counter metric."""
        key = self._get_metric_key(name, labels)
        if key in self._metrics:
            self._metrics[key].value += value
        else:
            self._metrics[key] = MetricData(
                name=name,
                value=value,
                labels=labels or {},
                metric_type=MetricType.COUNTER
            )
        self._metric_history.append(self._metrics[key])
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric value."""
        key = self._get_metric_key(name, labels)
        self._metrics[key] = MetricData(
            name=name,
            value=value,
            labels=labels or {},
            metric_type=MetricType.GAUGE
        )
        self._metric_history.append(self._metrics[key])
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a histogram metric."""
        key = self._get_metric_key(name, labels)
        if key in self._metrics:
            # For histograms, we'll store the latest value
            self._metrics[key].value = value
        else:
            self._metrics[key] = MetricData(
                name=name,
                value=value,
                labels=labels or {},
                metric_type=MetricType.HISTOGRAM
            )
        self._metric_history.append(self._metrics[key])
    
    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricData]:
        """Get a metric value."""
        key = self._get_metric_key(name, labels)
        return self._metrics.get(key)
    
    def get_metrics_by_prefix(self, prefix: str) -> List[MetricData]:
        """Get all metrics with a given prefix."""
        return [metric for metric in self._metrics.values() if metric.name.startswith(prefix)]
    
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._metric_history.clear()
    
    def get_metric_history(self, name: str = None) -> List[MetricData]:
        """Get metric history for testing."""
        if name:
            return [metric for metric in self._metric_history if metric.name == name]
        return self._metric_history.copy()
    
    def _get_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Generate a unique key for a metric."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"


# Service factory
def get_metrics_service(use_mock: bool = False) -> MetricsServiceInterface:
    """Factory function to get the appropriate metrics service."""
    if use_mock:
        return MockMetricsService()
    return PrometheusMetricsService()
```

#### **2. Laboratory Metrics Service**

Create `src/protocols/services/laboratory_metrics_service.py`:

```python
"""
Laboratory-specific metrics service implementation.
"""

from typing import Dict, Any, Optional
from .metrics_service import MetricsServiceInterface, get_metrics_service
from django.conf import settings
import time


class LaboratoryMetricsService:
    """Service for laboratory-specific metrics."""
    
    def __init__(self, metrics_service: MetricsServiceInterface = None):
        self.metrics_service = metrics_service or get_metrics_service(
            use_mock=getattr(settings, 'USE_MOCK_METRICS', False)
        )
    
    # Protocol Metrics
    def record_protocol_created(self, species: str, analysis_type: str, veterinarian_id: int) -> None:
        """Record protocol creation."""
        self.metrics_service.increment_counter(
            'protocols_created_total',
            labels={
                'species': species,
                'analysis_type': analysis_type,
                'veterinarian': str(veterinarian_id)
            }
        )
    
    def record_protocol_status_change(self, from_status: str, to_status: str, changed_by_id: int) -> None:
        """Record protocol status change."""
        self.metrics_service.increment_counter(
            'protocol_status_changes_total',
            labels={
                'from_status': from_status,
                'to_status': to_status,
                'changed_by': str(changed_by_id)
            }
        )
    
    def record_protocol_processing_duration(self, species: str, analysis_type: str, duration_seconds: float) -> None:
        """Record protocol processing duration."""
        self.metrics_service.observe_histogram(
            'protocols_processing_duration_seconds',
            duration_seconds,
            labels={
                'species': species,
                'analysis_type': analysis_type
            }
        )
    
    def set_protocols_by_status(self, status: str, count: int) -> None:
        """Set current protocol count by status."""
        self.metrics_service.set_gauge(
            'protocols_by_status_current',
            count,
            labels={'status': status}
        )
    
    # Report Metrics
    def record_report_created(self, histopathologist_id: int, report_type: str) -> None:
        """Record report creation."""
        self.metrics_service.increment_counter(
            'reports_created_total',
            labels={
                'histopathologist': str(histopathologist_id),
                'report_type': report_type
            }
        )
    
    def record_report_finalized(self, histopathologist_id: int, complexity: str) -> None:
        """Record report finalization."""
        self.metrics_service.increment_counter(
            'reports_finalized_total',
            labels={
                'histopathologist': str(histopathologist_id),
                'complexity': complexity
            }
        )
    
    def record_report_generation_duration(self, report_type: str, cassette_count: int, duration_seconds: float) -> None:
        """Record report generation duration."""
        self.metrics_service.observe_histogram(
            'report_generation_duration_seconds',
            duration_seconds,
            labels={
                'report_type': report_type,
                'cassette_count': str(cassette_count)
            }
        )
    
    # Work Order Metrics
    def record_work_order_created(self, veterinarian_id: int, order_type: str) -> None:
        """Record work order creation."""
        self.metrics_service.increment_counter(
            'work_orders_created_total',
            labels={
                'veterinarian': str(veterinarian_id),
                'order_type': order_type
            }
        )
    
    def record_work_order_revenue(self, veterinarian_id: int, service_type: str, amount: float) -> None:
        """Record work order revenue."""
        self.metrics_service.increment_counter(
            'work_order_revenue_total',
            amount,
            labels={
                'veterinarian': str(veterinarian_id),
                'service_type': service_type
            }
        )
    
    # User Activity Metrics
    def record_user_session(self, user_type: str, login_method: str) -> None:
        """Record user session."""
        self.metrics_service.increment_counter(
            'user_sessions_total',
            labels={
                'user_type': user_type,
                'login_method': login_method
            }
        )
    
    def record_user_action(self, user_type: str, action_type: str, module: str) -> None:
        """Record user action."""
        self.metrics_service.increment_counter(
            'user_actions_total',
            labels={
                'user_type': user_type,
                'action_type': action_type,
                'module': module
            }
        )
    
    def set_active_users(self, user_type: str, count: int) -> None:
        """Set active user count."""
        self.metrics_service.set_gauge(
            'active_users_current',
            count,
            labels={'user_type': user_type}
        )
    
    # Email Metrics
    def record_email_sent(self, email_type: str, status: str, recipient_type: str) -> None:
        """Record email sent."""
        self.metrics_service.increment_counter(
            'emails_sent_total',
            labels={
                'email_type': email_type,
                'status': status,
                'recipient_type': recipient_type
            }
        )
    
    def record_email_delivery_duration(self, email_type: str, size_category: str, duration_seconds: float) -> None:
        """Record email delivery duration."""
        self.metrics_service.observe_histogram(
            'email_delivery_duration_seconds',
            duration_seconds,
            labels={
                'email_type': email_type,
                'size_category': size_category
            }
        )
    
    # System Metrics
    def record_request_duration(self, method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
        """Record HTTP request duration."""
        self.metrics_service.observe_histogram(
            'http_request_duration_seconds',
            duration_seconds,
            labels={
                'method': method,
                'endpoint': endpoint,
                'status': str(status_code)
            }
        )
    
    def record_database_query_duration(self, query_type: str, table: str, duration_seconds: float) -> None:
        """Record database query duration."""
        self.metrics_service.observe_histogram(
            'database_query_duration_seconds',
            duration_seconds,
            labels={
                'query_type': query_type,
                'table': table
            }
        )
    
    def set_database_connections(self, state: str, count: int) -> None:
        """Set database connection count."""
        self.metrics_service.set_gauge(
            'database_connections_current',
            count,
            labels={'state': state}
        )
    
    # Utility methods for testing
    def get_protocol_metrics(self) -> Dict[str, Any]:
        """Get all protocol-related metrics."""
        return {
            'created': self.metrics_service.get_metrics_by_prefix('protocols_created_total'),
            'status_changes': self.metrics_service.get_metrics_by_prefix('protocol_status_changes_total'),
            'processing_duration': self.metrics_service.get_metrics_by_prefix('protocols_processing_duration_seconds'),
            'by_status': self.metrics_service.get_metrics_by_prefix('protocols_by_status_current')
        }
    
    def get_report_metrics(self) -> Dict[str, Any]:
        """Get all report-related metrics."""
        return {
            'created': self.metrics_service.get_metrics_by_prefix('reports_created_total'),
            'finalized': self.metrics_service.get_metrics_by_prefix('reports_finalized_total'),
            'generation_duration': self.metrics_service.get_metrics_by_prefix('report_generation_duration_seconds')
        }
    
    def clear_all_metrics(self) -> None:
        """Clear all metrics (for testing)."""
        self.metrics_service.clear_metrics()


# Global service instance
_laboratory_metrics_service = None

def get_laboratory_metrics_service() -> LaboratoryMetricsService:
    """Get the global laboratory metrics service instance."""
    global _laboratory_metrics_service
    if _laboratory_metrics_service is None:
        _laboratory_metrics_service = LaboratoryMetricsService()
    return _laboratory_metrics_service
```

#### **3. Django Settings for Testing**

Add to `src/config/settings.py`:

```python
# Testing configuration
USE_MOCK_METRICS = False

# Override for testing
if 'test' in sys.argv or 'pytest' in sys.modules:
    USE_MOCK_METRICS = True
```

#### **4. Model Integration with Service**

Update `src/protocols/models.py`:

```python
from .services.laboratory_metrics_service import get_laboratory_metrics_service

class Protocol(models.Model):
    # ... existing fields ...
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = Protocol.objects.get(pk=self.pk)
                old_status = old_instance.status
            except Protocol.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Record metrics using service
        metrics_service = get_laboratory_metrics_service()
        
        if is_new:
            metrics_service.record_protocol_created(
                species=self.species,
                analysis_type=self.analysis_type,
                veterinarian_id=self.veterinarian.id
            )
        
        if old_status and old_status != self.status:
            metrics_service.record_protocol_status_change(
                from_status=old_status,
                to_status=self.status,
                changed_by_id=getattr(self, '_changed_by_id', 0)
            )

class Report(models.Model):
    # ... existing fields ...
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            metrics_service = get_laboratory_metrics_service()
            metrics_service.record_report_created(
                histopathologist_id=self.histopathologist.id,
                report_type='standard'
            )
    
    def finalize(self):
        """Mark report as finalized."""
        if self.status != self.Status.DRAFT:
            raise ValueError("Only draft reports can be finalized")
        
        self.status = self.Status.FINALIZED
        self.save(update_fields=["status"])
        
        # Record finalization metric
        metrics_service = get_laboratory_metrics_service()
        metrics_service.record_report_finalized(
            histopathologist_id=self.histopathologist.id,
            complexity='standard'  # Could be calculated based on cassette count
        )
```

#### **5. View Integration with Service**

Create `src/protocols/decorators.py`:

```python
"""
Decorators for metrics collection using the service.
"""

from functools import wraps
from .services.laboratory_metrics_service import get_laboratory_metrics_service
import time

def track_view_metrics(view_name):
    """Decorator to track view metrics using the service."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            metrics_service = get_laboratory_metrics_service()
            
            try:
                response = func(request, *args, **kwargs)
                
                # Record request metrics
                duration = time.time() - start_time
                metrics_service.record_request_duration(
                    method=request.method,
                    endpoint=view_name,
                    status_code=response.status_code,
                    duration_seconds=duration
                )
                
                # Record user action
                user_type = 'staff' if request.user.is_staff else 'veterinarian'
                metrics_service.record_user_action(
                    user_type=user_type,
                    action_type='view_access',
                    module=view_name.split('.')[0] if '.' in view_name else 'unknown'
                )
                
                return response
            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                metrics_service.record_request_duration(
                    method=request.method,
                    endpoint=view_name,
                    status_code=500,
                    duration_seconds=duration
                )
                raise
        
        return wrapper
    return decorator

def track_celery_task_metrics(task_name):
    """Decorator to track Celery task metrics using the service."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            metrics_service = get_laboratory_metrics_service()
            
            try:
                result = func(*args, **kwargs)
                
                # Record task success
                duration = time.time() - start_time
                metrics_service.metrics_service.increment_counter(
                    'celery_tasks_total',
                    labels={'task_name': task_name, 'status': 'success'}
                )
                metrics_service.metrics_service.observe_histogram(
                    'celery_task_duration_seconds',
                    duration,
                    labels={'task_name': task_name}
                )
                
                return result
            except Exception as e:
                # Record task failure
                duration = time.time() - start_time
                metrics_service.metrics_service.increment_counter(
                    'celery_tasks_total',
                    labels={'task_name': task_name, 'status': 'failure'}
                )
                raise
        
        return wrapper
    return decorator
```

#### **6. Comprehensive Test Suite**

Create `src/protocols/tests/test_metrics_service.py`:

```python
"""
Comprehensive test suite for metrics service.
"""

from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from protocols.services.metrics_service import MockMetricsService, PrometheusMetricsService
from protocols.services.laboratory_metrics_service import LaboratoryMetricsService
from protocols.models import Protocol, Report, Veterinarian, Histopathologist
from protocols.tests.factories import ProtocolFactory, ReportFactory


class MockMetricsServiceTest(TestCase):
    """Test the mock metrics service."""
    
    def setUp(self):
        self.mock_service = MockMetricsService()
    
    def test_increment_counter(self):
        """Test counter increment."""
        self.mock_service.increment_counter('test_counter', {'label': 'value'}, 5.0)
        
        metric = self.mock_service.get_metric('test_counter', {'label': 'value'})
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 5.0)
        self.assertEqual(metric.name, 'test_counter')
        self.assertEqual(metric.labels, {'label': 'value'})
    
    def test_set_gauge(self):
        """Test gauge setting."""
        self.mock_service.set_gauge('test_gauge', 42.0, {'label': 'value'})
        
        metric = self.mock_service.get_metric('test_gauge', {'label': 'value'})
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 42.0)
    
    def test_observe_histogram(self):
        """Test histogram observation."""
        self.mock_service.observe_histogram('test_histogram', 1.5, {'label': 'value'})
        
        metric = self.mock_service.get_metric('test_histogram', {'label': 'value'})
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 1.5)
    
    def test_get_metrics_by_prefix(self):
        """Test getting metrics by prefix."""
        self.mock_service.increment_counter('protocols_created_total', {'species': 'canine'})
        self.mock_service.increment_counter('protocols_submitted_total', {'species': 'feline'})
        self.mock_service.increment_counter('reports_created_total', {'type': 'standard'})
        
        protocol_metrics = self.mock_service.get_metrics_by_prefix('protocols_')
        self.assertEqual(len(protocol_metrics), 2)
        
        all_metrics = self.mock_service.get_metrics_by_prefix('')
        self.assertEqual(len(all_metrics), 3)
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        self.mock_service.increment_counter('test_counter')
        self.mock_service.set_gauge('test_gauge', 1.0)
        
        self.mock_service.clear_metrics()
        
        self.assertEqual(len(self.mock_service._metrics), 0)
        self.assertEqual(len(self.mock_service._metric_history), 0)


class LaboratoryMetricsServiceTest(TestCase):
    """Test the laboratory metrics service."""
    
    def setUp(self):
        self.mock_service = MockMetricsService()
        self.lab_service = LaboratoryMetricsService(self.mock_service)
        
        # Create test data
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email='vet@test.com',
                password='testpass'
            ),
            license_number='VET123'
        )
        
        self.histopathologist = Histopathologist.objects.create(
            user=User.objects.create_user(
                email='histo@test.com',
                password='testpass'
            ),
            license_number='HISTO123'
        )
    
    def test_record_protocol_created(self):
        """Test recording protocol creation."""
        self.lab_service.record_protocol_created(
            species='canine',
            analysis_type='cytology',
            veterinarian_id=self.veterinarian.id
        )
        
        metric = self.mock_service.get_metric(
            'protocols_created_total',
            {
                'species': 'canine',
                'analysis_type': 'cytology',
                'veterinarian': str(self.veterinarian.id)
            }
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 1.0)
    
    def test_record_protocol_status_change(self):
        """Test recording protocol status change."""
        self.lab_service.record_protocol_status_change(
            from_status='draft',
            to_status='submitted',
            changed_by_id=self.veterinarian.id
        )
        
        metric = self.mock_service.get_metric(
            'protocol_status_changes_total',
            {
                'from_status': 'draft',
                'to_status': 'submitted',
                'changed_by': str(self.veterinarian.id)
            }
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 1.0)
    
    def test_record_report_generation_duration(self):
        """Test recording report generation duration."""
        self.lab_service.record_report_generation_duration(
            report_type='standard',
            cassette_count=3,
            duration_seconds=5.2
        )
        
        metric = self.mock_service.get_metric(
            'report_generation_duration_seconds',
            {
                'report_type': 'standard',
                'cassette_count': '3'
            }
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 5.2)
    
    def test_get_protocol_metrics(self):
        """Test getting protocol metrics."""
        # Record some metrics
        self.lab_service.record_protocol_created('canine', 'cytology', self.veterinarian.id)
        self.lab_service.record_protocol_status_change('draft', 'submitted', self.veterinarian.id)
        self.lab_service.set_protocols_by_status('submitted', 5)
        
        metrics = self.lab_service.get_protocol_metrics()
        
        self.assertIn('created', metrics)
        self.assertIn('status_changes', metrics)
        self.assertIn('by_status', metrics)
        self.assertEqual(len(metrics['created']), 1)
        self.assertEqual(len(metrics['status_changes']), 1)
        self.assertEqual(len(metrics['by_status']), 1)


class ModelIntegrationTest(TestCase):
    """Test model integration with metrics service."""
    
    def setUp(self):
        self.mock_service = MockMetricsService()
        
        # Patch the service to use our mock
        with patch('protocols.services.laboratory_metrics_service.get_laboratory_metrics_service') as mock_get_service:
            mock_lab_service = LaboratoryMetricsService(self.mock_service)
            mock_get_service.return_value = mock_lab_service
            
            self.veterinarian = Veterinarian.objects.create(
                user=User.objects.create_user(
                    email='vet@test.com',
                    password='testpass'
                ),
                license_number='VET123'
            )
    
    def test_protocol_creation_records_metrics(self):
        """Test that protocol creation records metrics."""
        protocol = Protocol.objects.create(
            analysis_type=Protocol.AnalysisType.CYTOLOGY,
            veterinarian=self.veterinarian,
            species='canine',
            animal_identification='Test Animal',
            presumptive_diagnosis='Test Diagnosis'
        )
        
        # Check that metrics were recorded
        metric = self.mock_service.get_metric(
            'protocols_created_total',
            {
                'species': 'canine',
                'analysis_type': 'cytology',
                'veterinarian': str(self.veterinarian.id)
            }
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 1.0)
    
    def test_protocol_status_change_records_metrics(self):
        """Test that protocol status change records metrics."""
        protocol = ProtocolFactory(veterinarian=self.veterinarian)
        
        # Change status
        protocol.status = Protocol.Status.SUBMITTED
        protocol._changed_by_id = self.veterinarian.id  # Simulate who changed it
        protocol.save()
        
        # Check that metrics were recorded
        metric = self.mock_service.get_metric(
            'protocol_status_changes_total',
            {
                'from_status': 'draft',
                'to_status': 'submitted',
                'changed_by': str(self.veterinarian.id)
            }
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 1.0)


class ViewIntegrationTest(TestCase):
    """Test view integration with metrics service."""
    
    def setUp(self):
        self.mock_service = MockMetricsService()
        
        # Patch the service
        with patch('protocols.services.laboratory_metrics_service.get_laboratory_metrics_service') as mock_get_service:
            mock_lab_service = LaboratoryMetricsService(self.mock_service)
            mock_get_service.return_value = mock_lab_service
            
            self.user = User.objects.create_user(
                email='test@test.com',
                password='testpass',
                is_staff=True
            )
    
    def test_view_metrics_tracking(self):
        """Test that view metrics are tracked."""
        from protocols.decorators import track_view_metrics
        
        @track_view_metrics('test_view')
        def test_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')
        
        # Make a request
        request = MagicMock()
        request.method = 'GET'
        request.user = self.user
        
        response = test_view(request)
        
        # Check that metrics were recorded
        request_metric = self.mock_service.get_metric(
            'http_request_duration_seconds',
            {
                'method': 'GET',
                'endpoint': 'test_view',
                'status': '200'
            }
        )
        
        action_metric = self.mock_service.get_metric(
            'user_actions_total',
            {
                'user_type': 'staff',
                'action_type': 'view_access',
                'module': 'test_view'
            }
        )
        
        self.assertIsNotNone(request_metric)
        self.assertIsNotNone(action_metric)


class CeleryTaskIntegrationTest(TestCase):
    """Test Celery task integration with metrics service."""
    
    def setUp(self):
        self.mock_service = MockMetricsService()
        
        # Patch the service
        with patch('protocols.services.laboratory_metrics_service.get_laboratory_metrics_service') as mock_get_service:
            mock_lab_service = LaboratoryMetricsService(self.mock_service)
            mock_get_service.return_value = mock_lab_service
    
    def test_celery_task_metrics_tracking(self):
        """Test that Celery task metrics are tracked."""
        from protocols.decorators import track_celery_task_metrics
        
        @track_celery_task_metrics('test_task')
        def test_task():
            return 'success'
        
        # Execute task
        result = test_task()
        
        # Check that metrics were recorded
        success_metric = self.mock_service.get_metric(
            'celery_tasks_total',
            {
                'task_name': 'test_task',
                'status': 'success'
            }
        )
        
        duration_metric = self.mock_service.get_metric(
            'celery_task_duration_seconds',
            {
                'task_name': 'test_task'
            }
        )
        
        self.assertIsNotNone(success_metric)
        self.assertIsNotNone(duration_metric)
        self.assertEqual(success_metric.value, 1.0)
    
    def test_celery_task_failure_metrics(self):
        """Test that Celery task failure metrics are tracked."""
        from protocols.decorators import track_celery_task_metrics
        
        @track_celery_task_metrics('failing_task')
        def failing_task():
            raise ValueError('Test error')
        
        # Execute task and expect failure
        with self.assertRaises(ValueError):
            failing_task()
        
        # Check that failure metrics were recorded
        failure_metric = self.mock_service.get_metric(
            'celery_tasks_total',
            {
                'task_name': 'failing_task',
                'status': 'failure'
            }
        )
        
        self.assertIsNotNone(failure_metric)
        self.assertEqual(failure_metric.value, 1.0)


class ServiceFactoryTest(TestCase):
    """Test the service factory."""
    
    def test_get_metrics_service_mock(self):
        """Test getting mock metrics service."""
        from protocols.services.metrics_service import get_metrics_service
        
        service = get_metrics_service(use_mock=True)
        self.assertIsInstance(service, MockMetricsService)
    
    def test_get_metrics_service_production(self):
        """Test getting production metrics service."""
        from protocols.services.metrics_service import get_metrics_service
        
        service = get_metrics_service(use_mock=False)
        self.assertIsInstance(service, PrometheusMetricsService)


@override_settings(USE_MOCK_METRICS=True)
class SettingsIntegrationTest(TestCase):
    """Test integration with Django settings."""
    
    def test_use_mock_metrics_setting(self):
        """Test that USE_MOCK_METRICS setting works."""
        from protocols.services.laboratory_metrics_service import get_laboratory_metrics_service
        
        service = get_laboratory_metrics_service()
        self.assertIsInstance(service.metrics_service, MockMetricsService)
```

#### **7. Test Configuration**

Create `src/protocols/tests/conftest.py` (for pytest):

```python
"""
Pytest configuration for metrics testing.
"""

import pytest
from django.conf import settings
from protocols.services.metrics_service import MockMetricsService


@pytest.fixture
def mock_metrics_service():
    """Fixture providing a mock metrics service."""
    return MockMetricsService()


@pytest.fixture
def laboratory_metrics_service(mock_metrics_service):
    """Fixture providing a laboratory metrics service with mock backend."""
    from protocols.services.laboratory_metrics_service import LaboratoryMetricsService
    return LaboratoryMetricsService(mock_metrics_service)


@pytest.fixture(autouse=True)
def enable_mock_metrics():
    """Automatically enable mock metrics for all tests."""
    settings.USE_MOCK_METRICS = True
    yield
    settings.USE_MOCK_METRICS = False
```

#### **8. Integration Test Example**

Create `src/protocols/tests/test_metrics_integration.py`:

```python
"""
Integration tests for metrics service.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from protocols.services.laboratory_metrics_service import get_laboratory_metrics_service
from protocols.models import Protocol, Veterinarian
from protocols.tests.factories import ProtocolFactory
import time

User = get_user_model()


class MetricsIntegrationTest(TransactionTestCase):
    """Integration tests for metrics service."""
    
    def setUp(self):
        self.veterinarian = Veterinarian.objects.create(
            user=User.objects.create_user(
                email='vet@test.com',
                password='testpass'
            ),
            license_number='VET123'
        )
    
    def test_full_protocol_lifecycle_metrics(self):
        """Test metrics throughout a protocol's lifecycle."""
        metrics_service = get_laboratory_metrics_service()
        
        # Create protocol
        protocol = ProtocolFactory(veterinarian=self.veterinarian)
        
        # Check creation metrics
        created_metrics = metrics_service.get_protocol_metrics()['created']
        self.assertEqual(len(created_metrics), 1)
        
        # Submit protocol
        protocol.status = Protocol.Status.SUBMITTED
        protocol._changed_by_id = self.veterinarian.id
        protocol.save()
        
        # Check status change metrics
        status_metrics = metrics_service.get_protocol_metrics()['status_changes']
        self.assertEqual(len(status_metrics), 1)
        
        # Receive protocol
        protocol.status = Protocol.Status.RECEIVED
        protocol._changed_by_id = self.veterinarian.id
        protocol.save()
        
        # Check updated status change metrics
        status_metrics = metrics_service.get_protocol_metrics()['status_changes']
        self.assertEqual(len(status_metrics), 2)
    
    def test_metrics_performance(self):
        """Test that metrics don't significantly impact performance."""
        metrics_service = get_laboratory_metrics_service()
        
        start_time = time.time()
        
        # Record many metrics
        for i in range(1000):
            metrics_service.record_protocol_created(
                species='canine',
                analysis_type='cytology',
                veterinarian_id=self.veterinarian.id
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in less than 1 second
        self.assertLess(duration, 1.0)
        
        # Verify metrics were recorded
        created_metrics = metrics_service.get_protocol_metrics()['created']
        self.assertEqual(len(created_metrics), 1)  # All with same labels
        self.assertEqual(created_metrics[0].value, 1000.0)
```

## Troubleshooting

### 1. **Services Not Starting**

```bash
# Check container logs
docker-compose logs loki
docker-compose logs prometheus
docker-compose logs grafana

# Check service health
curl http://localhost:3100/ready
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

### 2. **No Logs Appearing**

- Check Promtail configuration
- Verify log file paths
- Check Loki connectivity

### 3. **Metrics Not Showing**

- Verify Django metrics endpoint: http://localhost:8000/metrics
- Check Prometheus targets: http://localhost:9090/targets
- Verify Celery Flower metrics: http://localhost:5555/metrics

### 4. **High Resource Usage**

- Adjust retention periods
- Optimize log parsing rules
- Scale monitoring components

## Performance Optimization

### 1. **Loki Optimization**

- Use appropriate chunk sizes
- Optimize label cardinality
- Use log parsing rules efficiently

### 2. **Prometheus Optimization**

- Adjust scrape intervals
- Use recording rules for complex queries
- Optimize metric cardinality

### 3. **Grafana Optimization**

- Limit dashboard refresh rates
- Use appropriate time ranges
- Optimize query complexity

---

*Step 18 - Monitoring and Metrics*  
*Created: January 2025*  
*Priority: High - Essential for production operations*
