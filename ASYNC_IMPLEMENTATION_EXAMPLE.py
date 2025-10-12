"""
Example implementation of async tasks for PDF generation.
This is a reference implementation showing how to convert blocking PDF operations to async tasks.

To use this, you would:
1. Add the tasks to src/protocols/tasks.py
2. Update the views to call these tasks
3. Add progress tracking UI (optional)
"""

import hashlib
import io
import logging
import os
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from protocols.models import Report, WorkOrder, Protocol
from protocols.emails import send_report_ready_notification

logger = logging.getLogger(__name__)


# =============================================================================
# HIGH PRIORITY #1: Report PDF Generation
# =============================================================================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def generate_and_finalize_report_task(self, report_id, user_id=None):
    """
    Generate report PDF, save it, and send email notification asynchronously.
    
    This task can take 5-10 seconds for complex reports with multiple cassettes.
    By running it async, users get immediate feedback and can continue working.
    
    Args:
        report_id: ID of the Report to finalize
        user_id: ID of the user who initiated finalization (optional)
    
    Returns:
        dict: {'success': bool, 'report_id': int, 'pdf_path': str}
    """
    try:
        # Update task state to show progress
        self.update_state(state='PROGRESS', meta={'step': 'Loading report'})
        
        report = Report.objects.select_related(
            'protocol',
            'veterinarian',
            'histopathologist',
        ).prefetch_related(
            'cassette_observations__cassette',
        ).get(id=report_id)
        
        logger.info(f"Starting PDF generation for report {report_id}")
        
        # Check if report is in correct state
        if report.status != Report.Status.DRAFT:
            raise ValueError(f"Report {report_id} is not in DRAFT status")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'step': 'Generating PDF'})
        
        # Import here to avoid circular imports
        from protocols.views_reports import generate_report_pdf
        
        # Generate PDF (this is the slow part!)
        pdf_buffer, pdf_hash = generate_report_pdf(report)
        
        logger.info(f"PDF generated for report {report_id}, hash: {pdf_hash[:8]}")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'step': 'Saving PDF to disk'})
        
        # Save PDF to file
        pdf_filename = report.generate_pdf_filename()
        pdf_dir = os.path.join(settings.MEDIA_ROOT, "reports")
        os.makedirs(pdf_dir, exist_ok=True)
        
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        logger.info(f"PDF saved to {pdf_path}")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'step': 'Updating database'})
        
        # Update report
        report.pdf_path = pdf_path
        report.pdf_hash = pdf_hash
        report.finalize()  # This method updates status and timestamps
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'step': 'Sending email notification'})
        
        # Send email notification with PDF attachment
        send_report_ready_notification(report, pdf_path)
        
        logger.info(f"Report {report_id} finalized and email sent successfully")
        
        # Clear any cached data for this report
        cache.delete(f"report_pdf_{report_id}")
        
        return {
            'success': True,
            'report_id': report_id,
            'pdf_path': pdf_path,
            'pdf_hash': pdf_hash,
            'finalized_at': timezone.now().isoformat(),
        }
        
    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {'success': False, 'error': 'Report not found'}
        
    except Exception as exc:
        logger.error(f"Error finalizing report {report_id}: {exc}", exc_info=True)
        
        # Update report status to indicate failure
        try:
            report = Report.objects.get(id=report_id)
            # You might want to add an error field to the Report model
            # report.error_message = str(exc)
            # report.save(update_fields=['error_message'])
        except:
            pass
        
        # Re-raise for Celery retry mechanism
        raise


# =============================================================================
# HIGH PRIORITY #2: Work Order PDF Generation with Caching
# =============================================================================

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
)
def generate_workorder_pdf_task(self, work_order_id, force_regenerate=False):
    """
    Generate work order PDF and save to file with caching.
    
    This task generates PDFs on-demand and caches them. Subsequent requests
    will serve the cached PDF instead of regenerating.
    
    Args:
        work_order_id: ID of the WorkOrder
        force_regenerate: Force regeneration even if cached PDF exists
    
    Returns:
        dict: {'success': bool, 'work_order_id': int, 'pdf_path': str}
    """
    try:
        work_order = WorkOrder.objects.select_related(
            'veterinarian__user',
        ).prefetch_related(
            'services__protocol',
        ).get(id=work_order_id)
        
        logger.info(f"Starting PDF generation for work order {work_order_id}")
        
        # Check if PDF already exists and we're not forcing regeneration
        if not force_regenerate and work_order.pdf_path:
            pdf_full_path = os.path.join(settings.MEDIA_ROOT, work_order.pdf_path)
            if os.path.exists(pdf_full_path):
                logger.info(f"PDF already exists for work order {work_order_id}, skipping generation")
                return {
                    'success': True,
                    'work_order_id': work_order_id,
                    'pdf_path': pdf_full_path,
                    'cached': True,
                }
        
        # Import here to avoid circular imports
        from protocols.views_workorder import _generate_workorder_pdf_buffer
        
        # Generate PDF buffer
        self.update_state(state='PROGRESS', meta={'step': 'Generating PDF'})
        pdf_buffer = _generate_workorder_pdf_buffer(work_order)
        
        # Save to file
        self.update_state(state='PROGRESS', meta={'step': 'Saving to disk'})
        workorders_dir = os.path.join(settings.MEDIA_ROOT, "workorders")
        os.makedirs(workorders_dir, exist_ok=True)
        
        filename = work_order.generate_pdf_filename()
        filepath = os.path.join(workorders_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # Update work order with PDF path
        work_order.pdf_path = os.path.join("workorders", filename)
        work_order.save(update_fields=["pdf_path"])
        
        logger.info(f"Work order PDF generated and saved: {filepath}")
        
        # Cache the PDF path for quick lookup
        cache.set(f"workorder_pdf_{work_order_id}", filepath, timeout=3600 * 24)  # 24 hours
        
        return {
            'success': True,
            'work_order_id': work_order_id,
            'pdf_path': filepath,
            'cached': False,
            'generated_at': timezone.now().isoformat(),
        }
        
    except WorkOrder.DoesNotExist:
        logger.error(f"WorkOrder {work_order_id} not found")
        return {'success': False, 'error': 'Work order not found'}
        
    except Exception as exc:
        logger.error(f"Error generating work order PDF {work_order_id}: {exc}", exc_info=True)
        raise


# =============================================================================
# HIGH PRIORITY #3: Reception Label PDF Generation
# =============================================================================

@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_reception_label_pdf_task(self, protocol_id):
    """
    Generate reception label PDF with QR code.
    
    This task pre-generates labels so they're instantly available when needed.
    
    Args:
        protocol_id: ID of the Protocol
    
    Returns:
        dict: {'success': bool, 'protocol_id': int, 'pdf_path': str}
    """
    try:
        from io import BytesIO
        import qrcode
        from django.urls import reverse
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        
        protocol = Protocol.objects.select_related(
            'veterinarian__user',
            'cytology_sample',
            'histopathology_sample',
        ).get(id=protocol_id)
        
        logger.info(f"Starting label PDF generation for protocol {protocol_id}")
        
        if not protocol.protocol_number:
            raise ValueError(f"Protocol {protocol_id} doesn't have a protocol number yet")
        
        # Generate QR code
        self.update_state(state='PROGRESS', meta={'step': 'Generating QR code'})
        
        qr_box_size = 2
        qr = qrcode.QRCode(version=1, box_size=qr_box_size, border=1)
        
        # Create URL using external_id for public access
        protocol_url = f"{settings.SITE_URL}/protocols/public/{protocol.external_id}/"
        qr.add_data(protocol_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR to buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_image = ImageReader(qr_buffer)
        
        # Generate PDF
        self.update_state(state='PROGRESS', meta={'step': 'Creating PDF'})
        
        # 39x20 mm ticket paper configuration
        page_width = 39 * mm
        page_height = 20 * mm
        pagesize = (page_width, page_height)
        qr_size = 12 * mm
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=pagesize)
        
        # Layout
        margin = 1 * mm
        qr_x = margin
        qr_y = margin
        text_x = qr_x + qr_size + 1 * mm
        
        # Protocol number
        p.setFont("Helvetica-Bold", 8)
        protocol_text = protocol.protocol_number[:8]
        p.drawString(text_x, qr_y + qr_size - 2 * mm, protocol_text)
        
        # Animal ID
        p.setFont("Helvetica", 5)
        animal_text = protocol.animal_identification[:10]
        p.drawString(text_x, qr_y + qr_size - 6 * mm, animal_text)
        
        # Species
        species_text = protocol.species[:8]
        p.drawString(text_x, qr_y + qr_size - 9 * mm, species_text)
        
        # Analysis type
        analysis_type = "CT" if protocol.analysis_type == Protocol.AnalysisType.CYTOLOGY else "HP"
        p.drawString(text_x, qr_y + 1 * mm, analysis_type)
        
        # Draw QR code
        p.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        
        p.showPage()
        p.save()
        
        # Save PDF to file
        self.update_state(state='PROGRESS', meta={'step': 'Saving to disk'})
        
        labels_dir = os.path.join(settings.MEDIA_ROOT, "labels")
        os.makedirs(labels_dir, exist_ok=True)
        
        filename = f"label_{protocol.protocol_number.replace(' ', '_')}.pdf"
        filepath = os.path.join(labels_dir, filename)
        
        buffer.seek(0)
        with open(filepath, "wb") as f:
            f.write(buffer.getvalue())
        
        logger.info(f"Label PDF generated: {filepath}")
        
        # Store the path in cache for quick retrieval
        cache.set(f"label_pdf_{protocol_id}", filepath, timeout=3600 * 24 * 7)  # 7 days
        
        return {
            'success': True,
            'protocol_id': protocol_id,
            'pdf_path': filepath,
            'generated_at': timezone.now().isoformat(),
        }
        
    except Protocol.DoesNotExist:
        logger.error(f"Protocol {protocol_id} not found")
        return {'success': False, 'error': 'Protocol not found'}
        
    except Exception as exc:
        logger.error(f"Error generating label PDF for protocol {protocol_id}: {exc}", exc_info=True)
        raise


# =============================================================================
# MEDIUM PRIORITY: Bulk Operations
# =============================================================================

@shared_task(bind=True)
def bulk_update_protocol_status(self, protocol_ids, new_status, user_id, send_notifications=True):
    """
    Update status for multiple protocols asynchronously.
    
    This is useful for admin bulk actions where updating 50+ protocols
    would otherwise block the UI for 30-60 seconds.
    
    Args:
        protocol_ids: List of protocol IDs to update
        new_status: New status value (from Protocol.Status)
        user_id: ID of user making the change
        send_notifications: Whether to send email notifications
    
    Returns:
        dict: {'success': int, 'failed': int, 'results': list}
    """
    from django.contrib.auth import get_user_model
    from protocols.models import ProtocolStatusHistory
    from protocols.emails import send_sample_reception_notification
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'success': 0, 'failed': len(protocol_ids), 'error': 'User not found'}
    
    protocols = Protocol.objects.filter(id__in=protocol_ids)
    total = len(protocol_ids)
    
    success_count = 0
    failed_count = 0
    results = []
    
    for i, protocol in enumerate(protocols):
        try:
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': total,
                    'protocol_id': protocol.id,
                }
            )
            
            # Update status
            old_status = protocol.status
            protocol.status = new_status
            protocol.save(update_fields=["status"])
            
            # Log change
            ProtocolStatusHistory.log_status_change(
                protocol=protocol,
                new_status=new_status,
                changed_by=user,
                description=f"Bulk update from {old_status} to {new_status}"
            )
            
            # Send notifications if requested
            if send_notifications:
                if new_status == Protocol.Status.RECEIVED:
                    send_sample_reception_notification(protocol)
            
            success_count += 1
            results.append({
                'protocol_id': protocol.id,
                'protocol_number': protocol.protocol_number,
                'status': 'success',
            })
            
            logger.info(f"Updated protocol {protocol.id} to status {new_status}")
            
        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            results.append({
                'protocol_id': protocol.id if hasattr(protocol, 'id') else None,
                'status': 'failed',
                'error': error_msg,
            })
            logger.error(f"Error updating protocol {protocol.id}: {e}")
    
    logger.info(f"Bulk status update complete: {success_count} success, {failed_count} failed")
    
    return {
        'success': success_count,
        'failed': failed_count,
        'total': total,
        'results': results,
        'completed_at': timezone.now().isoformat(),
    }


# =============================================================================
# UTILITY: Task Status Checking
# =============================================================================

def get_task_status(task_id):
    """
    Get the status of a running task.
    
    This can be called from views to check task progress.
    
    Args:
        task_id: Celery task ID
    
    Returns:
        dict: Task status information
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    if result.state == 'PENDING':
        return {
            'state': 'PENDING',
            'status': 'Task is waiting to start...'
        }
    elif result.state == 'PROGRESS':
        return {
            'state': 'PROGRESS',
            'status': 'In progress...',
            'meta': result.info,
        }
    elif result.state == 'SUCCESS':
        return {
            'state': 'SUCCESS',
            'status': 'Task completed!',
            'result': result.result,
        }
    elif result.state == 'FAILURE':
        return {
            'state': 'FAILURE',
            'status': 'Task failed',
            'error': str(result.info),
        }
    else:
        return {
            'state': result.state,
            'status': str(result.info),
        }


# =============================================================================
# Example View Updates
# =============================================================================

"""
# In views_reports.py - Update report_finalize_view

@login_required
@csrf_protect
@require_http_methods(["POST"])
def report_finalize_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, _("No tiene permisos para acceder a esta función."))
        return redirect("protocols:protocol_list")

    report = get_object_or_404(Report, pk=pk)

    if report.status != Report.Status.DRAFT:
        messages.error(request, _("Solo se pueden finalizar informes en estado borrador."))
        return redirect("protocols:report_detail", pk=report.pk)

    try:
        # Queue async task
        task = generate_and_finalize_report_task.delay(report.id, request.user.id)
        
        # Store task ID in session for progress tracking
        request.session[f'report_finalize_task_{report.id}'] = task.id
        
        messages.success(
            request,
            _("El informe se está generando. Recibirás una notificación cuando esté listo.")
        )
        return redirect("protocols:report_detail", pk=report.pk)
        
    except Exception as e:
        logger.error(f"Error queueing report finalization {report.pk}: {e}")
        messages.error(
            request,
            _("Error al iniciar la generación del informe. Por favor intente nuevamente.")
        )
        return redirect("protocols:report_edit", pk=report.pk)


# Add a new view to check task status
@login_required
def report_finalize_status_view(request, pk):
    task_id = request.session.get(f'report_finalize_task_{pk}')
    
    if not task_id:
        return JsonResponse({'state': 'NOT_FOUND'})
    
    status = get_task_status(task_id)
    return JsonResponse(status)
"""

