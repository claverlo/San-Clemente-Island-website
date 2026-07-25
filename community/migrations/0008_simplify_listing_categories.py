from django.db import migrations, models


def simplify_categories(apps, schema_editor):
    Listing = apps.get_model("community", "Listing")
    Listing.objects.filter(category="Services").update(category="Volunteer Service")
    Listing.objects.exclude(
        category__in=["Free", "Volunteer Service", "Community Group"]
    ).update(category="For Sale")


class Migration(migrations.Migration):
    dependencies = [("community", "0007_format_existing_phone_numbers")]

    operations = [
        migrations.RunPython(simplify_categories, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="listing",
            name="category",
            field=models.CharField(
                choices=[
                    ("Free", "Free"),
                    ("For Sale", "For Sale"),
                    ("Volunteer Service", "Volunteer Service"),
                    ("Community Group", "Community Group"),
                ],
                max_length=30,
            ),
        ),
    ]
