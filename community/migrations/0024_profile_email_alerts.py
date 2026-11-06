import uuid
from django.db import migrations, models


def prepare_existing_profiles(apps, schema_editor):
    # Existing members keep posting as before; only new sign-ups have to verify their email.
    Profile = apps.get_model("community", "Profile")
    for profile in Profile.objects.all():
        profile.alerts_token = uuid.uuid4()
        profile.email_verified = True
        profile.save(update_fields=["alerts_token", "email_verified"])


class Migration(migrations.Migration):
    dependencies = [("community", "0023_chat_message")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="alert_categories",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="profile",
            name="alerts_token",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(prepare_existing_profiles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="profile",
            name="alerts_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
