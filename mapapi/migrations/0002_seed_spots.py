from django.db import migrations

STARTER_SPOTS = [
    {"name": "Airport", "lat": 32.88, "lng": -118.48},
    {"name": "Barracks", "lat": 32.91, "lng": -118.51},
    {"name": "Galley", "lat": 32.89, "lng": -118.49},
    {"name": "Gym", "lat": 32.9, "lng": -118.5},
]


def seed_spots(apps, schema_editor):
    Spot = apps.get_model("mapapi", "Spot")
    for spot in STARTER_SPOTS:
        Spot.objects.get_or_create(
            name=spot["name"], defaults={"lat": spot["lat"], "lng": spot["lng"]}
        )


def remove_seed_spots(apps, schema_editor):
    Spot = apps.get_model("mapapi", "Spot")
    Spot.objects.filter(name__in=[s["name"] for s in STARTER_SPOTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("mapapi", "0001_initial")]

    operations = [migrations.RunPython(seed_spots, remove_seed_spots)]
