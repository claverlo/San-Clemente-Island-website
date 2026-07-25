from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from community.models import Announcement, Event, Listing, LostFound, Profile

class Command(BaseCommand):
    help = "Create sample SCI List content"
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username="demo", defaults={"first_name": "Alex", "last_name": "Morgan", "email": "demo@example.com"})
        if created: user.set_password("DemoPass123!"); user.save()
        Profile.objects.get_or_create(user=user, defaults={"department": "MWR", "phone": "555-0142"})
        listings = [
            ("Island commuter bicycle", "For Sale", "Good", 175, "Reliable 7-speed bike with helmet and lock."),
            ("32-inch LED television", "For Sale", "Like New", 120, "Clean screen, remote included. Great for barracks room."),
            ("Compact desk and chair", "For Sale", "Good", 80, "Sturdy desk with adjustable office chair."),
            ("2012 Jeep Wrangler", "For Sale", "Good", 9800, "Well maintained island vehicle. Service records available."),
            ("Fishing rod bundle", "For Sale", "Like New", 95, "Two rods, reels, tackle box, and basic tackle."),
            ("Moving help", "Volunteer Service", "New", 0, "Available evenings to help load, unload, or move furniture."),
        ]
        for title, category, condition, price, description in listings:
            Listing.objects.get_or_create(title=title, seller=user, defaults={"category": category, "condition": condition, "price": price, "description": description, "location": "Wilson Cove", "contact_email": user.email, "contact_phone": "555-0142"})
        now = timezone.now()
        for title, days, hour, location, category, description in [
            ("Sunset 5K Fun Run", 5, 17, "Wilson Cove Fitness Center", "Fitness", "All ability levels welcome. Check-in begins 30 minutes before the run."),
            ("Outdoor Movie Night", 9, 19, "MWR Recreation Field", "Entertainment", "Bring a chair or blanket. Popcorn and refreshments provided."),
            ("Island Fishing Tournament", 16, 7, "Wilson Cove Marina", "Outdoor Recreation", "Team and individual divisions. Register at the MWR office."),
            ("Trivia Night", 22, 18, "Community Club", "Community", "Teams of up to six compete for MWR prizes."),
        ]:
            Event.objects.get_or_create(title=title, defaults={"date": (now + timedelta(days=days)).replace(hour=hour, minute=0), "location": location, "category": category, "description": description})
        for title, priority, body in [
            ("Water conservation reminder", "Important", "Please continue to observe posted water conservation measures across all housing and work areas."),
            ("MWR fitness center hours updated", "Routine", "The fitness center will open at 0500 Monday through Friday and 0700 on weekends."),
            ("Air terminal check-in guidance", "Important", "Passengers should arrive at least 45 minutes before scheduled departure with required identification."),
        ]: Announcement.objects.get_or_create(title=title, defaults={"priority": priority, "body": body})
        LostFound.objects.get_or_create(item="Black water bottle", user=user, defaults={"kind": "Found", "description": "Insulated bottle with stickers.", "location": "Fitness Center", "date": timezone.localdate()})
        LostFound.objects.get_or_create(item="Set of keys", user=user, defaults={"kind": "Lost", "description": "Three keys on a blue fabric loop.", "location": "Wilson Cove", "date": timezone.localdate() - timedelta(days=2)})
        self.stdout.write(self.style.SUCCESS("Sample data ready. Demo login: demo / DemoPass123!"))
