# Step 08: Email Notifications Integration Plan

## Overview
This document identifies all opportunities for integrating the new Celery-based email notification system (implemented in Step 08) into existing code from Steps 3-7.

## Current Status

### ✅ Already Implemented (Step 08 Core)
1. **Email Infrastructure**
   - `EmailLog` model for tracking
   - `NotificationPreference` model for veterinarian preferences
   - `send_email` Celery task with retry logic
   - Helper functions in `protocols/emails.py`
   - Email templates in `templates/emails/`

2. **Existing Email Code (Needs Migration)**
   - `src/protocols/views.py::_send_reception_email()` - Uses blocking `send_mail()`
   - `src/accounts/views.py` - Email verification and password reset

---

## Integration Opportunities by Step

### 📍 Step 3: Protocol Submission

**File:** `src/protocols/views.py`

#### 1. Protocol Submission Confirmation
**Location:** `protocol_submit_view()` (line ~517)
**Current:** No email sent
**Recommendation:** ✅ **ADD** submission confirmation email

```python
# After line 525 (after status change is logged)
from protocols.emails import queue_email
from protocols.models import EmailLog

# Send submission confirmation
queue_email(
    email_type=EmailLog.EmailType.CUSTOM,
    recipient_email=protocol.veterinarian.email,
    subject=f'Protocolo {protocol.temporary_code} enviado exitosamente',
    context={
        'protocol': protocol,
        'veterinarian': protocol.veterinarian,
        'temporary_code': protocol.temporary_code,
    },
    template_name='emails/protocol_submitted.html',
    protocol=protocol,
    veterinarian=protocol.veterinarian
)
```

**Why:** Veterinarians should receive confirmation that their protocol was successfully submitted with the temporary code.

---

### 📍 Step 4: Sample Reception

**File:** `src/protocols/views.py`

#### 1. ⚠️ Migrate Existing Email to Celery
**Location:** `_send_reception_email()` (line 53) and `reception_confirm_view()` (line 725)
**Current:** Uses blocking `send_mail()` with custom template
**Recommendation:** ✅ **MIGRATE** to use `protocols.emails.send_sample_reception_notification()`

**Current Code:**
```python
def _send_reception_email(protocol):
    # ... 30+ lines of blocking email code ...
    send_mail(...)  # BLOCKING!
```

**Should Be:**
```python
def _send_reception_email(protocol):
    """Send reception confirmation email asynchronously."""
    from protocols.emails import send_sample_reception_notification
    return send_sample_reception_notification(protocol)
```

**Benefits:**
- Non-blocking (async via Celery)
- Automatic retry on failure
- Respects veterinarian preferences
- Tracked in EmailLog
- Centralized template management

---

#### 2. Reception with Discrepancies
**Location:** `reception_confirm_view()` (line ~677)
**Current:** No special email for discrepancies
**Recommendation:** ✅ **ENHANCE** to send special email when discrepancies are found

```python
# After line 684 (after protocol.receive())
if discrepancies:
    # Send special discrepancy notification
    queue_email(
        email_type=EmailLog.EmailType.CUSTOM,
        recipient_email=protocol.veterinarian.email,
        subject=f'Discrepancias encontradas - Protocolo {protocol.protocol_number}',
        context={
            'protocol': protocol,
            'veterinarian': protocol.veterinarian,
            'discrepancies': discrepancies,
            'sample_condition': protocol.get_sample_condition_display(),
        },
        template_name='emails/reception_discrepancies.html',
        protocol=protocol,
        veterinarian=protocol.veterinarian
    )
```

**Why:** Veterinarians need to be immediately notified if there are issues with their samples.

---

#### 3. Admin Bulk Reception
**File:** `src/protocols/admin.py`
**Location:** `ProtocolAdmin.mark_as_received()` (line ~252)
**Current:** No emails sent during bulk admin actions
**Recommendation:** ✅ **ADD** email notifications for bulk receptions

```python
@admin.action(description=_("Mark selected protocols as received"))
def mark_as_received(self, request, queryset):
    count = 0
    for protocol in queryset:
        if protocol.status in [Protocol.Status.SUBMITTED, Protocol.Status.DRAFT]:
            try:
                protocol.receive()
                ProtocolStatusHistory.log_status_change(...)
                
                # Send email notification
                from protocols.emails import send_sample_reception_notification
                send_sample_reception_notification(protocol)
                
                count += 1
            except Exception:
                pass
```

---

### 📍 Step 5: Sample Processing

**File:** `src/protocols/admin.py`

#### 1. Protocol Status Change: PROCESSING
**Location:** `ProtocolAdmin.mark_as_processing()` (line ~278)
**Current:** No email sent
**Recommendation:** ⚠️ **OPTIONAL** - Add if veterinarians want to be notified

```python
@admin.action(description=_("Mark selected protocols as processing"))
def mark_as_processing(self, request, queryset):
    count = queryset.filter(status=Protocol.Status.RECEIVED).update(
        status=Protocol.Status.PROCESSING
    )
    
    for protocol in queryset.filter(status=Protocol.Status.PROCESSING):
        ProtocolStatusHistory.log_status_change(...)
        
        # Send processing notification (respects preferences)
        from protocols.emails import queue_email
        from protocols.models import EmailLog, NotificationPreference
        
        prefs, _ = NotificationPreference.objects.get_or_create(
            veterinarian=protocol.veterinarian
        )
        
        if prefs.should_send('processing'):
            queue_email(
                email_type=EmailLog.EmailType.CUSTOM,
                recipient_email=prefs.get_recipient_email(),
                subject=f'Protocolo {protocol.protocol_number} en procesamiento',
                context={'protocol': protocol, 'veterinarian': protocol.veterinarian},
                template_name='emails/protocol_processing.html',
                protocol=protocol,
                veterinarian=protocol.veterinarian
            )
```

**Why:** Some veterinarians may want status updates, but this is controlled by their preferences (`notify_on_processing`).

---

#### 2. Protocol Status Change: READY
**Location:** `ProtocolAdmin.mark_as_ready()` (line ~300)
**Current:** No email sent
**Recommendation:** ✅ **ADD** - This is important! Samples are ready for report generation.

```python
@admin.action(description=_("Mark selected protocols as ready"))
def mark_as_ready(self, request, queryset):
    count = queryset.filter(status=Protocol.Status.PROCESSING).update(
        status=Protocol.Status.READY
    )
    
    for protocol in queryset.filter(status=Protocol.Status.READY):
        ProtocolStatusHistory.log_status_change(...)
        
        # Notify veterinarian that sample processing is complete
        from protocols.emails import queue_email
        from protocols.models import EmailLog
        
        queue_email(
            email_type=EmailLog.EmailType.CUSTOM,
            recipient_email=protocol.veterinarian.email,
            subject=f'Muestra lista para diagnóstico - Protocolo {protocol.protocol_number}',
            context={'protocol': protocol, 'veterinarian': protocol.veterinarian},
            template_name='emails/protocol_ready.html',
            protocol=protocol,
            veterinarian=protocol.veterinarian
        )
```

**Why:** This signals to veterinarians that their sample has completed processing and diagnosis will begin soon.

---

### 📍 Step 6: Report Generation

**File:** `src/protocols/views_reports.py`

#### 1. ⚠️ Report Finalized - PDF Generated
**Location:** `report_finalize_view()` (line ~483)
**Current:** No email sent
**Recommendation:** ✅ **ADD** - This is the most important notification!

```python
@login_required
@csrf_protect
@require_http_methods(["POST"])
def report_finalize_view(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    # ... existing validation ...
    
    try:
        with transaction.atomic():
            # Generate PDF
            pdf_buffer, pdf_hash = generate_report_pdf(report)
            
            # Save PDF
            pdf_filename = report.generate_pdf_filename()
            pdf_dir = os.path.join(settings.MEDIA_ROOT, "reports")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            with open(pdf_path, "wb") as f:
                f.write(pdf_buffer.getvalue())
            
            # Update report
            report.pdf_path = pdf_path
            report.pdf_hash = pdf_hash
            report.finalize()
            
            # ✅ SEND EMAIL NOTIFICATION WITH PDF
            from protocols.emails import send_report_ready_notification
            send_report_ready_notification(
                protocol=report.protocol,
                report_pdf_path=pdf_path  # Attach PDF if preferences allow
            )
            
            messages.success(request, _("Informe finalizado y enviado por email."))
            return redirect("protocols:report_detail", pk=report.pk)
            
    except Exception as e:
        # ... error handling ...
```

**Why:** This is the primary goal of the entire workflow - veterinarians need to know their report is ready!

---

#### 2. Admin: Mark Report as Sent
**File:** `src/protocols/admin.py`
**Location:** `ReportAdmin.mark_as_sent()` (line ~788)
**Current:** Unclear if emails are sent
**Recommendation:** ✅ **ADD** email notification when manually marking as sent

```python
@admin.action(description=_("Mark as sent"))
def mark_as_sent(self, request, queryset):
    count = 0
    for report in queryset.filter(status=Report.Status.FINALIZED):
        try:
            # Get veterinarian email from form or use default
            report.mark_as_sent(email=report.veterinarian.email)
            
            # Send email notification
            from protocols.emails import send_report_ready_notification
            pdf_path = report.pdf_path if hasattr(report, 'pdf_path') else None
            send_report_ready_notification(
                protocol=report.protocol,
                report_pdf_path=pdf_path
            )
            
            count += 1
        except ValueError:
            pass
```

---

### 📍 Step 7: Work Orders

**File:** `src/protocols/views_workorder.py`

#### 1. Work Order Created
**Location:** `workorder_create_view()` (line ~260-274)
**Current:** No email sent
**Recommendation:** ✅ **ADD** notification when work order is created

```python
try:
    work_order = _create_work_order_with_services(
        form=form,
        protocols=protocols,
        services_data=services_data,
        created_by=request.user,
    )
    
    # ✅ SEND WORK ORDER NOTIFICATION
    from protocols.emails import send_work_order_notification
    
    # Generate PDF first (if not already generated)
    pdf_path = None  # TODO: Generate work order PDF if needed
    
    send_work_order_notification(
        work_order=work_order,
        work_order_pdf_path=pdf_path
    )
    
    messages.success(
        request,
        _("Orden de trabajo {} creada y enviada por email.").format(
            work_order.order_number
        )
    )
    return redirect("protocols:workorder_detail", pk=work_order.pk)
```

**Why:** Veterinarians should receive work orders immediately for billing purposes.

---

#### 2. Work Order Issued (Admin)
**File:** `src/protocols/admin.py`
**Location:** `WorkOrderAdmin.mark_as_issued()` (line ~770)
**Current:** No email sent
**Recommendation:** ✅ **ADD** email when work order is formally issued

```python
@admin.action(description=_("Mark as issued"))
def mark_as_issued(self, request, queryset):
    count = 0
    for wo in queryset.filter(status=WorkOrder.Status.DRAFT):
        try:
            wo.issue()
            
            # Send email notification
            from protocols.emails import send_work_order_notification
            pdf_path = None  # TODO: Get PDF path if available
            send_work_order_notification(
                work_order=wo,
                work_order_pdf_path=pdf_path
            )
            
            count += 1
        except ValueError:
            pass
```

---

#### 3. Work Order Sent to Finance
**Location:** `WorkOrderAdmin.mark_as_sent()` (line ~787)
**Current:** No email sent
**Recommendation:** ⚠️ **OPTIONAL** - Internal notification (not to veterinarian)

This might be an internal status change that doesn't require veterinarian notification.

---

## Priority Implementation Order

### 🔥 Critical (Must Have)
1. **Migrate reception email to Celery** - `views.py::_send_reception_email()`
2. **Report finalized notification** - `views_reports.py::report_finalize_view()`
3. **Work order created notification** - `views_workorder.py::workorder_create_view()`
4. **Admin bulk reception emails** - `admin.py::mark_as_received()`

### ⚠️ Important (Should Have)
5. **Protocol submission confirmation** - `views.py::protocol_submit_view()`
6. **Reception with discrepancies alert** - `views.py::reception_confirm_view()`
7. **Protocol ready for diagnosis** - `admin.py::mark_as_ready()`
8. **Work order issued** - `admin.py::mark_as_issued()`

### 💡 Optional (Nice to Have)
9. **Protocol processing status** - `admin.py::mark_as_processing()` (respects preferences)
10. **Work order sent to finance** - `admin.py::mark_as_sent()` (internal)

---

## New Email Templates Needed

The following templates should be created in `src/templates/emails/`:

1. ✅ `verification.html` - Already exists (migrated)
2. ✅ `password_reset.html` - Already exists (migrated)
3. ✅ `sample_reception.html` - Already created
4. ✅ `report_ready.html` - Already created
5. ✅ `work_order.html` - Already created
6. ✅ `default.html` - Already created
7. ❌ `protocol_submitted.html` - **NEW** - Submission confirmation
8. ❌ `reception_discrepancies.html` - **NEW** - Sample issues alert
9. ❌ `protocol_processing.html` - **NEW** - Processing status update
10. ❌ `protocol_ready.html` - **NEW** - Ready for diagnosis

---

## Email Preferences Integration

The `NotificationPreference` model controls when emails are sent:

```python
class NotificationPreference(models.Model):
    notify_on_reception = BooleanField(default=True)
    notify_on_processing = BooleanField(default=False)  # Opt-in
    notify_on_report_ready = BooleanField(default=True)
    alternative_email = EmailField(blank=True)
    include_attachments = BooleanField(default=True)
```

**Usage Pattern:**
```python
from protocols.models import NotificationPreference

prefs, _ = NotificationPreference.objects.get_or_create(veterinarian=vet)

if prefs.should_send('sample_reception'):
    send_email(...)
```

---

## Testing Checklist

After implementing email notifications:

- [ ] Test email sending with Celery worker running
- [ ] Verify emails appear in `EmailLog` with correct status
- [ ] Test retry logic (simulate email server failure)
- [ ] Verify notification preferences are respected
- [ ] Test alternative email addresses
- [ ] Test with/without PDF attachments
- [ ] Check email templates render correctly in email clients
- [ ] Verify emails are in Spanish with proper formatting
- [ ] Test bulk admin actions (multiple emails queued)
- [ ] Monitor Celery task performance and queue depth

---

## Migration Steps

### Phase 1: Replace Existing Email Code
1. Replace `_send_reception_email()` in `views.py`
2. Update `accounts/views.py` for verification/password reset
3. Update `accounts/admin.py` if it sends emails

### Phase 2: Add Critical Notifications
4. Report finalized email
5. Work order created email
6. Admin bulk reception emails

### Phase 3: Add Important Notifications
7. Protocol submission confirmation
8. Reception discrepancies alert
9. Protocol ready notification
10. Work order issued email

### Phase 4: Add Optional Notifications
11. Processing status updates (opt-in)
12. Any additional custom notifications

---

## Code Quality Checks

Before implementing each notification:
- ✅ Use `protocols.emails.queue_email()` or helper functions
- ✅ Create `EmailLog` entry automatically
- ✅ Respect `NotificationPreference` settings
- ✅ Use proper `EmailType` from `EmailLog.EmailType`
- ✅ Include protocol/work_order foreign keys
- ✅ Use Spanish for all user-facing text (`gettext_lazy`)
- ✅ Follow `.cursorrules` guidelines (module imports, docstrings)
- ✅ Add appropriate logging
- ✅ Handle errors gracefully (don't fail main operation)

---

## Example: Complete Integration

Here's a complete example of how to add an email notification:

```python
# In views.py or admin.py
from protocols.emails import queue_email
from protocols.models import EmailLog, NotificationPreference

def some_view_or_action(request, ...):
    # ... main business logic ...
    
    protocol.status = Protocol.Status.READY
    protocol.save()
    
    # Send email notification
    try:
        # Check preferences (optional, queue_email will handle this for standard types)
        veterinarian = protocol.veterinarian
        prefs, _ = NotificationPreference.objects.get_or_create(
            veterinarian=veterinarian
        )
        
        if prefs.should_send('report_ready'):  # Or just send for custom types
            queue_email(
                email_type=EmailLog.EmailType.CUSTOM,
                recipient_email=prefs.get_recipient_email(),
                subject=f'Status Update - Protocol {protocol.protocol_number}',
                context={
                    'protocol': protocol,
                    'veterinarian': veterinarian,
                    'status': protocol.get_status_display(),
                },
                template_name='emails/protocol_ready.html',
                protocol=protocol,
                veterinarian=veterinarian
            )
            
        logger.info(f"Email queued for protocol {protocol.pk}")
        
    except Exception as e:
        # Log but don't fail the main operation
        logger.error(f"Failed to queue email for protocol {protocol.pk}: {e}")
    
    # Continue with main logic
    messages.success(request, "Operation successful!")
    return redirect(...)
```

---

## Summary

**Total Opportunities Identified:** 10 integration points

**Critical:** 4 integrations  
**Important:** 4 integrations  
**Optional:** 2 integrations  

**New Templates Needed:** 4 additional templates

**Estimated Effort:**
- Phase 1 (Migration): 2-3 hours
- Phase 2 (Critical): 3-4 hours
- Phase 3 (Important): 2-3 hours
- Phase 4 (Optional): 1-2 hours
- Testing: 2-3 hours
- **Total: 10-15 hours**

This integration will complete the email notification system and provide a professional, automated communication channel with veterinarians throughout the entire laboratory workflow.

