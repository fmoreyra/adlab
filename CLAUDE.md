# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Workflow
```bash
# Start all services (first time: 5-10 minutes to build)
docker compose up --build

# Run database migrations
make manage ARGS="migrate"

# Run the test suite (RECOMMENDED: use SQLite for faster local development)
make test-with-sqlite              # Fast: ~10 seconds (uses SQLite in-memory)
make test                           # Slow: ~3-5 minutes (uses PostgreSQL)

# Run a single test file (RECOMMENDED: use SQLite for faster runs)
make test-with-sqlite ARGS="accounts.tests"

# Run a specific test method with SQLite
make test-with-sqlite ARGS="protocols.tests.ProtocolTestCase.test_protocol_creation"

# Code quality checks
make lint                # Lint Python code with ruff
make format              # Format Python code with ruff
make quality             # Run all quality checks (lint + format + shell checks)

# Clean up test database (if tests hang)
make test-cleanup

# Database operations
make psql                # Connect to PostgreSQL
make db-dump             # Generate database dump in ./backups/

# Shell access
make shell               # Bash shell in web container
make manage ARGS="shell" # Django shell

# Check outdated dependencies
make uv-outdated         # Python packages
make yarn-outdated       # Node packages
```

### Important Notes
- Use `make <target>` or `make <target> ARGS="..."` to run commands
- Tests automatically set `CELERY_TASK_ALWAYS_EAGER=True` (synchronous execution)
- Test database is auto-created as `test_adlab` and cleaned up after tests
- **For local development: always use `make test-with-sqlite`** - it's ~20x faster than PostgreSQL (10s vs 3-5min). The test settings in `config/settings_test.py` configure SQLite in-memory for maximum speed.
- **For CI: use PostgreSQL** (`make test` or `./scripts/test-wrapper.sh`) to match production behavior

## Architecture Overview

### Core Django Applications

**accounts**: User authentication and authorization
- Custom User model with email as username
- Four roles: VETERINARIO, PERSONAL_LAB, HISTOPATOLOGO, ADMIN
- Email verification required only for veterinarians
- Account lockout after 5 failed login attempts
- Related models: `Veterinarian`, `Histopathologist`, `AuthAuditLog`

**protocols**: Core business domain (contains all main models despite the name)
- Central models: `Protocol`, `HistopathologySample`, `CytologySample`
- Sample processing: `Cassette`, `Slide`, `CassetteSlide` (junction table)
- Report generation: `Report`, `CassetteObservation`, `ReportImage`
- Work orders: `WorkOrder`, `PricingCatalog` (all in protocols/models.py)
- Background tasks: `send_email` Celery task with retry logic

**pages**: Dashboard views and statistics
- Role-based dashboards route through `DashboardView`
- Management dashboard API with 2-minute Redis caching
- Real-time metrics: WIP, TAT, productivity per histopathologist

**reports**: Report PDF generation functionality
- Actually implemented in protocols app; this is primarily for organization

**workorders**: Work order/invoice management
- Models live in protocols app; billing logic in `services/workorder_service.py`

**up**: Health check endpoints for monitoring

### Critical Workflow: Protocol Lifecycle

```
1. DRAFT → SUBMITTED (veterinarian submits)
   - System assigns temporary_code (TMP-HP-20241017-001)

2. SUBMITTED → RECEIVED (lab staff reception)
   - Assigns protocol_number using ProtocolCounter (HP 24/001)
   - Sample condition assessment (OPTIMAL, ACCEPTABLE, etc.)
   - Creates HistopathologySample or CytologySample

3. RECEIVED → PROCESSING
   - Lab creates Cassettes (for histopathology)
   - Creates Slides (can link to multiple cassettes via CassetteSlide)
   - Updates processing stages (encasetado → fijacion → inclusion → etc)

4. PROCESSING → READY
   - All cassettes/slides reach final stage

5. Histopathologist creates Report (DRAFT → FINALIZED)
   - Adds CassetteObservations with microscopic findings
   - Optionally attaches ReportImages
   - Signs with digital signature

6. READY → REPORT_SENT
   - PDF generated via ReportLab (services/pdf_service.py)
   - Email queued via Celery (protocols/tasks.py)
   - EmailLog tracks delivery status
```

### Counter Pattern (Critical for Concurrency)

All sequential numbering uses atomic database locks to prevent race conditions:

```python
# protocols/models.py - ProtocolCounter.get_next_number()
with transaction.atomic():
    counter, created = cls.objects.select_for_update().get_or_create(...)
    counter.last_number += 1
    counter.save()
```

This pattern is used by:
- `ProtocolCounter` (protocol_number: HP 24/001)
- `TemporaryCodeCounter` (temporary_code: TMP-HP-20241017-001)
- `WorkOrderCounter` (work_order_number: WO-2024-001)

**Never bypass this pattern** when generating sequential identifiers.

### Background Tasks: Celery + Redis

**Configuration** (`config/celery.py`, `config/settings.py`):
- Broker: Redis
- Result backend: Redis
- Task serialization: JSON only (models must be serialized manually)

**Email Task Pattern**:
```python
# protocols/tasks.py
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, context, email_log_id):
    # Deserialize models from {"id": X, "model": "app.Model"}
    # Render template
    # Send via Django's email backend
    # Update EmailLog status
```

**Model Serialization Issue**: Celery can't serialize Django model instances in JSON. Solution:
1. Helper functions in `protocols/emails.py` convert models to dicts
2. Task reconstructs models using `apps.get_model()` and IDs
3. Fallback to string repr if object no longer exists

### Email System Architecture

Three-layer design:
1. **High-level helpers** (`protocols/emails.py`): Business logic, preference checking
2. **Service wrapper** (`protocols/services/email_service.py`): View-friendly interface
3. **Task execution** (`protocols/tasks.py`): Celery task with retries

**NotificationPreference model** controls per-veterinarian settings:
- notify_on_reception, notify_on_report_ready, etc.
- use_alternative_email option
- include_attachments toggle

**EmailLog model** tracks all business emails:
- Email type classification (VERIFICATION, REPORT_READY, etc.)
- Celery task_id for audit trail
- Related object references (protocol, work_order)
- Status: QUEUED → SENT/FAILED

### PDF Generation

**ReportLab-based** (`services/pdf_service.py`):
- `generate_report_pdf(report)` → (BytesIO, sha256_hash)
- `generate_workorder_pdf(work_order)` → (BytesIO, sha256_hash)
- SHA-256 hash stored in Report/WorkOrder models for integrity verification
- Supports embedding histopathologist's signature image

### Frontend Architecture

**Django templates** + **Vue.js** components + **TailwindCSS**
- Server-side rendering for most views
- Vue.js for interactive components (slide registration, dashboards)
- esbuild bundles assets (assets/package.json)
- WhiteNoise serves static files (no S3 dependency)

### Testing Patterns

**Custom test runner** (`config/test_runner.py`):
- `DockerTestRunner` extends Django's DiscoverRunner
- Handles test database cleanup in Docker environment
- Sets `CONN_MAX_AGE=0` during tests (prevents connection state leakage)

**Celery in tests**:
- `CELERY_TASK_ALWAYS_EAGER=True` forces synchronous execution
- No need to mock Celery tasks in most tests

**Common test scenarios**:
- Concurrency tests for counter atomicity (protocols/tests_concurrency.py)
- Permission tests for role-based access (accounts/test_views.py)
- Email queueing tests (protocols/test_emails.py)

## Key Design Decisions

### 1. Model Organization
**All domain models in protocols/models.py** despite conceptual separation (reports, workorders). This keeps business logic centralized and avoids circular dependencies.

### 2. Denormalized Data
- Animal data embedded in Protocol (not separate Animal model)
- Veterinarian.email duplicates User.email
- Trade-off: Fewer joins vs. update complexity

### 3. Email Verification
**Only required for veterinarians** (external users). Lab staff and admins bypass verification to reduce internal friction.

### 4. Sample Type Polymorphism
- `Protocol` has OneToOne to `HistopathologySample` OR `CytologySample`
- Each sample type has distinct processing models
- Avoids bloating Protocol with type-specific fields

### 5. Cassette-Slide Relationship
**Many-to-many via CassetteSlide junction table**. Multiple tissue cassettes can be mounted on a single microscope slide. This reflects real-world histopathology workflow.

### 6. Work Order Grouping
- Multiple protocols can be grouped into one WorkOrder
- Pricing determined dynamically from PricingCatalog (supports date-based pricing)
- Payment tracking: advance_payment, balance_due, payment_status

## Common Development Tasks

### Adding a New Email Notification

1. Add email type to `EmailLog.EmailType` choices (protocols/models.py)
2. Create helper function in `protocols/emails.py`:
   ```python
   def send_new_notification(protocol, request=None):
       context = serialize_email_context({
           'protocol': protocol,
           # ... other context
       })
       email_log = EmailLog.objects.create(
           email_type=EmailLog.EmailType.NEW_TYPE,
           recipient_email=protocol.veterinarian.email,
           related_protocol=protocol,
           celery_task_id='pending'
       )
       result = send_email.delay(context, email_log.id)
       email_log.celery_task_id = result.id
       email_log.save()
       return email_log
   ```
3. Create email template in `templates/emails/new_notification_email.html`
4. Add tests in `protocols/test_emails.py`

### Adding a New Protocol Status

1. Update `Protocol.Status` choices (protocols/models.py)
2. Add status transition method to Protocol model:
   ```python
   def transition_to_new_status(self):
       self.status = self.Status.NEW_STATUS
       self.save()
       ProtocolStatusHistory.objects.create(
           protocol=self,
           status=self.Status.NEW_STATUS,
           changed_by=user
       )
   ```
3. Update dashboard filters in `pages/views.py`
4. Add permission checks in `accounts/mixins.py` if needed
5. Update tests in `protocols/tests.py`

### Adding a New Role

1. Add role to `User.Role` choices (accounts/models.py)
2. Create decorator in `accounts/decorators.py`:
   ```python
   def new_role_required(view_func):
       @wraps(view_func)
       def wrapper(request, *args, **kwargs):
           if not request.user.is_authenticated or request.user.role != User.Role.NEW_ROLE:
               return redirect('accounts:login')
           return view_func(request, *args, **kwargs)
       return wrapper
   ```
3. Create dashboard view in `pages/views.py`
4. Update `DashboardView.get()` routing logic
5. Add tests in `accounts/test_mixins.py`

### Working with Migrations

```bash
# Create new migration after model changes
make manage ARGS="makemigrations"

# Apply migrations
make manage ARGS="migrate"

# View migration SQL without applying
make manage ARGS="sqlmigrate <app_label> <migration_name>"

# Show migration status
make manage ARGS="showmigrations"
```

## Security Considerations

- **Authentication tokens**: 32-byte URL-safe random tokens for email verification
- **Password reset tokens**: One-time use, 1-hour expiry
- **Account lockout**: Automatic after 5 failed login attempts
- **Audit logging**: All auth events logged to AuthAuditLog
- **PDF integrity**: SHA-256 hash verification for reports and work orders
- **Permission mixins**: Always use role-based decorators on views
- **CSRF protection**: Django's built-in CSRF middleware enabled
- **Email verification**: Required for external users (veterinarians)

## Performance Optimization

### Database
- Connection pooling: `CONN_MAX_AGE=60` (0 during tests)
- Strategic indexes on Protocol, Report, EmailLog (see models.py)
- `select_related()` for foreign keys, `prefetch_related()` for reverse relations

### Caching
- Redis for session storage
- Dashboard metrics cached for 2 minutes (pages/api_views.py:64)
- Template caching disabled in DEBUG mode

### Async Operations
- All email operations non-blocking via Celery
- Retry logic with exponential backoff (1min → 2min → 4min, max 10min)

## Common Pitfalls

1. **Don't bypass ProtocolCounter**: Always use `ProtocolCounter.get_next_number()` for protocol numbering
2. **Don't serialize models directly to Celery**: Use `serialize_email_context()` helper
3. **Don't forget email preferences**: Check `NotificationPreference` before sending emails
4. **Don't use `CONN_MAX_AGE` > 0 in tests**: Causes connection state leakage
5. **Don't forget status history**: Always create `ProtocolStatusHistory` on status changes
6. **Don't skip collectstatic before tests**: Tests fail without static files
7. **Don't use parallel test execution**: Database cleanup issues in Docker (use sequential)

## File Locations Reference

### Core Business Logic
- `src/protocols/models.py` - All domain models (Protocol, Sample, Report, WorkOrder)
- `src/protocols/views.py` - Protocol CRUD views
- `src/protocols/views_reports.py` - Report creation/editing views
- `src/protocols/views_workorder.py` - Work order management views
- `src/protocols/admin.py` - Django admin customizations
- `src/protocols/tasks.py` - Celery background tasks
- `src/protocols/emails.py` - Email notification helpers

### Services
- `src/services/pdf_service.py` - ReportLab PDF generation
- `src/services/workorder_service.py` - Pricing calculation, work order creation
- `src/services/email_service.py` - Email notification service wrapper

### User Management
- `src/accounts/models.py` - User, Veterinarian, Histopathologist models
- `src/accounts/views.py` - Authentication views (login, register, verify)
- `src/accounts/decorators.py` - Role-based permission decorators
- `src/accounts/mixins.py` - View mixins for permission checking

### Dashboard & UI
- `src/pages/views.py` - Dashboard views and routing
- `src/pages/api_views.py` - REST API for dashboard metrics

### Configuration
- `src/config/settings.py` - Django settings (DB, cache, email, etc.)
- `src/config/celery.py` - Celery configuration
- `src/config/urls.py` - URL routing
- `.env` - Environment variables (copy from .env.example)

### Frontend Assets
- `assets/` - JavaScript, CSS, images (managed by esbuild)
- `src/templates/` - Django templates
- `public/` - Static files served by WhiteNoise
- `public_collected/` - collectstatic output (git-ignored)

## Production Deployment

See `PRODUCTION_DEPLOYMENT.md` for complete production deployment guide including:
- Nginx configuration with SSL
- Gunicorn setup
- Database migration strategy
- Static file handling
- Email configuration
- Backup procedures

## Additional Documentation

- `README.md` - Comprehensive project overview and setup instructions
- `LABORATORY_SETUP.md` - Detailed laboratory workflow setup
- `TEST_CREDENTIALS.md` - Test user credentials for development
- `EMAIL_CONFIGURATION_GUIDE.md` - Email system configuration
- `STORAGE_BACKUP_GUIDE.md` - Backup and restore procedures
- `DEPLOYMENT_GUIDE.md` - Deployment strategies and best practices
