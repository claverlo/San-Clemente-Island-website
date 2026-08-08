from django.db import migrations


def rename_community_group_to_post(apps, schema_editor):
    Listing = apps.get_model("community", "Listing")
    Listing._base_manager.filter(category="Community Group").update(category="Community Post")


class Migration(migrations.Migration):

    dependencies = [
        ("community", "0012_pointofinterest_approved_pointofinterestphotorequest"),
    ]

    operations = [
        migrations.RunPython(rename_community_group_to_post, migrations.RunPython.noop),
    ]
