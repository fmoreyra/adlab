# Async Implementation Guide - Step by Step

This guide walks you through implementing the async improvements identified in the analysis.

---

## 📋 Pre-Implementation Checklist

- [x] Celery is configured and running
- [x] Redis/RabbitMQ message broker is working
- [x] Email async task is already working
- [ ] Review the analysis documents
- [ ] Plan maintenance window for deployment
- [ ] Set up monitoring (Flower recommended)

---

## 🎯 Phase 1: Report PDF Generation (Priority #1)

**Time:** 2-3 hours  
**Impact:** Saves 5-8 seconds per report finalization  
**Risk:** Low (isolated change)

### Step 1.1: Add Task to `src/protocols/tasks.py`

```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_and_finalize_report_task(self, report_id, user_id=None):
    """Generate report PDF and finalize asynchronously."""
    try:
        from protocols.models import Report
        from protocols.views_reports import generate_report_pdf
        from protocols.emails import send_report_ready_notification
        import os
        from django.conf import settings
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'step': 'Loading report'})
        
        report = Report.objects.select_related(
            'protocol', 'veterinarian', 'histopathologist'
        ).prefetch_related(
            'cassette_observations__cassette'
        ).get(id=report_id)
        
        if report.status != Report.Status.DRAFT:
            raise ValueError(f"Report {report_id} is not in DRAFT status")
        
        # Generate PDF
        self.update_state(state='PROGRESS', meta={'step': 'Generating PDF'})
        pdf_buffer, pdf_hash = generate_report_pdf(report)
        
        # Save to file
        self.update_state(state='PROGRESS', meta={'step': 'Saving PDF'})
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
        
        # Send notification
        self.update_state(state='PROGRESS', meta={'step': 'Sending email'})
        send_report_ready_notification(report, pdf_path)
        
        logger.info(f"Report {report_id} finalized successfully")
        
        return {
            'success': True,
            'report_id': report_id,
            'pdf_path': pdf_path,
        }
        
    except Exception as exc:
        logger.error(f"Error finalizing report {report_id}: {exc}", exc_info=True)
        raise
```

### Step 1.2: Update `src/protocols/views_reports.py`

Find the `report_finalize_view` function (around line 524) and replace it with:

```python
@login_required
@csrf_protect
@require_http_methods(["POST"])
def report_finalize_view(request, pk):
    """Finalize report and generate PDF asynchronously."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    report = get_object_or_404(Report, pk=pk)

    if report.status != Report.Status.DRAFT:
        messages.error(
            request,
            _("Solo se pueden finalizar informes en estado borrador.")
        )
        return redirect("protocols:report_detail", pk=report.pk)

    try:
        # Import task
        from protocols.tasks import generate_and_finalize_report_task
        
        # Queue async task
        task = generate_and_finalize_report_task.delay(report.id, request.user.id)
        
        # Store task ID for progress tracking (optional)
        request.session[f'report_finalize_task_{report.id}'] = task.id
        
        messages.success(
            request,
            _("El informe se está generando en segundo plano. "
              "Recibirá una notificación por email cuando esté listo.")
        )
        return redirect("protocols:report_detail", pk=report.pk)
        
    except Exception as e:
        logger.error(f"Error queueing report finalization {report.pk}: {e}")
        messages.error(
            request,
            _("Error al iniciar la generación del informe. Por favor intente nuevamente.")
        )
        return redirect("protocols:report_edit", pk=report.pk)
```

### Step 1.3: Test

```bash
# Terminal 1: Start Celery worker
cd laboratory-system
celery -A config worker -l info

# Terminal 2: Run Django dev server
./run

# Test:
# 1. Create a draft report
# 2. Click "Finalize"
# 3. Should see immediate success message
# 4. Check Celery logs for PDF generation
# 5. Verify PDF is created and email is sent
```

---

## 🎯 Phase 2: Work Order PDF Caching (Priority #2)

**Time:** 1-2 hours  
**Impact:** 20x faster for cached PDFs  
**Risk:** Low

### Step 2.1: Add Task to `src/protocols/tasks.py`

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_workorder_pdf_task(self, work_order_id, force_regenerate=False):
    """Generate work order PDF with caching."""
    try:
        from protocols.models import WorkOrder
        from protocols.views_workorder import _generate_workorder_pdf_buffer
        import os
        from django.conf import settings
        from django.core.cache import cache
        
        work_order = WorkOrder.objects.select_related(
            'veterinarian__user',
        ).prefetch_related(
            'services__protocol',
        ).get(id=work_order_id)
        
        # Check if PDF already exists
        if not force_regenerate and work_order.pdf_path:
            pdf_full_path = os.path.join(settings.MEDIA_ROOT, work_order.pdf_path)
            if os.path.exists(pdf_full_path):
                logger.info(f"PDF already exists for work order {work_order_id}")
                return {'success': True, 'cached': True, 'pdf_path': pdf_full_path}
        
        # Generate PDF
        self.update_state(state='PROGRESS', meta={'step': 'Generating PDF'})
        pdf_buffer = _generate_workorder_pdf_buffer(work_order)
        
        # Save to file
        workorders_dir = os.path.join(settings.MEDIA_ROOT, "workorders")
        os.makedirs(workorders_dir, exist_ok=True)
        
        filename = work_order.generate_pdf_filename()
        filepath = os.path.join(workorders_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # Update work order
        work_order.pdf_path = os.path.join("workorders", filename)
        work_order.save(update_fields=["pdf_path"])
        
        # Cache for 24 hours
        cache.set(f"workorder_pdf_{work_order_id}", filepath, timeout=86400)
        
        logger.info(f"Work order PDF generated: {filepath}")
        
        return {'success': True, 'cached': False, 'pdf_path': filepath}
        
    except Exception as exc:
        logger.error(f"Error generating work order PDF {work_order_id}: {exc}")
        raise
```

### Step 2.2: Update `src/protocols/views_workorder.py`

Replace `workorder_pdf_view` function (around line 554) with:

```python
@login_required
def workorder_pdf_view(request, pk):
    """Generate and serve work order PDF (with caching)."""
    if not request.user.is_staff:
        messages.error(
            request,
            _("No tiene permisos para acceder a esta función.")
        )
        return redirect("protocols:protocol_list")

    work_order = get_object_or_404(
        WorkOrder.objects.select_related('veterinarian__user')
                        .prefetch_related('services__protocol'),
        pk=pk
    )

    # Check if PDF already exists
    if work_order.pdf_path:
        pdf_full_path = os.path.join(settings.MEDIA_ROOT, work_order.pdf_path)
        if os.path.exists(pdf_full_path):
            # Serve cached PDF
            return FileResponse(
                open(pdf_full_path, "rb"),
                content_type="application/pdf",
                as_attachment=False,
                filename=work_order.generate_pdf_filename(),
            )
    
    # PDF doesn't exist - check if generation is in progress
    from django.core.cache import cache
    task_id = cache.get(f"workorder_pdf_task_{work_order.id}")
    
    if task_id:
        # Generation in progress
        messages.info(
            request,
            _("El PDF se está generando. Por favor recargue la página en unos segundos.")
        )
        return redirect("protocols:workorder_detail", pk=work_order.pk)
    
    # Start PDF generation
    from protocols.tasks import generate_workorder_pdf_task
    task = generate_workorder_pdf_task.delay(work_order.id)
    
    # Store task ID to prevent duplicate generation
    cache.set(f"workorder_pdf_task_{work_order.id}", task.id, timeout=300)
    
    messages.info(
        request,
        _("Generando PDF... Por favor recargue la página en unos segundos.")
    )
    return redirect("protocols:workorder_detail", pk=work_order.pk)
```

### Step 2.3: Pre-generate PDFs on Work Order Creation

Update `workorder_create_view` (around line 237):

```python
# After work order creation (line ~317):
work_order = _create_work_order_with_services(...)

# Queue PDF generation
from protocols.tasks import generate_workorder_pdf_task
generate_workorder_pdf_task.delay(work_order.id)

# Send notification
_send_work_order_notification(work_order)
```

---

## 🎯 Phase 3: Reception Label Pre-generation (Priority #3)

**Time:** 1 hour  
**Impact:** Instant label generation  
**Risk:** Very Low

### Step 3.1: Add Task to `src/protocols/tasks.py`

```python
@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_reception_label_pdf_task(self, protocol_id):
    """Generate reception label PDF with QR code."""
    try:
        from protocols.models import Protocol
        from io import BytesIO
        import qrcode
        from django.urls import reverse
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from django.conf import settings
        import os
        
        protocol = Protocol.objects.get(id=protocol_id)
        
        if not protocol.protocol_number:
            raise ValueError(f"Protocol {protocol_id} doesn't have a protocol number")
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        protocol_url = f"{settings.SITE_URL}/protocols/public/{protocol.external_id}/"
        qr.add_data(protocol_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_image = ImageReader(qr_buffer)
        
        # Create PDF
        page_width = 39 * mm
        page_height = 20 * mm
        qr_size = 12 * mm
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        
        # Layout
        margin = 1 * mm
        qr_x = margin
        qr_y = margin
        text_x = qr_x + qr_size + 1 * mm
        
        # Add text and QR code (copy from existing implementation)
        p.setFont("Helvetica-Bold", 8)
        p.drawString(text_x, qr_y + qr_size - 2 * mm, protocol.protocol_number[:8])
        
        p.setFont("Helvetica", 5)
        p.drawString(text_x, qr_y + qr_size - 6 * mm, protocol.animal_identification[:10])
        p.drawString(text_x, qr_y + qr_size - 9 * mm, protocol.species[:8])
        
        analysis_type = "CT" if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY else "HP"
        p.drawString(text_x, qr_y + 1 * mm, analysis_type)
        
        p.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        p.showPage()
        p.save()
        
        # Save to file
        labels_dir = os.path.join(settings.MEDIA_ROOT, "labels")
        os.makedirs(labels_dir, exist_ok=True)
        
        filename = f"label_{protocol.protocol_number.replace(' ', '_')}.pdf"
        filepath = os.path.join(labels_dir, filename)
        
        buffer.seek(0)
        with open(filepath, "wb") as f:
            f.write(buffer.getvalue())
        
        # Cache for 7 days
        from django.core.cache import cache
        cache.set(f"label_pdf_{protocol_id}", filepath, timeout=604800)
        
        logger.info(f"Label PDF generated: {filepath}")
        return {'success': True, 'pdf_path': filepath}
        
    except Exception as exc:
        logger.error(f"Error generating label PDF {protocol_id}: {exc}")
        raise
```

### Step 3.2: Update `reception_confirm_view` in `src/protocols/views.py`

Around line 810, after successful reception:

```python
# After reception is complete
messages.success(request, ...)

# Queue label generation
from protocols.tasks import generate_reception_label_pdf_task
generate_reception_label_pdf_task.delay(protocol.pk)

return redirect("protocols:reception_detail", pk=protocol.pk)
```

### Step 3.3: Update `reception_label_pdf_view` in `src/protocols/views.py`

Replace the function (around line 901):

```python
@login_required
def reception_label_pdf_view(request, pk):
    """Serve pre-generated label PDF."""
    if not request.user.is_staff:
        messages.error(request, _("No tiene permisos para acceder a esta función."))
        return redirect("home")

    protocol = get_object_or_404(Protocol, pk=pk)
    
    if not protocol.protocol_number:
        messages.error(request, _("Este protocolo aún no tiene número asignado."))
        return redirect("protocols:reception_search")
    
    # Check cache first
    from django.core.cache import cache
    cached_path = cache.get(f"label_pdf_{protocol.id}")
    
    if cached_path and os.path.exists(cached_path):
        # Serve cached PDF
        return FileResponse(
            open(cached_path, "rb"),
            as_attachment=True,
            filename=f"label_{protocol.protocol_number.replace(' ', '_')}.pdf",
        )
    
    # Check if file exists in media directory
    labels_dir = os.path.join(settings.MEDIA_ROOT, "labels")
    filename = f"label_{protocol.protocol_number.replace(' ', '_')}.pdf"
    filepath = os.path.join(labels_dir, filename)
    
    if os.path.exists(filepath):
        # Serve existing PDF
        cache.set(f"label_pdf_{protocol.id}", filepath, timeout=604800)
        return FileResponse(
            open(filepath, "rb"),
            as_attachment=True,
            filename=filename,
        )
    
    # PDF not generated yet - queue generation
    from protocols.tasks import generate_reception_label_pdf_task
    generate_reception_label_pdf_task.delay(protocol.id)
    
    messages.info(
        request,
        _("Generando etiqueta... Por favor recargue en unos segundos.")
    )
    return redirect("protocols:reception_detail", pk=protocol.pk)
```

---

## 🧪 Testing Checklist

### Report Finalization
- [ ] Create draft report
- [ ] Click finalize
- [ ] Verify immediate response (<1 second)
- [ ] Check Celery logs for task execution
- [ ] Verify PDF is generated
- [ ] Verify email is sent
- [ ] Test with complex report (multiple cassettes)

### Work Order PDF
- [ ] Create work order
- [ ] View PDF (should queue generation)
- [ ] Refresh page - PDF should be served
- [ ] View same PDF again (should be instant)
- [ ] Verify caching works
- [ ] Test with different work orders

### Reception Labels
- [ ] Receive a protocol
- [ ] View label (should be instant if pre-generated)
- [ ] Verify QR code works
- [ ] Test label printing

---

## 📊 Monitoring

### Celery Flower Setup

```bash
# Install Flower
pip install flower

# Start Flower
celery -A config flower --port=5555

# Access at: http://localhost:5555
```

### Check Task Status

```python
# In Django shell
from celery.result import AsyncResult

task_id = 'your-task-id-here'
result = AsyncResult(task_id)

print(f"State: {result.state}")
print(f"Info: {result.info}")
```

---

## 🚀 Deployment

### Pre-Deployment

1. **Test in development** ✓
2. **Review Celery worker configuration**
3. **Ensure sufficient disk space for PDFs**
4. **Plan rollback strategy**

### Deployment Steps

```bash
# 1. Deploy code
git pull origin main

# 2. Install any new dependencies
pip install -r requirements.txt

# 3. Restart Celery workers
sudo systemctl restart celery-worker

# 4. Restart web server
sudo systemctl restart gunicorn

# 5. Monitor logs
tail -f /var/log/celery/worker.log
tail -f /var/log/gunicorn/error.log
```

### Post-Deployment

- [ ] Monitor Celery tasks in Flower
- [ ] Check error logs
- [ ] Test all three features
- [ ] Monitor disk space
- [ ] Check performance metrics

---

## 🐛 Troubleshooting

### PDFs Not Generating

```bash
# Check Celery worker status
celery -A config inspect active

# Check Celery logs
tail -f /var/log/celery/worker.log

# Test task manually
python manage.py shell
>>> from protocols.tasks import generate_and_finalize_report_task
>>> result = generate_and_finalize_report_task.delay(report_id=1)
>>> print(result.get())
```

### Tasks Stuck in Queue

```bash
# Purge queue (CAREFUL!)
celery -A config purge

# Restart workers
sudo systemctl restart celery-worker
```

### Cache Issues

```python
# Clear specific cache
from django.core.cache import cache
cache.delete('workorder_pdf_1')

# Clear all caches
cache.clear()
```

---

## 📈 Performance Monitoring

### Metrics to Track

1. **Task Duration**
   - Report generation time
   - Work order PDF generation time
   - Label generation time

2. **Success Rate**
   - Successful tasks vs failed tasks
   - Retry counts

3. **Queue Length**
   - Number of pending tasks
   - Peak queue times

4. **User Experience**
   - Page load times
   - User complaints/feedback

---

## 🎉 Success Criteria

After implementation, you should see:

- ✅ Report finalization responds in < 1 second
- ✅ Work order PDFs serve instantly after first generation
- ✅ Reception labels available immediately
- ✅ No user complaints about slow PDF generation
- ✅ Celery workers processing tasks smoothly
- ✅ No task failures (< 1% failure rate acceptable)

---

## 📝 Next Steps (Optional Enhancements)

1. **Progress UI** - Show task progress in browser
2. **Bulk operations** - Implement Phase 4 (bulk admin actions)
3. **Scheduled tasks** - Daily reports, cleanup tasks
4. **WebSocket notifications** - Real-time updates when PDFs ready

---

*Implementation guide version 1.0*
*Last updated: October 12, 2025*

