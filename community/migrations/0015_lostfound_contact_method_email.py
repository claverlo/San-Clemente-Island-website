from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0014_lostfound_contact_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="lostfound",
            name="contact_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="lostfound",
            name="contact_method",
            field=models.CharField(choices=[("phone", "Phone"), ("email", "Email")], default="phone", max_length=10),
        ),
    ]
