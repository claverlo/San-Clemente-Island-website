from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=6, blank=True)
    phone_verification_sent_at = models.DateTimeField(null=True, blank=True)
    phone_verification_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self): return self.user.username

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
    contact_phone = models.CharField(max_length=30)
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

class ContentReport(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("resolved", "Resolved")]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    lost_found = models.ForeignKey(LostFound, on_delete=models.CASCADE, related_name="content_reports", null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["reporter", "listing"], name="unique_listing_report_per_user", condition=models.Q(reporter__isnull=False)),
            models.UniqueConstraint(fields=["reporter", "lost_found"], name="unique_lostfound_report_per_user", condition=models.Q(reporter__isnull=False)),
        ]

    def __str__(self):
        target = self.listing.title if self.listing else str(self.lost_found)
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
