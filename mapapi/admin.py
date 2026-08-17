from django.contrib import admin

from .models import Photo, Spot


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ("image", "status", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ("name", "lat", "lng", "created_at")
    search_fields = ("name",)
    inlines = (PhotoInline,)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("spot", "status", "uploaded_at")
    list_filter = ("status", "uploaded_at")
    search_fields = ("spot__name",)
    actions = ("approve_photos", "reject_photos")

    @admin.action(description="Approve selected photos")
    def approve_photos(self, request, queryset):
        count = queryset.update(status=Photo.STATUS_APPROVED)
        self.message_user(request, f"{count} photo(s) approved.")

    @admin.action(description="Reject selected photos (deletes them)")
    def reject_photos(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} photo(s) rejected and removed.")
