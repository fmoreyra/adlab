# Laboratory System - Current Project Structure & Reference

## Project Overview

This document provides a current state reference for the Laboratory Management System, including all implemented steps, user roles, and system architecture. This serves as a comprehensive guide for understanding the existing codebase before implementing changes.

## Current User Roles

### Implemented Roles
1. **VETERINARIO** - Veterinary Clients
   - Submit protocols and track samples
   - Download reports and manage work orders
   - Professional profile with license verification

2. **PERSONAL_LAB** - Laboratory Staff
   - Sample reception and processing
   - Cassette and slide management
   - Work order creation and tracking

3. **HISTOPATOLOGO** - Histopathologists
   - Report creation and diagnosis
   - Digital signature management
   - Professional credentials and specialty

4. **ADMIN** - System Administrators
   - User management and system configuration
   - Analytics and monitoring access
   - Full system privileges

### Role Separation (Pre-Step-16)
- Separate dashboards for lab staff and histopathologists
- Different permission decorators and mixins
- Distinct workflow interfaces
- Separate profile models and admin interfaces

## Completed Implementation Steps

### ✅ Step 01: Authentication & User Management
- Custom User model with role-based access
- Email verification system for veterinarians
- Password reset and account lockout
- Authentication audit logging
- Separate histopathologist login page
- Admin histopathologist creation workflow

### ✅ Step 01.1: Email Verification
- Token-based email verification
- Expiration handling and resend functionality
- Verification status tracking
- Integration with authentication flow

### ✅ Step 02: Veterinarian Registration & Profiles
- Professional profile management
- License number validation
- Address management with province/locality
- Profile verification by laboratory staff
- Change history and audit logging

### ✅ Step 03: Protocol Submission
- Digital protocol submission forms
- Cytology and histopathology support
- Temporary code generation
- Draft saving and validation
- Animal and sample data management

### ✅ Step 04: Sample Reception & Protocol Assignment
- Protocol matching and verification
- Final protocol number assignment
- Sample condition assessment
- Label generation and printing
- Reception discrepancy handling

### ✅ Step 05: Sample Processing
- Cassette creation and tracking
- Slide registration and management
- Processing stage workflow
- Quality control integration
- Processing history logging

### ✅ Step 06: Report Generation
- Professional report templates
- Digital signature integration
- PDF generation with ReportLab
- Report status management
- Email delivery integration

### ✅ Step 07: Work Orders
- Automatic work order generation
- Multi-protocol grouping
- Pricing catalog integration
- PDF work order creation
- Billing and payment tracking

### ✅ Step 08: Email Notifications
- Celery-based email system
- Multiple notification types
- Template management
- Delivery tracking
- Retry logic and error handling

### ✅ Step 15: User Dashboards & Feature Discovery
- Role-specific dashboard views
- Feature discovery cards
- Quick action buttons
- Statistics widgets
- Workflow guidance

## Partially Implemented Steps

### 🔄 Step 09: Dashboard & Monitoreo
- API endpoints implemented for metrics
- WIP, TAT, and productivity calculations
- Visual dashboard partially complete

### ⏳ Step 10: Reports & Analytics
- Historical report generation planned
- Productivity analytics planned
- Client activity tracking planned

### ⏳ Step 12: System Administration
- Django admin customization planned
- System monitoring interface planned
- User management tools planned

### ⏳ Step 13: Email Configuration
- Production email setup planned
- SMTP configuration planned
- Delivery monitoring planned

## Current System Architecture

### Database Models
```python
# Core Models
User (AbstractUser)
├── Veterinarian (OneToOne)
├── Histopathologist (OneToOne)  # TO BE MERGED
└── AuthAuditLog (Related)

Protocol
├── HistopathologySample (OneToOne)
├── CytologySample (OneToOne)
├── Cassette (Related)
├── Slide (Related)
├── Report (Related - via histopathologist FK)
└── WorkOrder (Related)

Report
├── ReportImages (Related)
├── CassetteObservations (Related)
└── PDF hash storage

EmailLog
└── Notification tracking and delivery status
```

### Permission System
```python
# Current Permission Decorators
@veterinarian_required      # Veterinarian access only
@lab_staff_required          # PERSONAL_LAB + HISTOPATOLOGO
@histopathologist_required    # HISTOPATOLOGO only (TO BE REMOVED)
@admin_required              # Admin access only

# Current Permission Mixins
VeterinarianRequiredMixin      # Veterinarian CBV access
StaffRequiredMixin           # Lab staff CBV access
HistopathologistRequiredMixin  # HISTOPATOLOGO CBV access (TO BE REMOVED)
ReportAccessMixin           # Report access control
```

### Dashboard System
```python
# Current Dashboard Views
DashboardView (Router)
├── VeterinarianDashboardView     # Protocol management
├── LabStaffDashboardView        # Sample processing
├── HistopathologistDashboardView  # Report creation (TO BE MERGED)
└── AdminDashboardView           # System administration

# Dashboard Templates
dashboard_veterinarian.html     # Protocol tracking
dashboard_lab_staff.html        # Processing queue
dashboard_histopathologist.html  # Report management (TO BE REMOVED)
dashboard_admin.html            # System metrics
```

## Current File Structure

### Key Application Structure
```
src/
├── accounts/
│   ├── models.py          # User, Veterinarian, Histopathologist, AuthAuditLog
│   ├── views.py           # Authentication, registration, profile management
│   ├── decorators.py       # Role-based permission decorators
│   ├── mixins.py          # Permission mixins for CBVs
│   ├── forms.py           # User registration and profile forms
│   ├── admin.py           # Django admin configuration
│   └── templates/         # Authentication templates
├── protocols/
│   ├── models.py          # Protocol, Report, WorkOrder, and related models
│   ├── views.py           # Protocol management and reception
│   ├── views_reports.py   # Report creation and management
│   ├── views_workorder.py  # Work order management
│   ├── forms.py           # Protocol and report forms
│   ├── admin.py           # Protocol admin configuration
│   └── templates/         # Protocol and report templates
├── pages/
│   ├── views.py           # Dashboard views and routing
│   ├── api_views.py       # Dashboard API endpoints
│   └── templates/         # Dashboard templates
├── services/
│   ├── email_service.py    # Email notification wrapper
│   ├── pdf_service.py     # PDF generation service
│   └── workorder_service.py # Work order business logic
└── config/
    ├── settings.py        # Django configuration
    ├── urls.py           # URL routing
    └── celery.py         # Celery configuration
```

### Documentation Structure
```
docs/
├── getting-started/
│   ├── user-roles-summary.md        # Role overview and capabilities
│   ├── system-overview.md            # General system introduction
│   └── basic-navigation.md           # User interface guide
├── user-guides/
│   ├── administrators/                # Admin user guides
│   ├── lab-staff/                   # Lab staff procedures
│   ├── histopathologists/            # Histopathologist guides (TO BE UPDATED)
│   └── veterinarians/                # Veterinarian procedures
├── internal/
│   └── archive/
│       └── planning/
│           └── main-project-docs/
│               └── steps/               # Implementation steps (step-01.md, step-02.md, etc.)
└── common-tasks/                     # General task guides
```

## Current Workflow Processes

### Complete Protocol Lifecycle
1. **Veterinarian** submits protocol → Temporary code generated
2. **Lab Staff** receives sample → Final protocol number assigned
3. **Lab Staff** processes sample → Cassette/slide creation
4. **Histopathologist** creates report → Diagnosis and signature
5. **System** generates work order → Billing and delivery
6. **System** sends notifications → Status updates throughout

### Email Notification Flow
```
Protocol Submissions → Veterinarian confirmation
Sample Reception → Veterinarian notification
Processing Updates → Status notifications
Report Creation → Delivery notification
Work Order Generation → Billing notification
```

## Current Technology Stack

### Backend Technologies
- **Django 5.2.7** - Web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and Celery broker
- **Celery** - Background task processing
- **ReportLab** - PDF generation
- **Django Admin** - Administrative interface

### Frontend Technologies
- **Django Templates** - Server-side rendering
- **TailwindCSS** - CSS framework
- **Vue.js 3** - Interactive components
- **Alpine.js** - Lightweight interactions
- **esbuild** - Asset bundling

### Infrastructure
- **Docker** - Containerized development
- **WhiteNoise** - Static file serving
- **Gunicorn** - WSGI server
- **Redis** - Session storage and caching

## Current Configuration

### Security Features
- Role-based access control
- Email verification for veterinarians
- Account lockout after failed attempts
- Password hashing with modern algorithms
- CSRF protection
- SQL injection protection
- XSS prevention

### Performance Features
- Database connection pooling
- Query optimization with select_related/prefetch_related
- Caching with Redis
- Efficient dashboard API with 2-minute cache
- Optimized database indexes

### Monitoring & Logging
- Authentication audit logging
- Email delivery tracking
- Performance metrics collection
- System health checks
- Error logging and alerting

## Integration Points

### External Systems
- **Email Service** - SMTP configuration for notifications
- **File Storage** - Signature and report PDF storage
- **Payment Processing** - Work order billing (future)

### Internal Integrations
- **Celery** - Asynchronous email processing
- **ReportLab** - PDF generation for reports and work orders
- **QR Code** - Sample label generation

## Key Dependencies

### Required Services
- **PostgreSQL Database** - Primary data storage
- **Redis Server** - Caching and background tasks
- **Email Service** - Notification delivery

### Optional/Future Integrations
- **Object Storage** - S3-compatible file storage
- **Monitoring Service** - Application performance monitoring
- **Backup Service** - Automated database backups

## Current Limitations

### Role Separation Complexity
- Duplicate dashboards for lab staff types
- Separate permission systems causing maintenance overhead
- Artificial barriers between similar roles

### Pending Features
- Analytics and reporting (Step 10)
- System administration interface (Step 12)
- Production email configuration (Step 13)
- Storage and backup systems (Step 14)

## Development Environment Setup

### Local Development
```bash
# Docker-based development
docker compose up --build

# Database management
./run manage migrate
./run manage shell

# Code quality
./run lint          # Ruff linting
./run format         # Ruff formatting
./run quality        # Combined checks

# Testing
./run manage test    # Full test suite
```

### Production Deployment
- Docker containerization
- Gunicorn WSGI server
- Nginx reverse proxy (configurable)
- SSL termination
- Database migrations
- Static file collection

---

**Document Status**: Current state reference
**Last Updated**: With step-16 planning complete
**Next Major Change**: Laboratory Staff Role Consolidation (Step 16)

This document serves as the authoritative reference for understanding the current system state before implementing any changes. All architectural decisions, user flows, and technical specifications are documented here for developer reference.