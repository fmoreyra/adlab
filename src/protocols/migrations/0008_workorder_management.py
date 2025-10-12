# Generated manually for Step 07: Work Order Management

import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_histopathologist'),
        ('protocols', '0007_report_cassetteobservation_reportimage_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Drop the old WorkOrder table
        migrations.DeleteModel(
            name='WorkOrder',
        ),
        
        # Create PricingCatalog model
        migrations.CreateModel(
            name='PricingCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(help_text='Identificador único del servicio', max_length=100, unique=True, verbose_name='tipo de servicio')),
                ('description', models.CharField(help_text='Descripción del servicio', max_length=500, verbose_name='descripción')),
                ('price', models.DecimalField(decimal_places=2, help_text='Precio en USD', max_digits=10, verbose_name='precio')),
                ('valid_from', models.DateField(help_text='Fecha desde la cual este precio es válido', verbose_name='vigente desde')),
                ('valid_until', models.DateField(blank=True, help_text='Fecha hasta la cual este precio es válido', null=True, verbose_name='vigente hasta')),
                ('observations', models.TextField(blank=True, verbose_name='observaciones')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creado el')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='actualizado el')),
            ],
            options={
                'verbose_name': 'catálogo de precios',
                'verbose_name_plural': 'catálogos de precios',
                'ordering': ['service_type'],
            },
        ),
        
        # Create WorkOrderCounter model
        migrations.CreateModel(
            name='WorkOrderCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(help_text='Año para el contador', unique=True, verbose_name='año')),
                ('last_number', models.IntegerField(default=0, help_text='Último número de orden de trabajo asignado', verbose_name='último número')),
            ],
            options={
                'verbose_name': 'contador de orden de trabajo',
                'verbose_name_plural': 'contadores de orden de trabajo',
            },
        ),
        
        # Create new WorkOrder model
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(db_index=True, help_text='Número único de orden de trabajo (ej: OT-2024-001)', max_length=50, unique=True, verbose_name='número de orden')),
                ('issue_date', models.DateField(default=datetime.date.today, help_text='Fecha de emisión de la orden de trabajo', verbose_name='fecha de emisión')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, help_text='Monto total de la orden', max_digits=10, verbose_name='monto total')),
                ('advance_payment', models.DecimalField(decimal_places=2, default=0, help_text='Pago adelantado recibido', max_digits=10, verbose_name='pago adelantado')),
                ('balance_due', models.DecimalField(decimal_places=2, default=0, help_text='Saldo pendiente de pago', max_digits=10, verbose_name='saldo pendiente')),
                ('payment_status', models.CharField(choices=[('pending', 'Pendiente'), ('partial', 'Pagado Parcial'), ('paid', 'Pagado Completo')], default='pending', max_length=20, verbose_name='estado de pago')),
                ('billing_name', models.CharField(blank=True, help_text='Nombre para facturación (si difiere del veterinario)', max_length=200, verbose_name='nombre de facturación')),
                ('cuit_cuil', models.CharField(blank=True, help_text='CUIT o CUIL del cliente', max_length=20, verbose_name='CUIT/CUIL')),
                ('iva_condition', models.CharField(blank=True, choices=[('responsable_inscripto', 'Responsable Inscripto'), ('monotributista', 'Monotributista'), ('exento', 'Exento')], max_length=30, verbose_name='condición IVA')),
                ('pdf_path', models.CharField(blank=True, help_text='Ruta del archivo PDF de la orden', max_length=500, verbose_name='ruta del PDF')),
                ('status', models.CharField(choices=[('draft', 'Borrador'), ('issued', 'Emitida'), ('sent', 'Enviada'), ('invoiced', 'Facturada')], default='draft', max_length=20, verbose_name='estado')),
                ('sent_date', models.DateTimeField(blank=True, help_text='Fecha en que se envió la orden a finanzas', null=True, verbose_name='fecha de envío')),
                ('invoiced_date', models.DateTimeField(blank=True, help_text='Fecha en que se facturó', null=True, verbose_name='fecha de facturación')),
                ('observations', models.TextField(blank=True, verbose_name='observaciones')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='creado el')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='actualizado el')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_work_orders', to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
                ('veterinarian', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='work_orders', to='accounts.veterinarian', verbose_name='veterinario')),
            ],
            options={
                'verbose_name': 'orden de trabajo',
                'verbose_name_plural': 'órdenes de trabajo',
                'ordering': ['-issue_date', '-created_at'],
            },
        ),
        
        # Create WorkOrderService model
        migrations.CreateModel(
            name='WorkOrderService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(help_text='Descripción del servicio', max_length=500, verbose_name='descripción')),
                ('service_type', models.CharField(help_text='Tipo de servicio prestado', max_length=100, verbose_name='tipo de servicio')),
                ('quantity', models.IntegerField(default=1, verbose_name='cantidad')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='precio unitario')),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='subtotal')),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='descuento')),
                ('protocol', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='work_order_services', to='protocols.protocol', verbose_name='protocolo')),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='protocols.workorder', verbose_name='orden de trabajo')),
            ],
            options={
                'verbose_name': 'servicio de orden de trabajo',
                'verbose_name_plural': 'servicios de orden de trabajo',
                'ordering': ['id'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='pricingcatalog',
            index=models.Index(fields=['service_type'], name='protocols_p_service_e29d93_idx'),
        ),
        migrations.AddIndex(
            model_name='pricingcatalog',
            index=models.Index(fields=['valid_from', 'valid_until'], name='protocols_p_valid_f_61a06e_idx'),
        ),
        migrations.AddIndex(
            model_name='workordercounter',
            index=models.Index(fields=['year'], name='protocols_w_year_45c9a3_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['order_number'], name='protocols_w_order_n_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['veterinarian', '-issue_date'], name='protocols_w_veterinary_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['status', '-issue_date'], name='protocols_w_status_g7h8i9_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['-created_at'], name='protocols_w_created_j0k1l2_idx'),
        ),
        migrations.AddIndex(
            model_name='workorderservice',
            index=models.Index(fields=['work_order'], name='protocols_w_work_or_m3n4o5_idx'),
        ),
        migrations.AddIndex(
            model_name='workorderservice',
            index=models.Index(fields=['protocol'], name='protocols_w_protoco_p6q7r8_idx'),
        ),
    ]

