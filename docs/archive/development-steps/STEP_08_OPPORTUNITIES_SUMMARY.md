# Email Notification Opportunities - Quick Reference

## 📧 Where to Add Email Notifications (Steps 3-7)

### Step 3: Protocol Submission
| Location | Current | Action | Priority |
|----------|---------|--------|----------|
| `views.py::protocol_submit_view()` line ~517 | ❌ No email | ✅ Add submission confirmation | 🔥 Important |

### Step 4: Sample Reception
| Location | Current | Action | Priority |
|----------|---------|--------|----------|
| `views.py::_send_reception_email()` line 53 | ⚠️ Blocking `send_mail()` | ✅ Migrate to Celery | 🔥 Critical |
| `views.py::reception_confirm_view()` line ~677 | ❌ No discrepancy email | ✅ Add discrepancy alert | 🔥 Important |
| `admin.py::mark_as_received()` line ~252 | ❌ No bulk emails | ✅ Add bulk reception emails | 🔥 Critical |

### Step 5: Sample Processing
| Location | Current | Action | Priority |
|----------|---------|--------|----------|
| `admin.py::mark_as_processing()` line ~278 | ❌ No email | ⚠️ Add opt-in notification | 💡 Optional |
| `admin.py::mark_as_ready()` line ~300 | ❌ No email | ✅ Add ready notification | 🔥 Important |

### Step 6: Report Generation
| Location | Current | Action | Priority |
|----------|---------|--------|----------|
| `views_reports.py::report_finalize_view()` line ~483 | ❌ No email | ✅ Add report ready + PDF | 🔥 Critical |
| `admin.py::ReportAdmin.mark_as_sent()` line ~788 | ❌ No email | ✅ Add sent notification | 🔥 Important |

### Step 7: Work Orders
| Location | Current | Action | Priority |
|----------|---------|--------|----------|
| `views_workorder.py::workorder_create_view()` line ~260 | ❌ No email | ✅ Add work order email | 🔥 Critical |
| `admin.py::mark_as_issued()` line ~770 | ❌ No email | ✅ Add issued notification | 🔥 Important |
| `admin.py::mark_as_sent()` line ~787 | ❌ No email | 💡 Internal only | 💡 Optional |

---

## 📊 Statistics

- **Total Integration Points:** 10
- **Critical (Must Have):** 4
- **Important (Should Have):** 4  
- **Optional (Nice to Have):** 2

---

## 🎯 Priority Queue

### Phase 1: Critical Migrations & Features
1. ✅ Migrate `_send_reception_email()` to use Celery
2. ✅ Add report finalized notification with PDF
3. ✅ Add work order created notification
4. ✅ Add admin bulk reception emails

### Phase 2: Important Features
5. ✅ Add protocol submission confirmation
6. ✅ Add reception discrepancy alerts
7. ✅ Add protocol ready notification
8. ✅ Add work order issued notification

### Phase 3: Optional Features
9. ⚠️ Add processing status updates (opt-in via preferences)
10. 💡 Consider internal work order sent notification

---

## 📝 New Templates Needed

Already Created (Step 08):
- ✅ `verification.html`
- ✅ `password_reset.html`
- ✅ `sample_reception.html`
- ✅ `report_ready.html`
- ✅ `work_order.html`
- ✅ `default.html`

Still Needed:
- ❌ `protocol_submitted.html` - Submission confirmation
- ❌ `reception_discrepancies.html` - Sample issues alert
- ❌ `protocol_processing.html` - Processing status update
- ❌ `protocol_ready.html` - Ready for diagnosis (different from report_ready)

---

## 💡 Key Benefits

### For Veterinarians:
- 📬 Immediate confirmation when protocols are submitted
- 📦 Notification when samples are received
- ⚠️ Instant alerts for sample discrepancies
- 📊 Updates on processing progress (opt-in)
- 📄 Automatic report delivery with PDF attachment
- 💰 Work order notifications for billing

### For Lab:
- ⚡ Non-blocking email delivery (no UI delays)
- 🔄 Automatic retry on failure (3 attempts)
- 📋 Complete audit trail in `EmailLog`
- 🎛️ Centralized preference management
- 🛠️ Easy to add new notification types

---

## 🔧 Implementation Pattern

Every email notification follows this pattern:

```python
from protocols.emails import queue_email
from protocols.models import EmailLog, NotificationPreference

# 1. Perform main business logic
protocol.status = Protocol.Status.READY
protocol.save()

# 2. Queue email asynchronously
try:
    queue_email(
        email_type=EmailLog.EmailType.CUSTOM,
        recipient_email=veterinarian.email,
        subject='Your notification subject',
        context={'protocol': protocol, 'veterinarian': veterinarian},
        template_name='emails/your_template.html',
        protocol=protocol,
        veterinarian=veterinarian
    )
except Exception as e:
    logger.error(f"Failed to queue email: {e}")
    # Don't fail the main operation
```

**Key Points:**
- ✅ Always use `queue_email()` or helper functions
- ✅ Never block the main operation
- ✅ Respect `NotificationPreference` settings
- ✅ Log errors but continue execution
- ✅ Include relevant context for templates
- ✅ Use Spanish for all user-facing text

---

## 📧 Email Flow Map

```
[Protocol Created] 
    └─> ❌ No email (draft state)

[Protocol Submitted] 
    └─> ✅ Confirmation email (NEW)

[Sample Received]
    ├─> ✅ Reception email (MIGRATE TO CELERY)
    └─> ✅ Discrepancy alert (NEW, if issues)

[Processing Started]
    └─> ⚠️ Processing update (OPTIONAL, opt-in)

[Processing Complete - Ready]
    └─> ✅ Ready notification (NEW)

[Report Finalized]
    └─> ✅ Report ready with PDF (ADD)

[Work Order Created]
    └─> ✅ Work order notification (ADD)

[Work Order Issued]
    └─> ✅ Issued notification (ADD)
```

---

## 🧪 Testing Checklist

Before deploying to production:

- [ ] Celery worker is running and consuming tasks
- [ ] Emails appear in `EmailLog` with `QUEUED` → `SENT` status
- [ ] Failed emails show `FAILED` status with error message
- [ ] Retry logic works (test with email server down)
- [ ] `NotificationPreference.notify_on_reception` is respected
- [ ] `NotificationPreference.notify_on_processing` is respected (opt-in)
- [ ] `NotificationPreference.notify_on_report_ready` is respected
- [ ] `alternative_email` field works correctly
- [ ] `include_attachments` field controls PDF delivery
- [ ] Email templates render correctly (HTML + plain text)
- [ ] All text is in Spanish
- [ ] Links in emails work (absolute URLs)
- [ ] PDF attachments open correctly
- [ ] Bulk admin actions queue multiple emails
- [ ] Email delivery doesn't block web requests
- [ ] Admin interface shows email logs correctly
- [ ] Notification preferences admin works

---

## 📚 Related Documentation

- **Step 08 Complete:** `STEP_08_COMPLETE.md` - Core implementation details
- **Integration Plan:** `STEP_08_EMAIL_INTEGRATION_PLAN.md` - Detailed integration guide
- **Email Helper Functions:** `src/protocols/emails.py` - API reference
- **Celery Task:** `src/protocols/tasks.py` - Task implementation
- **Models:** `src/protocols/models.py` - `EmailLog` and `NotificationPreference`
- **Templates:** `src/templates/emails/` - Email templates

---

## 🎯 Next Steps

1. Review this summary and the detailed integration plan
2. Prioritize which notifications to implement first
3. Create any missing email templates
4. Implement Phase 1 (critical migrations)
5. Test thoroughly in development
6. Deploy to staging for user acceptance testing
7. Monitor email logs and Celery worker performance
8. Gather feedback from veterinarians
9. Implement remaining phases based on feedback

---

## 📞 Questions?

If you need clarification on any integration point:
- See detailed code examples in `STEP_08_EMAIL_INTEGRATION_PLAN.md`
- Check existing implementations in `protocols/emails.py`
- Review email templates in `src/templates/emails/`
- Look at the Celery task in `protocols/tasks.py`

