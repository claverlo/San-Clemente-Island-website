import uuid
from django.db import migrations, models


def approve_existing_profiles(apps, schema_editor):
    Profile = apps.get_model("community", "Profile")
    for profile in Profile.objects.all():
        profile.verification_token = uuid.uuid4()
        profile.email_verified = True
        if not profile.phone:
            profile.phone = "Phone not provided"
        profile.save(update_fields=["verification_token", "email_verified", "phone"])


class Migration(migrations.Migration):
    dependencies = [("community", "0004_listing_contact_details")]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="verification_token",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="profile",
            name="phone",
            field=models.CharField(max_length=30),
        ),
        migrations.RunPython(approve_existing_profiles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="profile",
            name="verification_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
