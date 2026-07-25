from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("community", "0008_simplify_listing_categories")]

    operations = [
        migrations.AlterField(
            model_name="listing",
            name="category",
            field=models.CharField(
                choices=[
                    ("Free", "Free Stuff"),
                    ("For Sale", "For Sale"),
                    ("Volunteer Service", "Volunteer Service"),
                    ("Community Group", "Community Group"),
                ],
                max_length=30,
            ),
        ),
    ]
