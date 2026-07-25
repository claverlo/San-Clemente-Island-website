from django.db import migrations, models


def move_vehicle_listings(apps, schema_editor):
    Listing = apps.get_model("community", "Listing")
    Listing.objects.filter(category="Vehicles").update(category="Other")


class Migration(migrations.Migration):
    dependencies = [("community", "0001_initial")]

    operations = [
        migrations.RunPython(move_vehicle_listings, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="listing",
            name="category",
            field=models.CharField(
                choices=[
                    ("Electronics", "Electronics"),
                    ("Furniture", "Furniture"),
                    ("Outdoor Equipment", "Outdoor Equipment"),
                    ("Services", "Services"),
                    ("Miscellaneous", "Miscellaneous"),
                    ("Other", "Other"),
                ],
                max_length=30,
            ),
        ),
    ]
