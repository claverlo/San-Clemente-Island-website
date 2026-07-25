from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), path("marketplace/", views.marketplace, name="marketplace"),
    path("listings/new/", views.listing_create, name="listing_create"), path("listings/<int:pk>/", views.listing_detail, name="listing_detail"),
    path("listings/<int:pk>/edit/", views.listing_edit, name="listing_edit"), path("listings/<int:pk>/delete/", views.listing_delete, name="listing_delete"),
    path("events/", views.events, name="events"), path("announcements/", views.announcements, name="announcements"),
    path("lost-found/", views.lost_found, name="lost_found"), path("emergency/", views.emergency, name="emergency"),
    path("map/", views.map_view, name="map"), path("pois/new/", views.poi_create, name="poi_create"),
    path("pois/photo-request/", views.poi_photo_request, name="poi_photo_request"),
    path("pois/requests/<int:pk>/decision/", views.poi_request_decision, name="poi_request_decision"),
    path("register/", views.register, name="register"), path("dashboard/", views.dashboard, name="dashboard"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
    path("resend-verification/", views.resend_verification, name="resend_verification"),
]
