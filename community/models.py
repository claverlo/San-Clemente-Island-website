from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid

class EmailCode(models.Model):
    """A short one-time code emailed to a member, used to verify their email or reset their password."""
    VERIFY = "verify"
    RESET = "reset"
    PURPOSES = [(VERIFY, "Verify email"), (RESET, "Reset password")]
    LIFETIME = timedelta(minutes=15)
    MAX_TRIES = 5
    RESEND_WAIT = timedelta(seconds=60)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_codes")
    purpose = models.CharField(max_length=10, choices=PURPOSES)
    code_hash = models.CharField(max_length=128)
    tries = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_purpose_display()} code for {self.user}"


class Passkey(models.Model):
    """A Face ID / fingerprint / Windows Hello sign-in set up on one of the member's devices."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="passkeys")
    credential_id = models.CharField(max_length=512, unique=True)
    public_key = models.TextField()
    sign_count = models.PositiveBigIntegerField(default=0)
    name = models.CharField(max_length=60, default="This device")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} for {self.user}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=6, blank=True)
    phone_verification_sent_at = models.DateTimeField(null=True, blank=True)
    phone_verification_expires_at = models.DateTimeField(null=True, blank=True)
    alert_categories = models.JSONField(default=list, blank=True)
    alert_keywords = models.CharField(max_length=300, blank=True, help_text="Comma-separated words to watch for in any new post, like shoes, slippers.")
    alerts_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    failed_logins = models.PositiveSmallIntegerField(default=0)
    login_locked = models.BooleanField(default=False, help_text="Locked after too many wrong passwords. Resetting the password unlocks it.")

    @property
    def alert_keyword_list(self):
        return [word.strip() for word in (self.alert_keywords or "").split(",") if word.strip()]

    def __str__(self): return self.user.username

    @property
    def can_post(self):
        return self.email_verified or self.user.is_staff or self.user.is_superuser

    def set_phone_verification_code(self, code):
        now = timezone.now()
        self.phone_verification_code = code
        self.phone_verification_sent_at = now
        self.phone_verification_expires_at = now + timedelta(minutes=10)

    def clear_phone_verification_code(self):
        self.phone_verification_code = ""
        self.phone_verification_sent_at = None
        self.phone_verification_expires_at = None

    def is_phone_code_valid(self, code):
        if not self.phone_verification_code or not self.phone_verification_expires_at:
            return False
        if timezone.now() > self.phone_verification_expires_at:
            return False
        return self.phone_verification_code == code

LOST_FOUND_ALERT = "Lost & Found"

def alert_choices():
    return Listing.CATEGORIES + [(LOST_FOUND_ALERT, LOST_FOUND_ALERT)]

class ActiveListingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Listing(models.Model):
    MODERATION_STATUS_CHOICES = [
        ("pending", "Pending review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    CATEGORIES = [
        ("Free", "Free Stuff"),
        ("For Sale", "For Sale"),
        ("Volunteer Service", "Volunteer Service"),
        ("Community Post", "Community Post"),
    ]
    CONDITIONS = [(x, x) for x in ["New", "Like New", "Good", "Fair"]]
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=140)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    condition = models.CharField(max_length=20, choices=CONDITIONS)
    location = models.CharField(max_length=120, default="San Clemente Island")
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    image = models.ImageField(upload_to="listings/", blank=True)
    is_sold = models.BooleanField(default=False)
    moderation_status = models.CharField(max_length=20, choices=MODERATION_STATUS_CHOICES, default="pending")
    moderation_notes = models.CharField(max_length=255, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ActiveListingManager()
    all_objects = models.Manager()
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse("listing_detail", args=[self.pk])
    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
    @property
    def primary_image_url(self):
        first = self.images.first()
        if first:
            return first.image.url
        return self.image.url if self.image else ""

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="listings/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Photo for {self.listing.title}"


class EventQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(date__gte=timezone.now())

    def expired(self):
        return self.filter(date__lt=timezone.now())

class Event(models.Model):
    title = models.CharField(max_length=140)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=120)
    category = models.CharField(max_length=80, default="MWR Activity", blank=True)
    objects = EventQuerySet.as_manager()

    class Meta: ordering = ["date"]

    def __str__(self): return self.title

    @classmethod
    def purge_expired(cls):
        deleted_count, _ = cls.objects.expired().delete()
        return deleted_count

class Announcement(models.Model):
    title = models.CharField(max_length=160)
    body = models.TextField()
    priority = models.CharField(max_length=20, choices=[("Routine", "Routine"), ("Important", "Important"), ("Urgent", "Urgent")], default="Routine")
    published_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-published_at"]
    def __str__(self): return self.title

class LostFound(models.Model):
    CONTACT_METHODS = [("phone", "Phone"), ("email", "Email")]
    MODERATION_STATUS_CHOICES = Listing.MODERATION_STATUS_CHOICES
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=[("Lost", "Lost"), ("Found", "Found")])
    item = models.CharField(max_length=140)
    description = models.TextField()
    location = models.CharField(max_length=120)
    date = models.DateField()
    contact_name = models.CharField(max_length=100, blank=True)
    contact_method = models.CharField(max_length=10, choices=CONTACT_METHODS, default="phone")
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    image_1 = models.ImageField(upload_to="lost_found/", blank=True)
    image_2 = models.ImageField(upload_to="lost_found/", blank=True)
    resolved = models.BooleanField(default=False)
    moderation_status = models.CharField(max_length=20, choices=MODERATION_STATUS_CHOICES, default="pending")
    moderation_notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.kind}: {self.item}"

class SellerMessage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="messages")
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Message about {self.listing}"

class ChatMessage(models.Model):
    PHOTO_LIFETIME = timedelta(days=7)
    MODERATION_STATUS_CHOICES = Listing.MODERATION_STATUS_CHOICES
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    body = models.TextField(blank=True, max_length=1000)
    image = models.ImageField(upload_to="chat/", blank=True)
    photo_expired = models.BooleanField(default=False)
    moderation_status = models.CharField(max_length=20, choices=MODERATION_STATUS_CHOICES, default="approved")
    moderation_notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ["created_at"]

    def __str__(self): return f"{self.user.username}: {self.body[:40] or 'photo'}"

    @classmethod
    def purge_old_photos(cls):
        """Delete photo files older than PHOTO_LIFETIME but keep the text of the message."""
        cutoff = timezone.now() - cls.PHOTO_LIFETIME
        purged = 0
        for message in cls.objects.filter(created_at__lt=cutoff).exclude(image=""):
            message.image.delete(save=False)
            message.photo_expired = True
            message.save(update_fields=["image", "photo_expired"])
            purged += 1
        return purged

class ContentReport(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("resolved", "Resolved")]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    lost_found = models.ForeignKey(LostFound, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["reporter", "listing"], name="unique_listing_report_per_user", condition=models.Q(reporter__isnull=False)),
            models.UniqueConstraint(fields=["reporter", "lost_found"], name="unique_lostfound_report_per_user", condition=models.Q(reporter__isnull=False)),
            models.UniqueConstraint(fields=["reporter", "chat_message"], name="unique_chat_report_per_user", condition=models.Q(reporter__isnull=False)),
        ]

    def __str__(self):
        target = self.listing.title if self.listing else str(self.lost_found or self.chat_message)
        who = self.reporter.username if self.reporter else "anonymous"
        return f"Report by {who} on {target}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.name}"


class RateLimitHit(models.Model):
    """One attempt at something we limit (wrong password, report, sign-up...). Old rows are deleted after a day."""
    key = models.CharField(max_length=200, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class Notification(models.Model):
    """One line in a member's notification bell. Deleted automatically after 30 days."""
    KEEP_FOR = timedelta(days=30)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    icon = models.CharField(max_length=40, default="bi-bell")
    text = models.CharField(max_length=255)
    url = models.CharField(max_length=300, blank=True)
    key = models.CharField(max_length=120, blank=True, db_index=True)  # stops the same thing being sent twice
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.text[:50]}"
