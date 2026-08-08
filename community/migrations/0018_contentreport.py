from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0017_post_moderation_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(choices=[("open", "Open"), ("resolved", "Resolved")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("listing", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="content_reports", to="community.listing")),
                ("lost_found", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="content_reports", to="community.lostfound")),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="content_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="contentreport",
            constraint=models.UniqueConstraint(fields=("reporter", "listing"), name="unique_listing_report_per_user"),
        ),
        migrations.AddConstraint(
            model_name="contentreport",
            constraint=models.UniqueConstraint(fields=("reporter", "lost_found"), name="unique_lostfound_report_per_user"),
        ),
    ]
