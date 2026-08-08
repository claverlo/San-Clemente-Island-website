from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import ContentReport, Event, Listing, ListingImage, LostFound, Profile

class CommunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sailor", password="testpass123")
        Profile.objects.create(user=self.user, phone="555-555-0100", email_verified=True, phone_verified=True)
        self.listing = Listing.objects.create(seller=self.user, title="Bike", description="Good bike", price=100, category="For Sale", condition="Good", contact_email="seller@example.com", contact_phone="555-555-0100", moderation_status="approved")
    def test_public_pages(self):
        for name in ["home", "marketplace", "events", "announcements", "lost_found", "emergency"]: self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_homepage_uses_community_post_label(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Community Post")
        self.assertNotContains(response, "Community Group")

    def test_events_page_deletes_expired_events_and_shows_upcoming(self):
        Event.objects.create(
            title="Past event",
            description="Already finished",
            date=timezone.now() - timedelta(hours=2),
            location="Old location",
            category="Community",
        )
        future_event = Event.objects.create(
            title="Future event",
            description="Still upcoming",
            date=timezone.now() + timedelta(days=2),
            location="New location",
            category="Community",
        )

        response = self.client.get(reverse("events"))

        self.assertContains(response, "Future event")
        self.assertNotContains(response, "Past event")
        self.assertTrue(Event.objects.filter(pk=future_event.pk).exists())
        self.assertFalse(Event.objects.filter(title="Past event").exists())

    def test_purge_expired_events_command_deletes_only_expired_events(self):
        Event.objects.create(
            title="Expired",
            description="Should be deleted",
            date=timezone.now() - timedelta(days=1),
            location="Old location",
            category="Community",
        )
        upcoming = Event.objects.create(
            title="Upcoming",
            description="Should remain",
            date=timezone.now() + timedelta(days=1),
            location="Future location",
            category="Community",
        )

        call_command("purge_expired_events")

        self.assertFalse(Event.objects.filter(title="Expired").exists())
        self.assertTrue(Event.objects.filter(pk=upcoming.pk).exists())

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
        self.assertContains(response, "Contact email")
        self.assertContains(response, "Contact phone number")

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
    def test_registration_with_phone_can_reach_listing_form(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com", "phone": "555-555-0199",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
            "consent_privacy": "on",
        })
        self.assertRedirects(response, reverse("dashboard"))
        profile = Profile.objects.get(user__username="newuser")
        self.assertEqual(profile.phone, "555-555-0199")
        response = self.client.get(reverse("listing_create"))
        self.assertEqual(response.status_code, 200)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_registration_allows_email_signup_without_phone_and_posting_form(self):
        response = self.client.post(reverse("register"), {
            "username": "emailonly", "email": "emailonly@example.com", "phone": "",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
            "consent_privacy": "on",
        })
        self.assertRedirects(response, reverse("dashboard"))

        profile = Profile.objects.get(user__username="emailonly")
        self.assertEqual(profile.phone, "")

        response = self.client.get(reverse("listing_create"))
        self.assertEqual(response.status_code, 200)

    def test_new_listing_with_clean_text_is_auto_approved_and_visible_in_marketplace(self):
        user = User.objects.create_user("newposter", password="testpass123")
        Profile.objects.create(user=user, phone="555-555-0200", email_verified=True)
        self.client.login(username="newposter", password="testpass123")

        response = self.client.post(reverse("listing_create"), {
            "title": "Pending lamp", "category": "For Sale", "condition": "Good",
            "price": "25.00", "location": "Wilson Cove", "description": "Works well.",
            "contact_email": "seller@example.com", "contact_phone": "555-555-0200",
        }, follow=True)

        listing = Listing.all_objects.get(title="Pending lamp")
        self.assertEqual(listing.moderation_status, "approved")
        self.assertContains(response, "Listing published successfully")
        self.assertContains(self.client.get(reverse("marketplace")), "Pending lamp")

    def test_flagged_listing_text_is_sent_to_review(self):
        user = User.objects.create_user("rejectedposter", password="testpass123")
        Profile.objects.create(user=user, phone="555-555-0300", email_verified=True)
        self.client.login(username="rejectedposter", password="testpass123")

        response = self.client.post(reverse("listing_create"), {
            "title": "Drug sale", "category": "For Sale", "condition": "Good",
            "price": "25.00", "location": "Wilson Cove", "description": "Selling drugs now.",
            "contact_email": "seller@example.com", "contact_phone": "555-555-0300",
        }, follow=True)

        listing = Listing.all_objects.get(title="Drug sale")
        self.assertEqual(listing.moderation_status, "pending")
        self.assertContains(response, "sent to admin for review")

    def test_registration_requires_privacy_disclaimer_consent(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser2", "email": "new2@example.com", "phone": "555-555-0101",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You must accept the privacy disclaimer before signing up.")
        self.assertFalse(User.objects.filter(username="newuser2").exists())

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
        }, follow=True)
        listing = Listing.all_objects.get(title="Four photo item")
        self.assertEqual(listing.moderation_status, "pending")
        self.assertEqual(ListingImage.objects.filter(listing=listing).count(), 4)
        self.assertContains(response, "admin review")

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

    def test_community_post_allows_blank_price_and_email(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Poker night signup", "category": "Community Post", "condition": "Good",
            "price": "", "location": "Wilson Cove", "description": "Join the game night.",
            "contact_email": "", "contact_phone": "555-555-0100",
        }, follow=True)
        listing = Listing.all_objects.get(title="Poker night signup")
        self.assertEqual(listing.price, 0)
        self.assertEqual(listing.contact_email, "")
        self.assertContains(response, "Listing published successfully")

    def test_volunteer_service_allows_blank_price_but_requires_email(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "Weekend moving help", "category": "Volunteer Service", "condition": "Good",
            "price": "", "location": "Wilson Cove", "description": "Helping with boxes and lifting.",
            "contact_email": "helper@example.com", "contact_phone": "555-555-0100",
        }, follow=True)
        listing = Listing.all_objects.get(title="Weekend moving help")
        self.assertEqual(listing.price, 0)
        self.assertContains(response, "Listing published successfully")

    def test_non_community_post_requires_contact_email(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("listing_create"), {
            "title": "No email listing", "category": "For Sale", "condition": "Good",
            "price": "10.00", "location": "Wilson Cove", "description": "Missing email.",
            "contact_email": "", "contact_phone": "555-555-0100",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact email is required unless category is Community Post")

    def test_lost_found_pending_visible_to_everyone_but_marked_under_review(self):
        other_user = User.objects.create_user("other_lf_user", password="otherpass123")
        LostFound.objects.create(
            user=self.user,
            kind="Found",
            item="Pending sweater",
            description="Blue hoodie",
            location="Wilson Cove",
            date=timezone.localdate(),
            contact_name="Leo",
            contact_method="phone",
            contact_phone="555-555-0100",
            moderation_status="pending",
        )
        LostFound.objects.create(
            user=other_user,
            kind="Found",
            item="Approved wallet",
            description="Black wallet",
            location="Wilson Cove",
            date=timezone.localdate(),
            contact_name="Other",
            contact_method="phone",
            contact_phone="555-555-0111",
            moderation_status="approved",
        )

        public_response = self.client.get(reverse("lost_found"))
        self.assertContains(public_response, "Approved wallet")
        self.assertContains(public_response, "Pending sweater")
        self.assertContains(public_response, "Under review")

        self.client.login(username="sailor", password="testpass123")
        owner_response = self.client.get(reverse("lost_found"))
        self.assertContains(owner_response, "Pending sweater")
        self.assertContains(owner_response, "Under review")

    def test_lost_found_post_redirects_back_to_lost_found(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("lost_found"), {
            "kind": "Found",
            "item": "Posted keys",
            "description": "Key ring with blue tag",
            "location": "Wilson Cove",
            "date": timezone.localdate().isoformat(),
            "contact_name": "Leo",
            "contact_method": "phone",
            "contact_phone": "555-555-0100",
        })
        self.assertRedirects(response, reverse("lost_found"))

    def test_reporting_listing_sets_pending_and_creates_report(self):
        reporter = User.objects.create_user("reporter", password="reportpass123")
        self.client.login(username="reporter", password="reportpass123")

        response = self.client.post(reverse("report_listing", args=[self.listing.pk]), {
            "reason": "Inappropriate content",
        }, follow=True)

        self.assertRedirects(response, reverse("marketplace"))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.moderation_status, "pending")
        self.assertTrue(ContentReport.objects.filter(reporter=reporter, listing=self.listing).exists())

    def test_reporting_lost_found_sets_pending_and_creates_report(self):
        owner = User.objects.create_user("lfowner", password="ownerpass123")
        reporter = User.objects.create_user("lfreporter", password="reportpass123")
        report = LostFound.objects.create(
            user=owner,
            kind="Found",
            item="Found jacket",
            description="Black jacket",
            location="Wilson Cove",
            date=timezone.localdate(),
            contact_name="Owner",
            contact_method="phone",
            contact_phone="555-555-1111",
            moderation_status="approved",
        )

        self.client.login(username="lfreporter", password="reportpass123")
        response = self.client.post(reverse("report_lost_found", args=[report.pk]), {
            "reason": "Looks inappropriate",
        }, follow=True)

        self.assertRedirects(response, reverse("lost_found"))
        report.refresh_from_db()
        self.assertEqual(report.moderation_status, "pending")
        self.assertTrue(ContentReport.objects.filter(reporter=reporter, lost_found=report).exists())
