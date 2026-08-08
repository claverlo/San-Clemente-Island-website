from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Announcement, ContentReport, Event, Listing, ListingImage, LostFound, PointOfInterest, PointOfInterestPhotoRequest, Profile, SellerMessage


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
    list_display = ("title", "category", "moderation_status", "price", "seller", "is_sold", "deleted_at", "created_at")
    list_filter = ("category", "condition", "moderation_status", "is_sold", "deleted_at")
    search_fields = ("title", "description", "seller__username", "seller__first_name", "seller__last_name")
    readonly_fields = ("deleted_at",)
    actions = ("approve_posts", "reject_posts", "move_to_trash", "restore_posts")

    def get_queryset(self, request):
        return Listing.all_objects.get_queryset()

    @admin.action(description="Move selected posts to trash")
    def move_to_trash(self, request, queryset):
        count = queryset.filter(deleted_at__isnull=True).update(deleted_at=timezone.now())
        self.message_user(request, f"{count} post(s) moved to trash.")

    @admin.action(description="Approve selected posts")
    def approve_posts(self, request, queryset):
        count = queryset.update(moderation_status="approved", moderation_notes="")
        self.message_user(request, f"{count} post(s) approved.")

    @admin.action(description="Reject selected posts")
    def reject_posts(self, request, queryset):
        count = queryset.update(moderation_status="rejected")
        self.message_user(request, f"{count} post(s) rejected.")

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


@admin.register(LostFound)
class LostFoundAdmin(admin.ModelAdmin):
    list_display = ("item", "kind", "moderation_status", "user", "location", "created_at")
    list_filter = ("kind", "moderation_status", "resolved", "created_at")
    search_fields = ("item", "description", "user__username", "contact_name")
    actions = ("approve_reports", "reject_reports")

    @admin.action(description="Approve selected reports")
    def approve_reports(self, request, queryset):
        count = queryset.update(moderation_status="approved", moderation_notes="")
        self.message_user(request, f"{count} report(s) approved.")

    @admin.action(description="Reject selected reports")
    def reject_reports(self, request, queryset):
        count = queryset.update(moderation_status="rejected")
        self.message_user(request, f"{count} report(s) rejected.")


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "listing", "lost_found", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reporter__username", "reason", "listing__title", "lost_found__item")


admin.site.register([Announcement, Event, ListingImage, SellerMessage])
