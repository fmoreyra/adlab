# Generated manually: replace image_path CharField with ImageField (default storage)

from django.db import migrations, models

import protocols.report_media


class Migration(migrations.Migration):
    dependencies = [
        ("protocols", "0017_inapp_notification_announcement_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="reportimage",
            name="image_path",
        ),
        migrations.AddField(
            model_name="reportimage",
            name="image",
            field=models.ImageField(
                help_text="Fotografía microscópica (JPG, PNG o WebP, máx. 10 MB)",
                upload_to=protocols.report_media.report_image_upload_to,
                verbose_name="imagen",
            ),
            preserve_default=False,
        ),
    ]
