from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), path("marketplace/", views.marketplace, name="marketplace"),
    path("listings/new/", views.listing_create, name="listing_create"), path("listings/<int:pk>/", views.listing_detail, name="listing_detail"),
    path("listings/<int:pk>/edit/", views.listing_edit, name="listing_edit"), path("listings/<int:pk>/delete/", views.listing_delete, name="listing_delete"),
    path("listings/<int:pk>/report/", views.report_listing, name="report_listing"),
    path("events/", views.events, name="events"), path("announcements/", views.announcements, name="announcements"),
    path("lost-found/", views.lost_found, name="lost_found"), path("emergency/", views.emergency, name="emergency"),
    path("lost-found/<int:pk>/edit/", views.lost_found_edit, name="lost_found_edit"),
    path("lost-found/<int:pk>/delete/", views.lost_found_delete, name="lost_found_delete"),
    path("lost-found/<int:pk>/report/", views.report_lost_found, name="report_lost_found"),
    path("register/", views.register, name="register"), path("dashboard/", views.dashboard, name="dashboard"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
    path("resend-verification/", views.resend_verification, name="resend_verification"),
    path("phone/send-code/", views.send_phone_verification, name="send_phone_verification"),
    path("phone/verify/", views.verify_phone, name="verify_phone"),
    path("contact/", views.contact_admin, name="contact_admin"),
]
