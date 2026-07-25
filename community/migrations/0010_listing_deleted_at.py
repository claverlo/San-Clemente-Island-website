from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("community", "0009_rename_free_category_label")]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="deleted_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
