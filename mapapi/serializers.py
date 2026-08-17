from rest_framework import serializers

from .models import Photo, Spot


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["id", "image", "status", "uploaded_at"]


class SpotSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()
    mainImage = serializers.ImageField(source="main_image", read_only=True)
    gallery = serializers.SerializerMethodField()
    pending = serializers.SerializerMethodField()

    class Meta:
        model = Spot
        fields = ["id", "name", "position", "mainImage", "gallery", "pending"]

    def get_position(self, obj):
        return [obj.lat, obj.lng]

    def get_gallery(self, obj):
        approved = [p for p in obj.photos.all() if p.status == Photo.STATUS_APPROVED]
        return PhotoSerializer(approved, many=True, context=self.context).data

    def get_pending(self, obj):
        if not self.context.get("is_admin"):
            return []
        pending = [p for p in obj.photos.all() if p.status == Photo.STATUS_PENDING]
        return PhotoSerializer(pending, many=True, context=self.context).data
