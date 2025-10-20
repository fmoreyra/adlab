# Generated manually for dashboard performance optimization

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('protocols', '0010_add_temporary_code_counter'),
    ]

    operations = [
        # Add indexes for Protocol model - most frequently queried fields
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_protocol_status_analysis_type ON protocols_protocol(status, analysis_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_protocol_status_analysis_type;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_protocol_reception_date ON protocols_protocol(reception_date) WHERE reception_date IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_protocol_reception_date;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_protocol_submission_date ON protocols_protocol(submission_date) WHERE submission_date IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_protocol_submission_date;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_protocol_status_reception_date ON protocols_protocol(status, reception_date) WHERE reception_date IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_protocol_status_reception_date;",
        ),
        
        # Add indexes for Report model - frequently queried for productivity metrics
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_report_histopathologist_status ON protocols_report(histopathologist_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_report_histopathologist_status;",
        ),
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_report_updated_at_status ON protocols_report(updated_at, status) WHERE status = 'finalized';",
            reverse_sql="DROP INDEX IF EXISTS idx_report_updated_at_status;",
        ),
        
        # Add indexes for Cassette model - for histopathology processing stages
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_cassette_estado ON protocols_cassette(estado);",
            reverse_sql="DROP INDEX IF EXISTS idx_cassette_estado;",
        ),
        
        # Add indexes for Slide model - for histopathology processing stages
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_slide_estado ON protocols_slide(estado);",
            reverse_sql="DROP INDEX IF EXISTS idx_slide_estado;",
        ),
        
        # Add composite index for User model - for histopathologist queries
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS idx_user_role_active ON accounts_user(role, is_active) WHERE role = 'histopatologo';",
            reverse_sql="DROP INDEX IF EXISTS idx_user_role_active;",
        ),
    ]
