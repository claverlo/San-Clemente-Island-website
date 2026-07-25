from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("community", "0002_replace_vehicles_with_other")]

    operations = [
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
                    ("Free", "Free"),
                    ("Other", "Other"),
                ],
                max_length=30,
            ),
        ),
    ]
