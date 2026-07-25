from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Announcement, Event, Listing, ListingImage, LostFound, PointOfInterest, PointOfInterestPhotoRequest, Profile, SellerMessage


class UserListingInline(admin.TabularInline):
    model = Listing
    extra = 0
    fields = ("title", "category", "price", "is_sold", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True
    verbose_name = "User post"
    verbose_name_plural = "User posts (select Delete and save to remove individual posts)"


class UserProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    max_num = 1


admin.site.unregister(User)


@admin.register(User)
class CommunityUserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserListingInline)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "seller", "is_sold", "deleted_at", "created_at")
    list_filter = ("category", "condition", "is_sold", "deleted_at")
    search_fields = ("title", "description", "seller__username", "seller__first_name", "seller__last_name")
    readonly_fields = ("deleted_at",)
    actions = ("move_to_trash", "restore_posts")

    def get_queryset(self, request):
        return Listing.all_objects.get_queryset()

    @admin.action(description="Move selected posts to trash")
    def move_to_trash(self, request, queryset):
        count = queryset.filter(deleted_at__isnull=True).update(deleted_at=timezone.now())
        self.message_user(request, f"{count} post(s) moved to trash.")

    @admin.action(description="Restore selected deleted posts")
    def restore_posts(self, request, queryset):
        count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{count} post(s) restored.")

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        queryset.update(deleted_at=timezone.now())


@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ("title", "approved", "created_by", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("title", "description", "created_by__username")


@admin.register(PointOfInterestPhotoRequest)
class PointOfInterestPhotoRequestAdmin(admin.ModelAdmin):
    list_display = ("poi", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("poi__title", "caption", "user__username")


admin.site.register([Announcement, Event, ListingImage, LostFound, SellerMessage])
