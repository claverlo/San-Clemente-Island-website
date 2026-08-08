from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0016_profile_phone_verification_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="moderation_notes",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="listing",
            name="moderation_status",
            field=models.CharField(
                choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="lostfound",
            name="moderation_notes",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="lostfound",
            name="moderation_status",
            field=models.CharField(
                choices=[("pending", "Pending review"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunSQL(
            "UPDATE community_listing SET moderation_status = 'approved' WHERE moderation_status = 'pending'",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "UPDATE community_lostfound SET moderation_status = 'approved' WHERE moderation_status = 'pending'",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
