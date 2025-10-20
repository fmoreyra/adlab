# Step 16: Comprehensive Testing Coverage - PLAN 📋

**Status**: 🚧 **PLANNING PHASE**  
**Target Completion**: 3-4 weeks (Aggressive Timeline)  
**Developer**: AdLab Development Team

---

## 📋 Overview

Comprehensive testing plan to increase test coverage from **71% to 90%+** across the entire system. Focus on poorly-tested view layer, email/Celery tasks, and security (permissions testing). This plan uses a pragmatic testing approach covering critical paths and all permission scenarios.

**Current Coverage**: 71% overall (3,197 lines covered out of 5,197 total)

---

## 🎯 Goals

1. **Increase Overall Coverage**: From 71% to 90%+
2. **Test All View Permissions**: Security-critical access control
3. **Cover Critical Workflows**: Reception, processing, reports, work orders
4. **Test Email System**: Notification preferences, queueing, delivery
5. **Document Testing Patterns**: For future development

---

## 📊 Current State Analysis

### Coverage by Module

| Module | Current Coverage | Lines Uncovered | Priority |
|--------|------------------|-----------------|----------|
| `protocols/views.py` | 32% | 378 lines | 🔴 CRITICAL |
| `protocols/views_workorder.py` | 20% | 222 lines | 🔴 CRITICAL |
| `protocols/views_reports.py` | 58% | 120 lines | 🟡 HIGH |
| `pages/views.py` | 25% | 85 lines | 🔴 CRITICAL |
| `protocols/emails.py` | 42% | 28 lines | 🟡 HIGH |
| `protocols/tasks.py` | 26% | 32 lines | 🟡 HIGH |
| `accounts/views.py` | 73% | 79 lines | 🟢 MEDIUM |
| `protocols/admin.py` | 56% | 187 lines | 🟢 MEDIUM |

### Well-Tested Areas ✅

- **Models**: 95%+ coverage (excellent business logic testing)
- **Forms**: 70%+ coverage (good validation testing)
- **Existing Test Suite**: 158 tests passing

### Critical Gaps 🚨

1. **View Layer**: Very poor coverage (20-32%)
2. **Dashboard Views**: Only 25% coverage
3. **Email System**: 42% coverage (missing preference/queue tests)
4. **Celery Tasks**: 26% coverage (missing retry/error tests)

---

## 🗓️ Implementation Phases

### **Phase 1: Protocol Views Testing (Week 1)**

#### 1.1 Reception Views

**Target File**: `src/protocols/tests.py`  
**Coverage Goal**: `protocols/views.py` lines 635-897 → 85%+

**Views to Test**:
- ✅ `reception_search_view`: GET/POST, valid/invalid codes
- ✅ `reception_confirm_view`: Sample condition validation
- ✅ `reception_detail_view`: Label generation
- ✅ `reception_pending_view`: Protocol filtering, days calculation
- ✅ `reception_history_view`: Log retrieval
- ✅ `reception_label_pdf_view`: PDF generation, QR code validation

**Permission Tests**:
- Non-staff users blocked from all reception views
- Veterinarians cannot access reception functions
- Proper redirect behavior for unauthorized access

#### 1.2 Processing Views

**Target File**: `src/protocols/tests.py`  
**Coverage Goal**: `protocols/views.py` lines 1012-1627 → 85%+

**Views to Test**:
- ✅ `processing_dashboard_view`: Statistics calculation
- ✅ `processing_queue_view`: Filtering by type, queue calculations
- ✅ `protocol_processing_status_view`: Timeline display
- ✅ `cassette_create_view`: Multiple cassette creation
- ✅ `slide_register_view`: Vue.js data handling, JSON validation
- ✅ `slide_update_stage_view`: Stage transitions, logging
- ✅ `slide_update_quality_view`: Quality assessment

**Permission Tests**:
- All processing views restricted to staff only
- Non-staff redirected appropriately

**Estimated Tests**: 40-50 new test cases  
**Estimated Time**: 5 days

---

### **Phase 2: Work Order & Reports Testing (Week 2)**

#### 2.1 Work Order Views

**Target File**: `src/protocols/tests_workorder.py`  
**Coverage Goal**: `protocols/views_workorder.py` → 85%+

**Views to Test**:
- ✅ `workorder_list_view`: Filtering, pagination
- ✅ `workorder_pending_protocols_view`: Grouping by veterinarian
- ✅ `workorder_select_protocols_view`: Protocol selection validation
- ✅ `workorder_create_view`: Service calculation, form validation
- ✅ `workorder_detail_view`: Display logic
- ✅ `workorder_issue_view`: Status transitions
- ✅ `workorder_send_view`: PDF generation, status updates
- ✅ `workorder_pdf_view`: PDF buffer generation

**Permission Tests**:
- All work order views restricted to staff
- PDF generation access control

#### 2.2 Report Views

**Target File**: `src/protocols/tests_reports.py`  
**Coverage Goal**: `protocols/views_reports.py` → 85%+

**Views to Test**:
- ✅ `report_create_view`: Form validation, protocol status checks
- ✅ `report_edit_view`: Draft-only editing, formset handling
- ✅ `report_finalize_view`: PDF generation, email sending
- ✅ `report_pdf_view`: Access control (staff OR owner)
- ✅ `report_send_view`: Email delivery, attachment handling

**Permission Tests**:
- Staff access for creation/editing
- Veterinarian access for viewing their own reports
- PDF download permissions (staff + owner)

**Estimated Tests**: 50-60 new test cases  
**Estimated Time**: 5 days

---

### **Phase 3: Dashboard & Pages Testing (Week 2-3)**

#### 3.1 Dashboard Views

**Target File**: `src/pages/tests.py`  
**Coverage Goal**: `pages/views.py` → 90%+

**Views to Test**:
- ✅ `veterinarian_dashboard`: Statistics, protocol counts, recent protocols
- ✅ `lab_staff_dashboard`: Processing queue, reception counts
- ✅ `histopathologist_dashboard`: Report statistics, pending reports
- ✅ `admin_dashboard`: System statistics, active users
- ✅ `dashboard_view`: Role-based routing logic

**Permission Tests**:
- Each dashboard only accessible by correct role
- Redirects for unauthorized users
- Statistics only show data user has access to

**Estimated Tests**: 30-40 new test cases  
**Estimated Time**: 3 days

---

### **Phase 4: Email & Celery Tasks (Week 3)**

#### 4.1 Email Functions

**Target File**: `src/protocols/test_emails.py` (NEW)  
**Coverage Goal**: `protocols/emails.py` → 90%+

**Test Classes**:

```python
class EmailNotificationTest(TestCase):
    """Test email notification system."""
    
    @patch('protocols.emails.send_email_task.delay')
    def test_send_sample_reception_notification(self, mock_task):
        # Test email queueing, preference checking
        
    @patch('protocols.emails.send_email_task.delay')
    def test_send_protocol_processing_notification(self, mock_task):
        # Test processing notifications
        
    @patch('protocols.emails.send_email_task.delay')
    def test_send_report_ready_notification(self, mock_task):
        # Test report notifications with PDF
        
    @patch('protocols.emails.send_email_task.delay')
    def test_send_work_order_notification(self, mock_task):
        # Test work order notifications
        
    def test_queue_email_respects_preferences(self):
        # Test preference checking logic
        
    def test_alternative_email_handling(self):
        # Test alternative email logic
```

#### 4.2 Celery Tasks

**Target File**: `src/protocols/test_tasks.py` (NEW)  
**Coverage Goal**: `protocols/tasks.py` → 90%+

**Test Classes**:

```python
class CeleryTaskTest(TestCase):
    """Test Celery background tasks."""
    
    @patch('django.core.mail.send_mail')
    def test_send_email_task_success(self, mock_send):
        # Test successful email sending
        
    @patch('django.core.mail.send_mail')
    def test_send_email_task_failure_retry(self, mock_send):
        # Test retry logic on failure
        
    def test_task_logging(self):
        # Test task execution logging
        
    def test_exponential_backoff(self):
        # Test retry backoff strategy
```

**Estimated Tests**: 40-50 new test cases  
**Estimated Time**: 4 days

---

### **Phase 5: Security & Permission Tests (Week 3-4)**

#### 5.1 Comprehensive Security Tests

**Target File**: `src/protocols/test_security.py` (NEW)  
**Coverage Goal**: Complete security audit via tests

**Test Classes**:

```python
class SecurityPermissionTest(TestCase):
    """Comprehensive permission and security tests."""
    
    def test_veterinarian_isolation(self):
        # Vet can only see their own protocols/reports
        
    def test_staff_only_views(self):
        # All staff-only views block non-staff
        
    def test_admin_only_features(self):
        # Admin-only functionality
        
    def test_public_view_access(self):
        # Protocol public detail with UUID
        
    def test_cross_user_access_blocked(self):
        # Vet A cannot access Vet B's data
        
    def test_permission_redirects(self):
        # Proper redirect behavior for all roles
```

**Security Scenarios**:
- Data isolation between veterinarians
- Staff-only view protection
- Admin-only feature protection
- Public view access control
- Cross-user access prevention
- Proper authentication requirements

**Estimated Tests**: 30-40 new test cases  
**Estimated Time**: 3 days

---

### **Phase 6: Accounts & Admin Testing (Week 4)**

#### 6.1 Accounts Views Completion

**Target File**: `src/accounts/tests.py`  
**Coverage Goal**: `accounts/views.py` → 90%+

**Areas to Cover**:
- Password reset confirmation flow (lines 395-456)
- Profile view edge cases (lines 463-479)
- Veterinarian profile editing error cases
- Edge cases and error handling

#### 6.2 Protocols Admin

**Target File**: `src/protocols/test_admin.py` (NEW)  
**Coverage Goal**: `protocols/admin.py` → 85%+

**Test Areas**:
- Admin actions testing
- Custom admin methods
- Filter functionality
- Permissions in admin interface
- Bulk operations
- Admin form validation

**Estimated Tests**: 50-60 new test cases  
**Estimated Time**: 5 days

---

## 📐 Implementation Guidelines

### Test Structure Pattern

Each test file should follow this pattern:

```python
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock

class ViewNameTest(TestCase):
    """Tests for specific_view."""
    
    def setUp(self):
        """Set up test data."""
        # Create users with different roles
        self.vet_user = User.objects.create_user(...)
        self.staff_user = User.objects.create_user(...)
        self.admin_user = User.objects.create_user(...)
        
        # Create test data
        self.protocol = Protocol.objects.create(...)
        
        self.client = Client()
    
    def test_get_request_success(self):
        """Test successful GET request."""
        self.client.login(...)
        response = self.client.get(reverse('view_name'))
        self.assertEqual(response.status_code, 200)
        
    def test_post_request_valid_data(self):
        """Test POST with valid data."""
        self.client.login(...)
        response = self.client.post(reverse('view_name'), data={...})
        self.assertEqual(response.status_code, 302)  # Redirect
        
    def test_post_request_invalid_data(self):
        """Test POST with invalid data."""
        response = self.client.post(reverse('view_name'), data={...})
        self.assertFormError(...)
        
    def test_permission_staff_required(self):
        """Test that staff permission is required."""
        self.client.login(username='vet', password='pass')
        response = self.client.get(reverse('view_name'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
    def test_permission_veterinarian_blocked(self):
        """Test that veterinarians are blocked."""
        self.client.login(username='vet', password='pass')
        response = self.client.get(reverse('view_name'))
        self.assertRedirects(response, expected_url)
```

### Coverage Verification Commands

After each phase, verify coverage:

```bash
# Run tests with coverage
docker-compose exec web python -m coverage run --source='.' manage.py test

# Generate overall report
docker-compose exec web python -m coverage report

# Generate module-specific report
docker-compose exec web python -m coverage report --include='src/protocols/*'

# Generate HTML report for detailed analysis
docker-compose exec web python -m coverage html
```

### Success Metrics by Phase

| Phase | Module | Target Coverage | Tests Added |
|-------|--------|-----------------|-------------|
| 1 | `protocols/views.py` | 85%+ | 40-50 |
| 2 | `views_workorder.py` | 85%+ | 25-30 |
| 2 | `views_reports.py` | 85%+ | 25-30 |
| 3 | `pages/views.py` | 90%+ | 30-40 |
| 4 | `emails.py` | 90%+ | 25-30 |
| 4 | `tasks.py` | 90%+ | 15-20 |
| 5 | Security tests | Complete | 30-40 |
| 6 | `accounts/views.py` | 90%+ | 30-40 |
| 6 | `admin.py` | 85%+ | 20-30 |
| **TOTAL** | **System-wide** | **90%+** | **300-400** |

---

## 🗓️ Timeline Summary

| Week | Focus Areas | Deliverables |
|------|-------------|--------------|
| **Week 1** | Protocol views (reception + processing) | 40-50 tests, 85%+ coverage |
| **Week 2** | Work orders + Reports + Dashboards | 80-100 tests, 85%+ coverage |
| **Week 3** | Email/Tasks + Security tests | 70-90 tests, 90%+ coverage |
| **Week 4** | Accounts + Admin + Buffer + Verification | 50-70 tests, final 90%+ |

**Total Estimated Time**: 3-4 weeks (aggressive timeline)  
**Total New Tests**: 300-400 test cases

---

## 🚫 Out of Scope (Future Phase)

### Integration Tests (Deferred)

End-to-end integration tests are documented but **excluded from current scope**:

**Future File**: `src/protocols/test_integration.py`

```python
class ProtocolWorkflowIntegrationTest(TestCase):
    """End-to-end workflow tests."""
    
    def test_complete_protocol_workflow(self):
        """Test complete workflow: create → submit → receive → process → report."""
        # Multi-step workflow test
        
    def test_work_order_workflow(self):
        """Test work order workflow: ready → created → sent → invoiced."""
        # Complete work order lifecycle
        
    def test_email_workflow(self):
        """Test email notifications throughout workflow."""
        # All email notifications in sequence
```

**Rationale**: Integration tests provide valuable coverage but are time-intensive. Current focus is on unit and functional tests to reach 90% coverage target. Integration tests should be implemented in a future sprint once unit test foundation is solid.

**Future Benefits**:
- Catch integration issues between modules
- Validate complete user workflows
- Test complex state transitions
- Ensure data consistency across operations

---

## 📦 Deliverables

### 1. Test Suite Expansion
- **300-400 new test cases** across all modules
- **90%+ overall coverage** verified by coverage report
- All critical workflows tested

### 2. Security Coverage
- All permission scenarios tested
- Cross-user access prevention verified
- Role-based access control validated

### 3. Documentation
- Test patterns documented for future development
- Coverage reports saved for tracking
- Testing guidelines established

### 4. Infrastructure
- 3 new test files created (`test_emails.py`, `test_tasks.py`, `test_security.py`)
- Enhanced existing test files
- Mock patterns established for external services

---

## 🎯 Success Criteria

### Mandatory Requirements

✅ **Overall coverage reaches 90%+**  
✅ **All view permissions tested**  
✅ **Critical workflows covered**  
✅ **Email system fully tested**  
✅ **All 158 existing tests still pass**

### Quality Standards

- Every test follows documented pattern
- Clear test names and docstrings
- Proper use of mocks for external services
- Setup/teardown properly implemented
- Edge cases and error conditions covered

---

## 📝 Notes

- **Timeline is aggressive**: Requires full-time focus (halt other development)
- **Pragmatic approach**: Focus on critical paths, not exhaustive edge cases
- **Security is priority**: All permission tests are mandatory
- **Integration tests deferred**: To be implemented in future sprint
- **Coverage tool installed**: Already available in Docker container

---

## 🔗 Related Documentation

- [Step 08: Email Notifications](../../STEP_08_COMPLETE.md) - Email system implementation
- [Step 01: Authentication](../../STEP_01_COMPLETE.md) - Auth system with existing tests
- [Step 02: Veterinarian Profiles](../../STEP_02_COMPLETE.md) - Profile system with tests
- [Production Readiness Checklist](../../PRODUCTION_READINESS_CHECKLIST.md) - Overall system health

---

**Next Steps**: Begin Phase 1 implementation with reception views testing.
