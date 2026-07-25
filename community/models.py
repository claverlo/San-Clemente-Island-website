from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30)
    department = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    def __str__(self): return self.user.username

class ActiveListingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Listing(models.Model):
    CATEGORIES = [
        ("Free", "Free Stuff"),
        ("For Sale", "For Sale"),
        ("Volunteer Service", "Volunteer Service"),
        ("Community Group", "Community Group"),
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

class Event(models.Model):
    title = models.CharField(max_length=140)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=120)
    category = models.CharField(max_length=80, default="MWR Activity")
    class Meta: ordering = ["date"]
    def __str__(self): return self.title

class Announcement(models.Model):
    title = models.CharField(max_length=160)
    body = models.TextField()
    priority = models.CharField(max_length=20, choices=[("Routine", "Routine"), ("Important", "Important"), ("Urgent", "Urgent")], default="Routine")
    published_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-published_at"]
    def __str__(self): return self.title

class LostFound(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=[("Lost", "Lost"), ("Found", "Found")])
    item = models.CharField(max_length=140)
    description = models.TextField()
    location = models.CharField(max_length=120)
    date = models.DateField()
    resolved = models.BooleanField(default=False)
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

class PointOfInterest(models.Model):
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    image = models.ImageField(upload_to="poi/", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="points_of_interest", blank=True, null=True)
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class PointOfInterestPhotoRequest(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]
    poi = models.ForeignKey(PointOfInterest, on_delete=models.CASCADE, related_name="photo_requests")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="poi_photo_requests")
    caption = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="poi_requests/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Photo request for {self.poi.title}"
