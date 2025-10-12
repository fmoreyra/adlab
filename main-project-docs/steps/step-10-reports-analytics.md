# Step 10: Reports & Analytics

## Problem Statement

Laboratory management needs detailed analytical reports for decision-making, performance evaluation, and planning. Historical data is currently difficult to access and analyze. The system should provide comprehensive reports on volume, productivity, turnaround times, client activity, and other key metrics through web-based dashboards that are print-friendly.

## Requirements

### Functional Requirements (RF10)

- **RF10.1**: Historical volume reports (web page)
- **RF10.2**: Turnaround time analysis (web page)
- **RF10.3**: Productivity by histopathologist (web page)
- **RF10.4**: Most frequent analysis types (web page)
- **RF10.5**: Most active clients (web page)
- **RF10.6**: Print-friendly report pages
- **RF10.7**: Daily automated analytics calculation (Celery)
- **RF10.8**: Display last calculation timestamp
- **RF10.9**: Manual refresh option (admin only)
- Admin-only access to analytics
- Fixed date ranges (last 30 days, last 90 days, last year, all time)
- Print page functionality for physical reports

### Non-Functional Requirements

- **Performance**: Analytics calculation completes in < 2 minutes (background task)
- **Performance**: Page load < 2 seconds (cached data)
- **Scalability**: Handle 10+ years of historical data
- **Accuracy**: 100% data accuracy
- **Usability**: Clean, print-friendly layouts

## Data Model

### Existing Tables (Queried)

Reports primarily query existing tables:
- `Protocol` - Protocol submissions and reception dates
- `Report` - Report generation dates and turnaround times
- `Veterinarian` - Client information and activity
- `Histopathologist` - Productivity metrics
- `WorkOrder` - Financial data

### New Model: AnalyticsSnapshot

Store pre-calculated analytics to avoid heavy queries on every page load.

```python
class AnalyticsSnapshot(models.Model):
    """
    Stores pre-calculated analytics data.
    Updated daily by Celery task.
    """
    
    class ReportType(models.TextChoices):
        VOLUME = 'volume', 'Volume Report'
        TAT = 'tat', 'Turnaround Time'
        PRODUCTIVITY = 'productivity', 'Productivity'
        CLIENTS = 'clients', 'Client Activity'
        SERVICES = 'services', 'Service Mix'
    
    class DateRange(models.TextChoices):
        LAST_30_DAYS = '30d', 'Last 30 Days'
        LAST_90_DAYS = '90d', 'Last 90 Days'
        LAST_YEAR = '1y', 'Last Year'
        ALL_TIME = 'all', 'All Time'
    
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    date_range = models.CharField(max_length=10, choices=DateRange.choices)
    data = models.JSONField()
    calculated_at = models.DateTimeField(auto_now=True)
    calculation_duration = models.FloatField(help_text="Seconds")
    
    class Meta:
        unique_together = [['report_type', 'date_range']]
        indexes = [
            models.Index(fields=['report_type', 'date_range']),
            models.Index(fields=['calculated_at']),
        ]
```

## URL Design

### Analytics Pages (Admin Only)

All analytics pages require admin authentication via `@user_passes_test(lambda u: u.is_staff)`.

#### GET /analytics/
Analytics dashboard overview.

**Template:** `protocols/analytics/dashboard.html`

**Context:**
- `snapshots`: Dict of latest AnalyticsSnapshot objects
- `last_calculation`: Most recent calculation timestamp
- Links to all report pages

#### GET /analytics/volume/?range=30d
Volume report page.

**Template:** `protocols/analytics/volume.html`

**Query Parameters:**
- `range`: '30d', '90d', '1y', 'all' (default: '30d')

**Context:**
- `data`: Pre-calculated volume data from AnalyticsSnapshot
- `date_range`: Selected date range
- `calculated_at`: When data was last calculated
- Chart data for visualization

#### GET /analytics/tat/?range=30d
Turnaround time analysis page.

**Template:** `protocols/analytics/tat.html`

**Query Parameters:**
- `range`: '30d', '90d', '1y', 'all' (default: '30d')

**Context:**
- `data`: TAT metrics from AnalyticsSnapshot
- `date_range`: Selected date range
- `calculated_at`: Timestamp

#### GET /analytics/productivity/?range=30d
Productivity by histopathologist page.

**Template:** `protocols/analytics/productivity.html`

**Query Parameters:**
- `range`: '30d', '90d', '1y', 'all' (default: '30d')

**Context:**
- `data`: Productivity metrics from AnalyticsSnapshot
- `date_range`: Selected date range

#### GET /analytics/clients/?range=30d
Client activity analysis page.

**Template:** `protocols/analytics/clients.html`

**Query Parameters:**
- `range`: '30d', '90d', '1y', 'all' (default: '30d')
- `top_n`: Number of top clients (default: 20)

**Context:**
- `data`: Client rankings from AnalyticsSnapshot
- `top_n`: Number displayed

#### GET /analytics/services/?range=30d
Service mix analysis page.

**Template:** `protocols/analytics/services.html`

**Query Parameters:**
- `range`: '30d', '90d', '1y', 'all' (default: '30d')

**Context:**
- `data`: Service distribution from AnalyticsSnapshot

#### POST /analytics/refresh/
Manual refresh of all analytics (admin only).

**Permission:** Superuser only (`@user_passes_test(lambda u: u.is_superuser)`)

**Action:** Triggers `calculate_all_analytics.delay()` Celery task

**Response:** Redirect to dashboard with success message

## Business Logic

### Report Types

**1. Volume Report**
- Protocols received per period
- By analysis type (Histopathology, Cytology)
- Monthly/weekly trends
- Year-over-year comparison

**2. TAT Report**
- Average, median turnaround time
- Distribution histogram (0-3, 4-7, 8-14, 15+ days)
- Compliance with target (10 days)
- By analysis type

**3. Productivity Report**
- Reports per histopathologist
- Average weekly output
- Average TAT per histopathologist
- Distribution by analysis type

**4. Client Report**
- Top 20 most active clients
- Protocols per client
- Revenue per client (if WorkOrder data available)
- Service preferences

**5. Service Mix Report**
- Distribution by analysis type
- Distribution by species
- Common diagnoses
- Trend analysis

### Calculation Methods

**Protocolos Agregados:**
From document Ch. II.4:
```
1 Protocol Agregado = 1 HP = 2 CT
```

Used for capacity and productivity calculations.

**TAT Calculation:**
```python
tat_days = (report.report_date - protocol.reception_date).days
```

### Celery Tasks

#### Daily Calculation Task

**Task:** `calculate_all_analytics`
**Schedule:** Every day at 2:00 AM
**Action:** Calculate all report types for all date ranges

```python
@shared_task
def calculate_all_analytics():
    """
    Calculate all analytics snapshots.
    Runs daily at 2 AM via Celery beat.
    """
    report_types = ['volume', 'tat', 'productivity', 'clients', 'services']
    date_ranges = ['30d', '90d', '1y', 'all']
    
    for report_type in report_types:
        for date_range in date_ranges:
            calculate_analytics_snapshot(report_type, date_range)
```

#### Individual Calculation

**Task:** `calculate_analytics_snapshot(report_type, date_range)`
**Action:** Calculate and store one specific analytics snapshot

**Process:**
1. Determine date range boundaries
2. Query relevant data from database
3. Perform aggregations and calculations
4. Store results in `AnalyticsSnapshot` model
5. Record calculation duration

### Print Functionality

All analytics pages include print-friendly CSS:
- Clean layouts without navigation
- Page breaks where appropriate
- Black and white friendly
- Logo and header on each page
- Footer with "Generated on: [date]" and "Page X of Y"

## Acceptance Criteria

1. [ ] Volume report page displays data correctly
2. [ ] TAT report calculates and displays correctly
3. [ ] Productivity per histopathologist is accurate
4. [ ] Client activity rankings are correct
5. [ ] Service mix analysis is comprehensive
6. [ ] Date range selector works (30d, 90d, 1y, all)
7. [ ] Celery task calculates all analytics daily at 2 AM
8. [ ] Manual refresh triggers Celery task (superuser only)
9. [ ] Last calculation timestamp displays on all pages
10. [ ] Pages are print-friendly (clean layout, no navigation)
11. [ ] Only staff users can access analytics pages
12. [ ] AnalyticsSnapshot model stores data correctly
13. [ ] Page loads in < 2 seconds (using cached data)
14. [ ] Analytics calculation completes in < 2 minutes
15. [ ] Dashboard provides overview and links to all reports

## Testing Approach

### Unit Tests
- **Model Tests:**
  - `AnalyticsSnapshot` creation and retrieval
  - Unique constraint on (report_type, date_range)
  - JSONField data storage

- **Calculation Tests:**
  - Volume calculation logic
  - TAT calculation with different date ranges
  - Productivity metrics per histopathologist
  - Client ranking algorithm
  - Service mix aggregations

- **Date Range Tests:**
  - 30-day range boundary calculation
  - 90-day range boundary calculation
  - 1-year range boundary calculation
  - All-time range handling

### Integration Tests
- **View Tests:**
  - Dashboard view renders correctly
  - Each report view retrieves correct snapshot
  - Date range query parameter works
  - Staff-only access enforcement
  - Superuser-only refresh enforcement

- **Celery Task Tests:**
  - `calculate_all_analytics` task creates all snapshots
  - `calculate_analytics_snapshot` for each report type
  - Task records calculation duration
  - Task handles missing data gracefully

### Performance Tests
- Query performance with 10+ years of data
- Analytics calculation completes in < 2 minutes
- Page load times < 2 seconds with cached data
- Celery task doesn't block web server

## Technical Considerations

### Technology Stack

**Backend:**
- Django views with staff authentication
- Celery for scheduled analytics calculation
- Celery Beat for daily scheduling (2 AM)
- PostgreSQL JSONField for flexible data storage

**Frontend:**
- Django templates with print-friendly CSS
- Chart.js for visualizations (optional)
- Responsive tables for data display
- Browser print functionality (Ctrl+P / Cmd+P)

### Performance Optimization

**Query Optimization:**
- Indexed columns: `reception_date`, `report_date`, `analysis_type`
- Use Django ORM aggregations (`Count`, `Avg`, `Sum`)
- Limit queries to specific date ranges
- Use `select_related()` and `prefetch_related()` for joins

**Caching Strategy:**
- Pre-calculate analytics daily via Celery
- Store results in `AnalyticsSnapshot` model
- Views simply retrieve cached data (no heavy queries)
- Display last calculation timestamp to users

**Celery Configuration:**
```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'calculate-daily-analytics': {
        'task': 'protocols.tasks.calculate_all_analytics',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
    },
}
```

### Print CSS

```css
@media print {
  /* Hide navigation, buttons, etc. */
  nav, .no-print, .btn, header, footer { display: none; }
  
  /* Optimize for printing */
  body { font-size: 12pt; }
  table { page-break-inside: avoid; }
  tr, img { page-break-inside: avoid; }
  
  /* Add page headers */
  @page {
    margin: 2cm;
    @top-center {
      content: "Laboratory Analytics Report";
    }
    @bottom-right {
      content: "Page " counter(page) " of " counter(pages);
    }
  }
}
```

## Dependencies

### Must be completed first:
- Step 03: Protocol Submission (provides Protocol data)
- Step 04: Sample Reception (provides reception dates)
- Step 06: Report Generation (provides Report data and TAT)
- Step 07: Work Orders (optional, for revenue metrics)
- Celery configuration (from Step 08 or earlier)

### Estimated Effort

**Time**: 4-5 days

**Breakdown**:
- Data model and migrations: 0.5 day
- Analytics calculation logic: 1.5 days
- Celery tasks and scheduling: 0.5 day
- Views and URL routing: 1 day
- Templates (5 reports + dashboard): 1.5 days
- Print CSS styling: 0.5 day
- Testing: 1 day
- Admin integration: 0.5 day

## Implementation Notes

### Sample Django Query (Volume by Month)

```python
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

def calculate_volume_data(date_range):
    """Calculate volume metrics for a given date range."""
    start_date, end_date = get_date_boundaries(date_range)
    
    # Group by month and analysis type
    volume_by_month = Protocol.objects.filter(
        reception_date__gte=start_date,
        reception_date__lte=end_date
    ).annotate(
        month=TruncMonth('reception_date')
    ).values('month', 'analysis_type').annotate(
        count=Count('id')
    ).order_by('month', 'analysis_type')
    
    # Aggregate totals
    totals = Protocol.objects.filter(
        reception_date__gte=start_date,
        reception_date__lte=end_date
    ).values('analysis_type').annotate(
        total=Count('id')
    )
    
    return {
        'period': {'from': start_date, 'to': end_date},
        'monthly_data': list(volume_by_month),
        'totals': {item['analysis_type']: item['total'] for item in totals}
    }
```

### Sample TAT Calculation

```python
from django.db.models import Avg, F, ExpressionWrapper, fields

def calculate_tat_data(date_range):
    """Calculate TAT metrics."""
    start_date, end_date = get_date_boundaries(date_range)
    
    # Calculate TAT in days
    reports = Report.objects.filter(
        protocol__reception_date__gte=start_date,
        protocol__reception_date__lte=end_date,
        report_date__isnull=False
    ).annotate(
        tat_days=ExpressionWrapper(
            F('report_date') - F('protocol__reception_date'),
            output_field=fields.DurationField()
        )
    )
    
    # Distribution buckets
    distribution = {
        '0-3_days': reports.filter(tat_days__lte=timedelta(days=3)).count(),
        '4-7_days': reports.filter(
            tat_days__gt=timedelta(days=3),
            tat_days__lte=timedelta(days=7)
        ).count(),
        '8-14_days': reports.filter(
            tat_days__gt=timedelta(days=7),
            tat_days__lte=timedelta(days=14)
        ).count(),
        'over_14_days': reports.filter(tat_days__gt=timedelta(days=14)).count(),
    }
    
    avg_tat = reports.aggregate(Avg('tat_days'))['tat_days__avg']
    
    return {
        'average_tat_days': avg_tat.days if avg_tat else 0,
        'distribution': distribution,
        'target_days': 10,
        'compliance_pct': calculate_compliance(distribution)
    }
```

### Celery Task Example

```python
# protocols/tasks.py
from celery import shared_task
from datetime import datetime
import time

@shared_task
def calculate_analytics_snapshot(report_type, date_range):
    """Calculate and store one analytics snapshot."""
    start_time = time.time()
    
    # Calculate data based on report type
    if report_type == 'volume':
        data = calculate_volume_data(date_range)
    elif report_type == 'tat':
        data = calculate_tat_data(date_range)
    # ... other report types
    
    duration = time.time() - start_time
    
    # Store in database
    AnalyticsSnapshot.objects.update_or_create(
        report_type=report_type,
        date_range=date_range,
        defaults={
            'data': data,
            'calculation_duration': duration
        }
    )
    
    return f"{report_type}/{date_range} calculated in {duration:.2f}s"
```

### View Example

```python
# protocols/views_analytics.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AnalyticsSnapshot
from .tasks import calculate_all_analytics

@user_passes_test(lambda u: u.is_staff)
def analytics_dashboard_view(request):
    """Main analytics dashboard."""
    # Get latest snapshots
    latest_snapshots = {}
    for report_type in ['volume', 'tat', 'productivity', 'clients', 'services']:
        snapshot = AnalyticsSnapshot.objects.filter(
            report_type=report_type
        ).order_by('-calculated_at').first()
        latest_snapshots[report_type] = snapshot
    
    context = {
        'snapshots': latest_snapshots,
        'last_calculation': max(
            (s.calculated_at for s in latest_snapshots.values() if s),
            default=None
        )
    }
    return render(request, 'protocols/analytics/dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def analytics_volume_view(request):
    """Volume report page."""
    date_range = request.GET.get('range', '30d')
    
    snapshot = AnalyticsSnapshot.objects.filter(
        report_type='volume',
        date_range=date_range
    ).first()
    
    context = {
        'data': snapshot.data if snapshot else {},
        'date_range': date_range,
        'calculated_at': snapshot.calculated_at if snapshot else None
    }
    return render(request, 'protocols/analytics/volume.html', context)

@user_passes_test(lambda u: u.is_superuser)
def analytics_refresh_view(request):
    """Trigger manual refresh of all analytics."""
    if request.method == 'POST':
        calculate_all_analytics.delay()
        messages.success(request, 'Analytics recalculation started. Check back in a few minutes.')
        return redirect('analytics_dashboard')
```

### Testing Checklist
- [ ] AnalyticsSnapshot model saves and retrieves data
- [ ] Volume report calculates for all date ranges
- [ ] TAT report calculates correctly
- [ ] Productivity report accurate per histopathologist
- [ ] Client rankings correct
- [ ] Celery task completes successfully
- [ ] Celery Beat schedule configured
- [ ] Staff-only access enforced
- [ ] Superuser-only refresh enforced
- [ ] Print CSS renders correctly
- [ ] Page loads quickly with cached data
- [ ] Dashboard displays all reports
- [ ] Manual refresh triggers task

