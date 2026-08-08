from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0015_lostfound_contact_method_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="phone_verification_code",
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name="profile",
            name="phone_verification_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="phone_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="phone_verified",
            field=models.BooleanField(default=False),
        ),
    ]
