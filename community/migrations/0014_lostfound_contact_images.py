from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0013_rename_community_group_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="lostfound",
            name="contact_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="lostfound",
            name="contact_phone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="lostfound",
            name="image_1",
            field=models.ImageField(blank=True, upload_to="lost_found/"),
        ),
        migrations.AddField(
            model_name="lostfound",
            name="image_2",
            field=models.ImageField(blank=True, upload_to="lost_found/"),
        ),
    ]
