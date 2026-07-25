from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Listing, ListingImage, PointOfInterest, PointOfInterestPhotoRequest, Profile

class CommunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sailor", password="testpass123")
        Profile.objects.create(user=self.user, phone="555-555-0100", email_verified=True)
        self.listing = Listing.objects.create(seller=self.user, title="Bike", description="Good bike", price=100, category="For Sale", condition="Good", contact_email="seller@example.com", contact_phone="555-555-0100")
    def test_public_pages(self):
        for name in ["home", "marketplace", "events", "announcements", "lost_found", "emergency"]: self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_homepage_has_local_map_preview(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "https://www.google.com/maps")
        self.assertContains(response, 'data-react-map-root="true"')

    def test_homepage_has_react_map_container(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'data-react-map-root="true"')

    def test_map_page_loads(self):
        response = self.client.get(reverse("map"))
        self.assertContains(response, "Explore the island")

    def test_map_page_has_local_interactive_map(self):
        response = self.client.get(reverse("map"))
        self.assertNotContains(response, "https://www.google.com/maps")
        self.assertContains(response, 'data-react-map-root="true"')
        self.assertContains(response, "Click the map")

    def test_admin_can_create_point_of_interest(self):
        admin = User.objects.create_user("admin", password="adminpass123", is_staff=True, is_superuser=True)
        self.client.login(username="admin", password="adminpass123")
        response = self.client.post(reverse("poi_create"), {
            "title": "Dockside cafe",
            "description": "Great place to meet up.",
            "latitude": "33.0",
            "longitude": "-118.4",
        })
        self.assertRedirects(response, reverse("map"))
        self.assertTrue(PointOfInterest.objects.filter(title="Dockside cafe").exists())

    def test_admin_can_create_point_of_interest_from_map_click_without_title(self):
        admin = User.objects.create_user("admin", password="adminpass123", is_staff=True, is_superuser=True)
        self.client.login(username="admin", password="adminpass123")
        response = self.client.post(reverse("poi_create"), {
            "description": "Added from the map preview.",
            "latitude": "33.123456",
            "longitude": "-118.654321",
        })
        self.assertRedirects(response, reverse("map"))
        poi = PointOfInterest.objects.get(latitude=33.123456, longitude=-118.654321)
        self.assertTrue(poi.title.startswith("Point of interest at"))

    def test_phone_registered_user_can_request_photo_approval(self):
        self.client.login(username="sailor", password="testpass123")
        poi = PointOfInterest.objects.create(title="Dock", description="Test", latitude=33.0, longitude=-118.4)
        response = self.client.post(reverse("poi_photo_request"), {
            "poi_id": poi.pk,
            "caption": "Fresh photo for review",
            "image": self.photo("poi-request.gif"),
        })
        self.assertRedirects(response, reverse("map"))
        self.assertTrue(PointOfInterestPhotoRequest.objects.filter(poi=poi, user=self.user, status="pending").exists())

    def test_map_page_shows_pending_requests_for_admin(self):
        admin = User.objects.create_user("admin", password="adminpass123", is_staff=True, is_superuser=True)
        poi = PointOfInterest.objects.create(title="Dock", description="Test", latitude=33.0, longitude=-118.4)
        PointOfInterestPhotoRequest.objects.create(poi=poi, user=self.user, caption="Need review", image=self.photo("pending.gif"))
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse("map"))
        self.assertContains(response, "Pending approval")

    def test_admin_can_approve_photo_request(self):
        admin = User.objects.create_user("admin", password="adminpass123", is_staff=True, is_superuser=True)
        poi = PointOfInterest.objects.create(title="Dock", description="Test", latitude=33.0, longitude=-118.4)
        request = PointOfInterestPhotoRequest.objects.create(poi=poi, user=self.user, caption="Need review", image=self.photo("approve.gif"))
        self.client.login(username="admin", password="adminpass123")
        response = self.client.post(reverse("poi_request_decision", args=[request.pk]), {"decision": "approved"})
        self.assertRedirects(response, reverse("map"))
        request.refresh_from_db()
        self.assertEqual(request.status, "approved")
        poi.refresh_from_db()
        self.assertTrue(poi.image)
    def test_marketplace_search(self):
        response = self.client.get(reverse("marketplace"), {"q": "Bike"}); self.assertContains(response, "Bike")
    def test_create_requires_login(self): self.assertEqual(self.client.get(reverse("listing_create")).status_code, 302)
    def test_owner_can_edit(self):
        self.client.login(username="sailor", password="testpass123"); self.assertEqual(self.client.get(reverse("listing_edit", args=[self.listing.pk])).status_code, 200)
    def test_logged_in_user_can_post_listing(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Desk lamp", "category": "For Sale", "condition": "Good",
            "price": "25.00", "location": "Wilson Cove", "description": "Works well.",
            "contact_email": "seller@example.com", "contact_phone": "555-555-0100",
        })
        listing = Listing.objects.get(title="Desk lamp")
        self.assertRedirects(response, reverse("listing_detail", args=[listing.pk]))
        self.assertEqual(listing.seller, self.user)

    def test_listing_shows_direct_contact_details(self):
        response = self.client.get(self.listing.get_absolute_url())
        self.assertContains(response, "seller@example.com")
        self.assertContains(response, "555-555-0100")
        self.assertContains(response, "listing-safety-ribbon")
        self.assertNotContains(response, "online shopping store")

    def test_missing_contact_details_show_error_summary(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Chair", "category": "For Sale", "condition": "Good",
            "price": "20.00", "location": "Wilson Cove", "description": "A chair.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your listing was not posted")
        self.assertContains(response, "Seller contact email")
        self.assertContains(response, "Seller contact phone number")

    def test_admin_can_delete_another_users_listing(self):
        admin = User.objects.create_user("adminuser", password="adminpass123", is_staff=True)
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.post(reverse("listing_delete", args=[self.listing.pk]))
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(Listing.objects.filter(pk=self.listing.pk).exists())
        deleted_listing = Listing.all_objects.get(pk=self.listing.pk)
        self.assertIsNotNone(deleted_listing.deleted_at)
        deleted_listing.restore()
        self.assertTrue(Listing.objects.filter(pk=self.listing.pk).exists())

    def test_regular_user_cannot_delete_another_users_listing(self):
        other = User.objects.create_user("otheruser", password="otherpass123")
        self.client.login(username="otheruser", password="otherpass123")
        response = self.client.post(reverse("listing_delete", args=[self.listing.pk]))
        self.assertRedirects(response, self.listing.get_absolute_url())
        self.assertTrue(Listing.objects.filter(pk=self.listing.pk).exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_registration_requires_phone_and_email_verification(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com", "phone": "555-555-0199",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("dashboard"))
        profile = Profile.objects.get(user__username="newuser")
        self.assertEqual(profile.phone, "555-555-0199")
        self.assertFalse(profile.email_verified)
        self.assertRedirects(self.client.get(reverse("listing_create")), reverse("dashboard"))
        self.client.get(reverse("verify_email", args=[profile.verification_token]))
        profile.refresh_from_db()
        self.assertTrue(profile.email_verified)

    def photo(self, name):
        # Valid transparent 1x1 GIF used to exercise Django's image validation.
        content = bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b")
        return SimpleUploadedFile(name, content, content_type="image/gif")

    def test_listing_accepts_four_photos(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Four photo item", "category": "For Sale", "condition": "Good",
            "price": "10.00", "location": "Wilson Cove", "description": "Four views.",
            "contact_email": "seller@example.com", "contact_phone": "555-555-0100",
            "photos": [self.photo(f"photo-{number}.gif") for number in range(4)],
        })
        listing = Listing.objects.get(title="Four photo item")
        self.assertRedirects(response, listing.get_absolute_url())
        self.assertEqual(ListingImage.objects.filter(listing=listing).count(), 4)

    def test_listing_rejects_more_than_four_photos(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Too many photos", "category": "For Sale", "condition": "Good",
            "price": "10.00", "location": "Wilson Cove", "description": "Five views.",
            "contact_email": "seller@example.com", "contact_phone": "555-555-0100",
            "photos": [self.photo(f"extra-{number}.gif") for number in range(5)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no more than 4 photos")
        self.assertFalse(Listing.objects.filter(title="Too many photos").exists())

    def test_listing_phone_is_saved_with_dashes(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Formatted phone", "category": "For Sale", "condition": "Good",
            "price": "10.00", "location": "Wilson Cove", "description": "Phone test.",
            "contact_email": "seller@example.com", "contact_phone": "(808) 348-5584",
        })
        listing = Listing.objects.get(title="Formatted phone")
        self.assertRedirects(response, listing.get_absolute_url())
        self.assertEqual(listing.contact_phone, "808-348-5584")
