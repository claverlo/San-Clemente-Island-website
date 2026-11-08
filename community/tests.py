import re
from django.core import mail
import tempfile
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .chat import search_terms
from .models import ChatMessage, ContentReport, Event, Listing, ListingImage, LostFound, Profile

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
    def test_signup_needs_only_email_name_and_password(self):
        response = self.client.post(reverse("register"), {
            "email": "New.Member@Example.com", "first_name": "Dana",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("verify_code"))
        user = User.objects.get(email="new.member@example.com")
        self.assertEqual(user.username, "new.member@example.com")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.phone, "")
        self.assertFalse(profile.email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(profile.verification_token), mail.outbox[0].body)
        self.assertRegex(mail.outbox[0].subject, r"\d{6}")

        self.client.get(reverse("verify_email", args=[profile.verification_token]))
        response = self.client.post(reverse("listing_create"), {
            "title": "No phone lamp", "category": "For Sale", "price": "5.00", "location": "Wilson Cove",
            "description": "Works well.", "contact_email": "new.member@example.com", "contact_phone": "",
        })
        self.assertTrue(Listing.all_objects.filter(title="No phone lamp", contact_phone="").exists())

    def test_signup_form_has_no_phone_or_text_consent(self):
        page = self.client.get(reverse("register")).content.decode()
        self.assertNotIn('name="phone"', page)
        self.assertNotIn('name="username"', page)
        self.assertNotIn("consent_privacy", page)

    def test_signup_rejects_an_email_already_in_use(self):
        User.objects.create_user("old", email="taken@example.com", password="x")
        response = self.client.post(reverse("register"), {
            "email": "TAKEN@example.com", "first_name": "Sam",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertContains(response, "already uses this email")

    def test_login_with_email_or_old_username(self):
        User.objects.create_user("oldname", email="Old@Example.com", password="testpass123")
        response = self.client.post(reverse("login"), {"username": "old@example.com", "password": "testpass123"})
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "oldname", "password": "testpass123"})
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "old@example.com", "password": "wrong"})
        self.assertContains(response, "email and password don")

    def test_chat_never_shows_an_email_as_the_name(self):
        user = User.objects.create_user("pat@example.com", email="pat@example.com", password="x")
        ChatMessage.objects.create(user=user, body="hello")
        page = self.client.get(reverse("chat")).content.decode()
        self.assertNotIn("pat@example.com", page)
        self.assertIn("<strong>pat</strong>", page)

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
        self.assertEqual(listing.moderation_status, "approved")
        self.assertEqual(ListingImage.objects.filter(listing=listing).count(), 4)
        self.assertContains(response, "Listing published successfully")

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


def make_photo(name="hours.png", size=(3000, 2000)):
    from io import BytesIO
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGB", size, "blue").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), OPENAI_API_KEY="")
class ChatTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("sailor", password="testpass123")
        self.other = User.objects.create_user("diver", password="testpass123")
        for user in (self.user, self.other):
            Profile.objects.create(user=user, phone="", email_verified=True)

    def test_anyone_can_read_but_must_log_in_to_post(self):
        ChatMessage.objects.create(user=self.other, body="Hello island")
        response = self.client.get(reverse("chat"))
        self.assertContains(response, "Hello island")
        self.assertContains(response, "Log in")
        self.client.post(reverse("chat"), {"body": "sneaky"})
        self.assertFalse(ChatMessage.objects.filter(body="sneaky").exists())

    def test_chat_page_can_be_shown_in_the_site_panel(self):
        self.assertEqual(self.client.get(reverse("chat"))["X-Frame-Options"], "SAMEORIGIN")

    def test_member_posts_text_and_photo_is_shrunk(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("chat"), {"body": "Store is open 8 to 3 today", "image": make_photo()})
        self.assertEqual(response.status_code, 302)
        message = ChatMessage.objects.get(user=self.user)
        self.assertEqual(message.moderation_status, "approved")
        self.assertTrue(message.image.name.endswith(".jpg"))
        from PIL import Image
        with Image.open(message.image.path) as image:
            self.assertLessEqual(max(image.size), 1600)

    def test_empty_message_is_rejected(self):
        self.client.login(username="sailor", password="testpass123")
        response = self.client.post(reverse("chat"), {"body": "   "})
        self.assertContains(response, "Type a message or add a photo.")
        self.assertFalse(ChatMessage.objects.exists())

    def test_photos_older_than_seven_days_are_removed_but_text_stays(self):
        old = ChatMessage.objects.create(user=self.user, body="Old hours", image=make_photo("old.png", (10, 10)))
        ChatMessage.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=8))
        fresh = ChatMessage.objects.create(user=self.user, body="New hours", image=make_photo("new.png", (10, 10)))
        self.client.get(reverse("chat"))
        old.refresh_from_db(); fresh.refresh_from_db()
        self.assertFalse(old.image)
        self.assertTrue(old.photo_expired)
        self.assertEqual(old.body, "Old hours")
        self.assertTrue(fresh.image)

    def test_search_shows_matching_messages_without_ai(self):
        ChatMessage.objects.create(user=self.other, body="Anyone want to go fishing?")
        ChatMessage.objects.create(user=self.other, body="The store hours today are 0800 to 1500")
        response = self.client.get(reverse("chat"), {"q": "does anybody know the store hours today"})
        self.assertContains(response, "0800 to 1500")
        self.assertNotContains(response, "fishing")
        self.assertContains(response, "1 related message")

    def test_search_shows_ai_answer_crediting_the_poster(self):
        hours = ChatMessage.objects.create(user=self.other, body="Store is open 8 to 3 today")
        with patch("community.views.ai_answer", return_value=("According to diver, the store is open 8 to 3.", [hours.pk])) as mocked:
            response = self.client.get(reverse("chat"), {"q": "store hours"})
        self.assertContains(response, "According to diver, the store is open 8 to 3.")
        self.assertIn(hours, mocked.call_args.args[1])

    def test_reported_message_is_hidden_until_admin_review(self):
        message = ChatMessage.objects.create(user=self.other, body="Rude message")
        self.client.login(username="sailor", password="testpass123")
        self.client.post(reverse("report_chat_message", args=[message.pk]), {"reason": "rude"})
        message.refresh_from_db()
        self.assertEqual(message.moderation_status, "pending")
        self.assertTrue(ContentReport.objects.filter(reporter=self.user, chat_message=message).exists())
        self.assertNotContains(self.client.get(reverse("chat")), "Rude message")

    def test_updates_returns_only_new_visible_messages(self):
        first = ChatMessage.objects.create(user=self.other, body="First")
        ChatMessage.objects.create(user=self.other, body="Second")
        ChatMessage.objects.create(user=self.other, body="Hidden", moderation_status="pending")
        data = self.client.get(reverse("chat_updates"), {"after": first.pk}).json()
        self.assertIn("Second", data["html"])
        self.assertNotIn("First", data["html"])
        self.assertNotIn("Hidden", data["html"])

    def test_only_author_can_delete_message(self):
        message = ChatMessage.objects.create(user=self.other, body="Mine")
        self.client.login(username="sailor", password="testpass123")
        self.client.post(reverse("chat_delete", args=[message.pk]))
        self.assertTrue(ChatMessage.objects.filter(pk=message.pk).exists())
        self.client.login(username="diver", password="testpass123")
        self.client.post(reverse("chat_delete", args=[message.pk]))
        self.assertFalse(ChatMessage.objects.filter(pk=message.pk).exists())

    def test_search_includes_replies_that_dont_repeat_the_question(self):
        ChatMessage.objects.create(user=self.user, body="Anybody know the store hours today?")
        ChatMessage.objects.create(user=self.other, body="Open 0800 to 1500")
        response = self.client.get(reverse("chat"), {"q": "store hours"})
        self.assertContains(response, "Open 0800 to 1500")

    def test_search_terms_drop_filler_words(self):
        self.assertEqual(search_terms("Hey, does anybody know the store hours today?"), ["store", "hours"])


class InstallableAppTests(TestCase):
    def test_manifest_describes_sci_connect_app(self):
        response = self.client.get(reverse("app_manifest"))
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        manifest = response.json()
        self.assertEqual(manifest["name"], "SCI Connect")
        self.assertEqual(manifest["display"], "standalone")
        self.assertTrue(any(icon["purpose"] == "maskable" for icon in manifest["icons"]))

    def test_service_worker_is_served_from_site_root_and_not_cached(self):
        response = self.client.get("/sw.js")
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertContains(response, reverse("offline"))

    def test_pages_link_the_manifest_and_offline_page_loads(self):
        self.assertContains(self.client.get(reverse("home")), reverse("app_manifest"))
        self.assertContains(self.client.get(reverse("offline")), "No signal right now")


class SessionAndChatNoticeTests(TestCase):
    def test_login_survives_closing_the_browser_for_twelve_hours(self):
        User.objects.create_user("sailor", password="testpass123")
        self.client.post(reverse("login"), {"username": "sailor", "password": "testpass123"})
        cookie = self.client.cookies["sessionid"]
        self.assertEqual(int(cookie["max-age"]), 12 * 60 * 60)

    def test_chat_warns_against_sharing_sensitive_information(self):
        self.assertContains(self.client.get(reverse("chat")), "Please do not share any sensitive information.")



@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", OPENAI_API_KEY="")
class AccountFeatureTests(TestCase):
    def setUp(self):
        self.poster = User.objects.create_user("poster", email="poster@example.com", password="testpass123")
        Profile.objects.create(user=self.poster, phone="555-555-0100", email_verified=True)
        self.fan = User.objects.create_user("fan", email="fan@example.com", password="testpass123")
        self.fan_profile = Profile.objects.create(user=self.fan, phone="", email_verified=True, alert_categories=["Free", "Lost & Found"])

    def post_listing(self, category):
        self.client.login(username="poster", password="testpass123")
        return self.client.post(reverse("listing_create"), {
            "title": "Free couch", "category": category, "price": "0", "location": "Housing",
            "description": "Comfy couch, come get it.", "contact_email": "poster@example.com", "contact_phone": "555-555-0100",
        })

    def test_free_stuff_alert_emails_subscribers_but_not_the_poster(self):
        self.post_listing("Free")
        self.assertEqual([m.to for m in mail.outbox], [["fan@example.com"]])
        self.assertIn("Free couch", mail.outbox[0].subject)
        self.assertIn(str(self.fan_profile.alerts_token), mail.outbox[0].body)

    def test_no_alert_for_categories_the_member_did_not_pick(self):
        self.post_listing("For Sale")
        self.assertEqual(mail.outbox, [])

    def test_other_words_alert_matches_any_category_and_plurals(self):
        self.fan_profile.alert_categories = []
        self.fan_profile.alert_keywords = "slipper, socks"
        self.fan_profile.save()
        self.client.login(username="poster", password="testpass123")
        self.client.post(reverse("listing_create"), {
            "title": "Bedroom stuff", "category": "For Sale", "price": "5", "location": "Housing",
            "description": "Two pairs of slippers, size 9.", "contact_email": "poster@example.com", "contact_phone": "",
        })
        self.assertEqual([m.to for m in mail.outbox], [["fan@example.com"]])
        self.assertIn('mentions "slipper"', mail.outbox[0].subject)

    def test_other_words_do_not_match_parts_of_words(self):
        self.fan_profile.alert_categories = []
        self.fan_profile.alert_keywords = "car"
        self.fan_profile.save()
        self.post_listing("For Sale")  # "Free couch ... Comfy couch" has no "car"; "care" etc. should not match either
        self.client.post(reverse("listing_create"), {
            "title": "Scarf", "category": "For Sale", "price": "5", "location": "Housing",
            "description": "Handle with care.", "contact_email": "poster@example.com", "contact_phone": "",
        })
        self.assertEqual(mail.outbox, [])

    def test_one_email_when_category_and_word_both_match(self):
        self.fan_profile.alert_keywords = "couch"
        self.fan_profile.save()
        self.post_listing("Free")
        self.assertEqual(len(mail.outbox), 1)

    def test_dashboard_saves_other_words(self):
        self.client.login(username="fan", password="testpass123")
        self.client.post(reverse("dashboard"), {"form_type": "alerts", "alert_other": "on", "alert_keywords": " Shoes,slippers , shoes,, "})
        self.fan_profile.refresh_from_db()
        self.assertEqual(self.fan_profile.alert_keywords, "Shoes, slippers")
        self.assertEqual(self.fan_profile.alert_categories, [])
        page = self.client.get(reverse("dashboard"))
        self.assertContains(page, "e.g. shoes, slippers, socks")
        self.assertContains(page, 'value="Shoes, slippers"')

    def test_other_ticked_but_empty_shows_a_hint(self):
        self.client.login(username="fan", password="testpass123")
        response = self.client.post(reverse("dashboard"), {"form_type": "alerts", "alert_other": "on", "alert_keywords": ""})
        self.assertContains(response, "Type what you want to hear about")

    def test_unticking_other_clears_the_words(self):
        self.fan_profile.alert_keywords = "shoes"
        self.fan_profile.save()
        self.client.login(username="fan", password="testpass123")
        self.client.post(reverse("dashboard"), {"form_type": "alerts", "alert_keywords": "shoes"})
        self.fan_profile.refresh_from_db()
        self.assertEqual(self.fan_profile.alert_keywords, "")

    def test_lost_and_found_alert(self):
        self.client.login(username="poster", password="testpass123")
        self.client.post(reverse("lost_found"), {
            "kind": "Lost", "item": "Keys", "description": "Blue lanyard", "location": "Galley",
            "date": timezone.localdate().isoformat(), "contact_name": "Poster", "contact_method": "phone", "contact_phone": "555-555-0100",
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Lost: Keys", mail.outbox[0].subject)

    def test_member_saves_alert_choices_from_dashboard(self):
        self.client.login(username="fan", password="testpass123")
        self.client.post(reverse("dashboard"), {"form_type": "alerts", "alert_categories": ["For Sale"]})
        self.fan_profile.refresh_from_db()
        self.assertEqual(self.fan_profile.alert_categories, ["For Sale"])

    def test_alerts_off_link_turns_off_every_alert(self):
        url = reverse("alerts_off", args=[self.fan_profile.alerts_token])
        self.assertContains(self.client.get(url), "Turn off all alerts")
        self.client.post(url)
        self.fan_profile.refresh_from_db()
        self.assertEqual(self.fan_profile.alert_categories, [])

    def test_unverified_member_cannot_post_until_email_is_verified(self):
        newbie = User.objects.create_user("newbie", email="newbie@example.com", password="testpass123")
        Profile.objects.create(user=newbie, phone="")
        self.client.login(username="newbie", password="testpass123")
        self.assertRedirects(self.client.get(reverse("listing_create")), reverse("verify_code"))
        self.client.post(reverse("chat"), {"body": "hi"})
        self.assertFalse(ChatMessage.objects.exists())
        self.assertContains(self.client.get(reverse("dashboard")), "Enter my code")

    def test_delete_account_needs_the_right_password(self):
        self.client.login(username="fan", password="testpass123")
        response = self.client.post(reverse("delete_account"), {"password": "wrong"})
        self.assertContains(response, "That password is not correct.")
        self.assertTrue(User.objects.filter(username="fan").exists())
        response = self.client.post(reverse("delete_account"), {"password": "testpass123"})
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(User.objects.filter(username="fan").exists())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_delete_account_removes_the_members_posts(self):
        self.post_listing("For Sale")
        self.client.post(reverse("delete_account"), {"password": "testpass123"})
        self.assertFalse(Listing.all_objects.filter(title="Free couch").exists())

    def test_main_admin_account_cannot_be_deleted_from_the_site(self):
        User.objects.create_superuser("boss", "boss@example.com", "testpass123")
        self.client.login(username="boss", password="testpass123")
        self.client.post(reverse("delete_account"), {"password": "testpass123"})
        self.assertTrue(User.objects.filter(username="boss").exists())


def code_from(message):
    return re.search(r"\b(\d{6})\b", message.body).group(1)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OneTimeCodeAndLoginSafetyTests(TestCase):
    def sign_up(self):
        self.client.post(reverse("register"), {
            "email": "kai@example.com", "first_name": "Kai",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        return User.objects.get(email="kai@example.com")

    def test_signup_code_verifies_the_email(self):
        user = self.sign_up()
        code = code_from(mail.outbox[0])
        page = self.client.get(reverse("verify_code"))
        self.assertContains(page, "kai@example.com")
        response = self.client.post(reverse("verify_code"), {"code": code[:3] + " " + code[3:]})
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(Profile.objects.get(user=user).email_verified)

    def test_wrong_code_does_not_verify_and_codes_work_once(self):
        user = self.sign_up()
        code = code_from(mail.outbox[0])
        wrong = "000000" if code != "000000" else "111111"
        self.assertContains(self.client.post(reverse("verify_code"), {"code": wrong}), "right or has expired")
        self.assertFalse(Profile.objects.get(user=user).email_verified)

    def test_code_stops_working_after_five_wrong_tries(self):
        user = self.sign_up()
        code = code_from(mail.outbox[0])
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(5):
            self.client.post(reverse("verify_code"), {"code": wrong})
        self.client.post(reverse("verify_code"), {"code": code})
        self.assertFalse(Profile.objects.get(user=user).email_verified)

    def test_resend_waits_a_minute(self):
        self.sign_up()
        self.client.post(reverse("verify_code"), {"action": "resend"})
        self.assertEqual(len(mail.outbox), 1)

    def test_posting_before_verifying_goes_to_the_code_page(self):
        self.sign_up()
        self.assertRedirects(self.client.get(reverse("listing_create")), reverse("verify_code"))

    def make_member(self):
        user = User.objects.create_user("lee@example.com", email="lee@example.com", password="RightPass123!")
        Profile.objects.create(user=user, email_verified=True)
        return user

    def test_trust_this_device_keeps_you_signed_in_30_days(self):
        self.make_member()
        self.client.post(reverse("login"), {"username": "lee@example.com", "password": "RightPass123!", "trust_device": "on"})
        self.assertEqual(int(self.client.cookies["sessionid"]["max-age"]), 30 * 24 * 60 * 60)

    def test_without_trust_it_is_12_hours(self):
        self.make_member()
        self.client.post(reverse("login"), {"username": "lee@example.com", "password": "RightPass123!"})
        self.assertEqual(int(self.client.cookies["sessionid"]["max-age"]), 12 * 60 * 60)

    def test_email_stays_filled_in_after_a_wrong_password(self):
        self.make_member()
        response = self.client.post(reverse("login"), {"username": "lee@example.com", "password": "nope"})
        self.assertContains(response, 'value="lee@example.com"')
        self.assertContains(response, "3 more tries before the account locks")
        self.assertContains(response, "data-remember-email")

    def test_four_wrong_passwords_lock_the_account(self):
        self.make_member()
        for _ in range(4):
            response = self.client.post(reverse("login"), {"username": "lee@example.com", "password": "nope"})
        self.assertContains(response, "account is locked")
        response = self.client.post(reverse("login"), {"username": "lee@example.com", "password": "RightPass123!"})
        self.assertContains(response, "account is locked")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_a_right_password_resets_the_count(self):
        user = self.make_member()
        for _ in range(3):
            self.client.post(reverse("login"), {"username": "lee@example.com", "password": "nope"})
        self.client.post(reverse("login"), {"username": "lee@example.com", "password": "RightPass123!"})
        self.assertEqual(Profile.objects.get(user=user).failed_logins, 0)

    def test_reset_by_code_unlocks_and_signs_in(self):
        user = self.make_member()
        for _ in range(4):
            self.client.post(reverse("login"), {"username": "lee@example.com", "password": "nope"})
        response = self.client.post(reverse("password_reset"), {"email": "LEE@example.com"})
        self.assertRedirects(response, reverse("password_reset_code"))
        code = code_from(mail.outbox[-1])
        response = self.client.post(reverse("password_reset_code"), {"code": code, "new_password1": "BrandNew456!", "new_password2": "BrandNew456!"})
        self.assertRedirects(response, reverse("dashboard"))
        profile = Profile.objects.get(user=user)
        self.assertFalse(profile.login_locked)
        self.assertEqual(profile.failed_logins, 0)
        self.client.logout()
        self.client.post(reverse("login"), {"username": "lee@example.com", "password": "BrandNew456!"})
        self.assertIn("_auth_user_id", self.client.session)

    def test_reset_with_wrong_code_changes_nothing(self):
        user = self.make_member()
        self.client.post(reverse("password_reset"), {"email": "lee@example.com"})
        code = code_from(mail.outbox[-1])
        wrong = "000000" if code != "000000" else "111111"
        response = self.client.post(reverse("password_reset_code"), {"code": wrong, "new_password1": "BrandNew456!", "new_password2": "BrandNew456!"})
        self.assertContains(response, "right or has expired")
        user.refresh_from_db()
        self.assertTrue(user.check_password("RightPass123!"))

    def test_reset_for_unknown_email_looks_the_same_and_sends_nothing(self):
        response = self.client.post(reverse("password_reset"), {"email": "nobody@example.com"})
        self.assertRedirects(response, reverse("password_reset_code"))
        self.assertEqual(mail.outbox, [])

    def test_admins_are_never_locked_out(self):
        User.objects.create_superuser("boss2", email="boss2@example.com", password="RightPass123!")
        for _ in range(5):
            self.client.post(reverse("login"), {"username": "boss2@example.com", "password": "nope"})
        self.client.post(reverse("login"), {"username": "boss2@example.com", "password": "RightPass123!"})
        self.assertIn("_auth_user_id", self.client.session)


class FakeFaceIdDevice:
    """Acts like a phone's Face ID / fingerprint passkey so the full sign-in flow can be tested."""

    def __init__(self, rp_id="testserver", origin="https://testserver"):
        import os
        from cryptography.hazmat.primitives.asymmetric import ec
        self.rp_id, self.origin = rp_id, origin
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.count = 0

    @staticmethod
    def b64(data):
        import base64
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def client_data(self, kind, challenge):
        import json as _json
        return _json.dumps({"type": kind, "challenge": challenge, "origin": self.origin}).encode()

    def rp_hash(self):
        import hashlib
        return hashlib.sha256(self.rp_id.encode()).digest()

    def create(self, options):
        import cbor2
        numbers = self.key.public_key().public_numbers()
        cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32, "big"), -3: numbers.y.to_bytes(32, "big")})
        auth_data = (self.rp_hash() + bytes([0x45]) + (0).to_bytes(4, "big") + bytes(16)
                     + len(self.credential_id).to_bytes(2, "big") + self.credential_id + cose)
        attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        cid = self.b64(self.credential_id)
        return {"id": cid, "rawId": cid, "type": "public-key", "response": {
            "clientDataJSON": self.b64(self.client_data("webauthn.create", options["challenge"])),
            "attestationObject": self.b64(attestation), "transports": ["internal"]}, "clientExtensionResults": {}}

    def sign_in(self, options):
        import hashlib
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        self.count += 1
        client_data = self.client_data("webauthn.get", options["challenge"])
        auth_data = self.rp_hash() + bytes([0x05]) + self.count.to_bytes(4, "big")
        signature = self.key.sign(auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256()))
        cid = self.b64(self.credential_id)
        return {"id": cid, "rawId": cid, "type": "public-key", "response": {
            "clientDataJSON": self.b64(client_data), "authenticatorData": self.b64(auth_data),
            "signature": self.b64(signature), "userHandle": None}, "clientExtensionResults": {}}


class FaceIdSignInTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana@example.com", email="ana@example.com", password="RightPass123!")
        Profile.objects.create(user=self.user, email_verified=True)
        self.device = FakeFaceIdDevice()

    def post_json(self, name, data=None):
        import json as _json
        return self.client.post(reverse(name), _json.dumps(data or {}), content_type="application/json")

    def turn_on(self):
        self.client.force_login(self.user)
        options = self.post_json("passkey_register_options").json()
        self.assertEqual(options["authenticatorSelection"]["userVerification"], "required")
        return self.post_json("passkey_register_verify", self.device.create(options))

    def test_turn_on_then_sign_in_with_face_id(self):
        self.assertTrue(self.turn_on().json()["ok"])
        from community.models import Passkey
        self.assertEqual(Passkey.objects.filter(user=self.user).count(), 1)
        self.client.logout()
        options = self.post_json("passkey_login_options").json()
        response = self.post_json("passkey_login_verify", self.device.sign_in(options))
        self.assertEqual(response.json()["redirect"], reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)
        self.assertEqual(int(self.client.cookies["sessionid"]["max-age"]), 30 * 24 * 60 * 60)

    def test_a_device_that_was_never_set_up_is_refused(self):
        self.client.logout()
        options = self.post_json("passkey_login_options").json()
        response = self.post_json("passkey_login_verify", FakeFaceIdDevice().sign_in(options))
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_a_faked_signature_is_refused(self):
        self.turn_on()
        self.client.logout()
        options = self.post_json("passkey_login_options").json()
        attempt = self.device.sign_in(options)
        attempt["response"]["signature"] = FakeFaceIdDevice().sign_in(options)["response"]["signature"]
        self.assertEqual(self.post_json("passkey_login_verify", attempt).status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_reusing_an_old_challenge_is_refused(self):
        self.turn_on()
        self.client.logout()
        options = self.post_json("passkey_login_options").json()
        attempt = self.device.sign_in(options)
        self.post_json("passkey_login_verify", attempt)
        self.client.logout()
        self.assertEqual(self.post_json("passkey_login_verify", attempt).status_code, 400)

    def test_face_id_unlocks_an_account_locked_by_wrong_passwords(self):
        self.turn_on()
        self.client.logout()
        for _ in range(4):
            self.client.post(reverse("login"), {"username": "ana@example.com", "password": "nope"})
        self.assertTrue(Profile.objects.get(user=self.user).login_locked)
        options = self.post_json("passkey_login_options").json()
        self.post_json("passkey_login_verify", self.device.sign_in(options))
        self.assertFalse(Profile.objects.get(user=self.user).login_locked)
        self.assertIn("_auth_user_id", self.client.session)

    def test_must_be_signed_in_to_turn_on(self):
        self.assertEqual(self.post_json("passkey_register_options").status_code, 302)

    def test_remove_a_device(self):
        self.turn_on()
        key = self.user.passkeys.get()
        page = self.client.get(reverse("dashboard"))
        self.assertContains(page, "Turn on for this device")
        self.assertContains(page, key.name)
        self.client.post(reverse("passkey_delete", args=[key.pk]))
        self.assertFalse(self.user.passkeys.exists())

    def test_login_page_offers_face_id(self):
        self.assertContains(self.client.get(reverse("login")), "Sign in with Face ID / fingerprint")


class FederalHolidayTests(TestCase):
    """Dates checked against OPM's published federal holiday schedules."""

    def test_2026_dates_match_opm(self):
        from datetime import date
        from community.holidays import holidays_in_year
        got = {h.slug: (h.date, h.observed) for h in holidays_in_year(2026)}
        self.assertEqual(got["mlk-day"][0], date(2026, 1, 19))
        self.assertEqual(got["washingtons-birthday"][0], date(2026, 2, 16))
        self.assertEqual(got["memorial-day"][0], date(2026, 5, 25))
        self.assertEqual(got["independence-day"], (date(2026, 7, 4), date(2026, 7, 3)))
        self.assertEqual(got["labor-day"][0], date(2026, 9, 7))
        self.assertEqual(got["columbus-day"][0], date(2026, 10, 12))
        self.assertEqual(got["thanksgiving-day"][0], date(2026, 11, 26))
        self.assertNotIn("inauguration-day", got)

    def test_2027_weekend_holidays_move_like_opm_says(self):
        from datetime import date
        from community.holidays import holidays_in_year
        got = {h.slug: h.observed for h in holidays_in_year(2027)}
        self.assertEqual(got["juneteenth"], date(2027, 6, 18))
        self.assertEqual(got["independence-day"], date(2027, 7, 5))
        self.assertEqual(got["christmas-day"], date(2027, 12, 24))
        self.assertEqual(got["mlk-day"], date(2027, 1, 18))

    def test_each_month_shows_only_its_own_holidays(self):
        from community.holidays import holidays_in_month
        slugs = lambda y, m: [h.slug for h in holidays_in_month(y, m)]
        self.assertEqual(slugs(2026, 11), ["veterans-day", "thanksgiving-day"])
        self.assertEqual(slugs(2026, 10), ["columbus-day"])
        self.assertEqual(slugs(2026, 12), ["christmas-day"])
        self.assertEqual(slugs(2026, 3), [])
        self.assertEqual(slugs(2029, 1), ["new-years-day", "mlk-day"])  # no Inauguration Day slide

    def test_popular_days_are_added_to_their_month(self):
        from datetime import date
        from community.holidays import easter_sunday, month_highlights
        slugs = lambda y, m: [h.slug for h in month_highlights(y, m)]
        self.assertEqual(slugs(2026, 2), ["valentines-day", "washingtons-birthday"])
        self.assertEqual(slugs(2026, 5), ["mothers-day", "memorial-day"])
        self.assertEqual(slugs(2026, 6), ["juneteenth", "fathers-day"])
        self.assertEqual(slugs(2026, 10), ["columbus-day", "halloween"])
        self.assertEqual(slugs(2026, 12), ["christmas-day"])
        self.assertEqual(slugs(2026, 8), [])
        self.assertEqual([easter_sunday(y) for y in (2024, 2025, 2026, 2027)],
                         [date(2024, 3, 31), date(2025, 4, 20), date(2026, 4, 5), date(2027, 3, 28)])
        self.assertEqual(slugs(2027, 3), ["st-patricks-day", "easter"])

    def test_every_holiday_has_a_picture(self):
        from pathlib import Path
        from django.conf import settings
        from community.holidays import holidays_in_year, observances_in_year
        folder = Path(settings.BASE_DIR) / "static" / "images" / "holidays"
        for holiday in holidays_in_year(2029) + observances_in_year(2029):
            self.assertTrue((folder / f"{holiday.slug}.jpg").exists(), holiday.slug)

    def test_homepage_puts_this_months_holidays_first(self):
        from datetime import date
        from unittest import mock
        with mock.patch("community.views.timezone.localdate", return_value=date(2026, 11, 7)):
            page = self.client.get(reverse("home")).content.decode()
        self.assertIn('holiday-slide active" data-holiday="veterans-day"><img src="/static/images/holidays/veterans-day.jpg', page)
        self.assertIn("thanksgiving-day.jpg", page)
        self.assertNotIn("columbus-day.jpg", page)
        self.assertLess(page.index("thanksgiving-day.jpg"), page.index("homepage-diver.jpg"))
        with mock.patch("community.views.timezone.localdate", return_value=date(2026, 8, 7)):
            page = self.client.get(reverse("home")).content.decode()
        self.assertNotIn("holiday-slide", page)
        self.assertIn('class="hero-slide active" src="/static/images/homepage-diver.jpg"', page)
