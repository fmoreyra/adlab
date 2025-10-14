# Optimized version of dashboard API views for better performance

from django.db.models import Count, Q, Avg, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta

class OptimizedDashboardProductivityView:
    """Optimized productivity view to eliminate N+1 queries."""
    
    def _calculate_productivity_metrics_optimized(self, periodo: str) -> Dict:
        """Calculate productivity metrics with optimized queries."""
        now = timezone.now()
        
        # Calculate date range
        if periodo == "semana":
            date_from = now - timedelta(days=7)
        elif periodo == "mes":
            date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif periodo == "año":
            date_from = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            date_from = now - timedelta(days=30)
        
        # SINGLE OPTIMIZED QUERY - eliminates N+1 problem
        histopathologist_data = (
            Report.objects
            .filter(
                status=Report.Status.FINALIZED,
                updated_at__gte=date_from
            )
            .select_related('histopathologist__user', 'protocol')
            .values(
                'histopathologist__user__first_name',
                'histopathologist__user__last_name',
                'histopathologist__user__email'
            )
            .annotate(
                informes_enviados=Count('id'),
                tat_promedio_dias=Avg(
                    Case(
                        When(
                            protocol__reception_date__isnull=False,
                            then=timezone.now().date() - F('protocol__reception_date')
                        ),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            )
            .order_by('-informes_enviados')
        )
        
        # Calculate weekly averages
        weeks = max(1, (now - date_from).days / 7)
        total_reports = sum(item['informes_enviados'] for item in histopathologist_data)
        
        result = []
        for item in histopathologist_data:
            result.append({
                'nombre': f"{item['histopathologist__user__first_name']} {item['histopathologist__user__last_name']}".strip() or item['histopathologist__user__email'],
                'informes_enviados': item['informes_enviados'],
                'promedio_por_semana': round(item['informes_enviados'] / weeks, 2),
                'tat_promedio_dias': round(item['tat_promedio_dias'] or 0, 1)
            })
        
        return {
            'periodo': periodo,
            'histopatologos': result,
            'total_informes': total_reports,
        }


class OptimizedDashboardAgingView:
    """Optimized aging view to reduce Python processing."""
    
    def _calculate_aging_metrics_optimized(self) -> Dict:
        """Calculate aging metrics with database-level processing."""
        now = timezone.now().date()
        
        # Use database aggregation instead of Python loops
        aging_data = (
            Protocol.objects
            .filter(
                status__in=[
                    Protocol.Status.RECEIVED,
                    Protocol.Status.PROCESSING,
                    Protocol.Status.READY,
                ],
                reception_date__isnull=False
            )
            .annotate(
                days_since_reception=now - F('reception_date'),
                age_bucket=Case(
                    When(days_since_reception__lte=3, then=0),
                    When(days_since_reception__lte=7, then=1),
                    When(days_since_reception__lte=14, then=2),
                    default=3,
                    output_field=IntegerField()
                )
            )
            .values('age_bucket')
            .annotate(count=Count('id'))
        )
        
        # Initialize buckets
        aging_buckets = {
            '0_3_dias': 0,
            '4_7_dias': 0,
            '8_14_dias': 0,
            'mas_14_dias': 0,
        }
        
        # Map results
        bucket_names = ['0_3_dias', '4_7_dias', '8_14_dias', 'mas_14_dias']
        for item in aging_data:
            bucket_name = bucket_names[item['age_bucket']]
            aging_buckets[bucket_name] = item['count']
        
        # Get overdue samples with single query
        overdue_protocols = (
            Protocol.objects
            .filter(
                status__in=[
                    Protocol.Status.RECEIVED,
                    Protocol.Status.PROCESSING,
                    Protocol.Status.READY,
                ],
                reception_date__isnull=False
            )
            .select_related('veterinarian__user')
            .annotate(
                days_since_reception=now - F('reception_date'),
                target_days=Case(
                    When(analysis_type='histopathology', then=7),
                    default=3,
                    output_field=IntegerField()
                )
            )
            .filter(days_since_reception__gt=F('target_days'))
            .values(
                'protocol_number',
                'animal_identification',
                'veterinarian__user__first_name',
                'veterinarian__user__last_name',
                'status',
                'days_since_reception'
            )[:10]  # Limit to 10 most overdue
        )
        
        return {
            'por_rango': aging_buckets,
            'protocolos_vencidos': list(overdue_protocols),
        }
