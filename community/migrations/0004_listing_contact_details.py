from django.db import migrations, models


def populate_contact_details(apps, schema_editor):
    Listing = apps.get_model("community", "Listing")
    Profile = apps.get_model("community", "Profile")
    profiles = {profile.user_id: profile.phone for profile in Profile.objects.all()}
    for listing in Listing.objects.select_related("seller"):
        listing.contact_email = listing.seller.email or "contact@example.com"
        listing.contact_phone = profiles.get(listing.seller_id) or "Contact seller for phone"
        listing.save(update_fields=["contact_email", "contact_phone"])


class Migration(migrations.Migration):
    dependencies = [("community", "0003_add_free_category")]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="contact_email",
            field=models.EmailField(default="contact@example.com", max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="listing",
            name="contact_phone",
            field=models.CharField(default="Contact seller for phone", max_length=30),
            preserve_default=False,
        ),
        migrations.RunPython(populate_contact_details, migrations.RunPython.noop),
    ]
