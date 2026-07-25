from django.db import migrations


def format_phone(value):
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return value
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"


def format_existing_numbers(apps, schema_editor):
    Listing = apps.get_model("community", "Listing")
    Profile = apps.get_model("community", "Profile")
    for listing in Listing.objects.all():
        formatted = format_phone(listing.contact_phone)
        if formatted != listing.contact_phone:
            listing.contact_phone = formatted
            listing.save(update_fields=["contact_phone"])
    for profile in Profile.objects.all():
        formatted = format_phone(profile.phone)
        if formatted != profile.phone:
            profile.phone = formatted
            profile.save(update_fields=["phone"])


class Migration(migrations.Migration):
    dependencies = [("community", "0006_listing_images")]
    operations = [migrations.RunPython(format_existing_numbers, migrations.RunPython.noop)]
