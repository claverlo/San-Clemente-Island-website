from django.contrib.auth import authenticate, login as auth_login, logout
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Photo, Spot
from .permissions import IsAdminSession
from .serializers import SpotSerializer


def spot_context(request):
    is_admin = bool(request.user.is_authenticated and request.user.is_staff)
    return {"request": request, "is_admin": is_admin}


class SpotListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminSession()]
        return [AllowAny()]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        spots = Spot.objects.all()
        data = SpotSerializer(spots, many=True, context=spot_context(request)).data
        return Response(data)

    def post(self, request):
        name = request.data.get("name")
        try:
            lat = float(request.data.get("lat"))
            lng = float(request.data.get("lng"))
        except (TypeError, ValueError):
            return Response({"detail": "name, lat and lng are required."}, status=400)
        if not name:
            return Response({"detail": "name, lat and lng are required."}, status=400)

        spot = Spot.objects.create(name=name, lat=lat, lng=lng)
        data = SpotSerializer(spot, context=spot_context(request)).data
        return Response(data, status=201)


class SpotDetailView(APIView):
    permission_classes = [IsAdminSession]

    def patch(self, request, spot_id):
        spot = get_object_or_404(Spot, id=spot_id)
        try:
            lat = float(request.data.get("lat"))
            lng = float(request.data.get("lng"))
        except (TypeError, ValueError):
            return Response({"detail": "lat and lng are required."}, status=400)

        spot.lat = lat
        spot.lng = lng
        spot.save(update_fields=["lat", "lng"])
        data = SpotSerializer(spot, context=spot_context(request)).data
        return Response(data)

    def delete(self, request, spot_id):
        spot = get_object_or_404(Spot, id=spot_id)
        spot.delete()
        return Response(status=204)


class SpotMainImageView(APIView):
    permission_classes = [IsAdminSession]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, spot_id):
        spot = get_object_or_404(Spot, id=spot_id)
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "image file is required."}, status=400)

        spot.main_image = image
        spot.save()
        data = SpotSerializer(spot, context=spot_context(request)).data
        return Response(data)


class SpotPhotoUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, spot_id):
        spot = get_object_or_404(Spot, id=spot_id)
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "image file is required."}, status=400)

        is_admin = bool(request.user.is_authenticated and request.user.is_staff)
        status_value = Photo.STATUS_APPROVED if is_admin else Photo.STATUS_PENDING
        Photo.objects.create(spot=spot, image=image, status=status_value)

        data = SpotSerializer(spot, context=spot_context(request)).data
        return Response(data, status=201)


class PhotoDetailView(APIView):
    permission_classes = [IsAdminSession]

    def delete(self, request, spot_id, photo_id):
        photo = get_object_or_404(Photo, id=photo_id, spot_id=spot_id)
        spot = photo.spot
        photo.delete()
        data = SpotSerializer(spot, context=spot_context(request)).data
        return Response(data)


class PhotoApproveView(APIView):
    permission_classes = [IsAdminSession]

    def post(self, request, spot_id, photo_id):
        photo = get_object_or_404(Photo, id=photo_id, spot_id=spot_id)
        photo.status = Photo.STATUS_APPROVED
        photo.save()
        data = SpotSerializer(photo.spot, context=spot_context(request)).data
        return Response(data)


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            auth_login(request, user)
            return Response({"isAdmin": True})
        return Response({"detail": "Invalid username or password."}, status=403)


class AdminLogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({"isAdmin": False})


class AdminStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        is_admin = bool(request.user.is_authenticated and request.user.is_staff)
        return Response({"isAdmin": is_admin})
