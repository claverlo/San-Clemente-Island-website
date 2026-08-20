from django.urls import path

from . import views

urlpatterns = [
    path("spots/", views.SpotListCreateView.as_view(), name="spot-list-create"),
    path("spots/<int:spot_id>/", views.SpotDetailView.as_view(), name="spot-detail"),
    path(
        "spots/<int:spot_id>/main-image/",
        views.SpotMainImageView.as_view(),
        name="spot-main-image",
    ),
    path(
        "spots/<int:spot_id>/photos/",
        views.SpotPhotoUploadView.as_view(),
        name="spot-photo-upload",
    ),
    path(
        "spots/<int:spot_id>/photos/<int:photo_id>/",
        views.PhotoDetailView.as_view(),
        name="photo-detail",
    ),
    path(
        "spots/<int:spot_id>/photos/<int:photo_id>/approve/",
        views.PhotoApproveView.as_view(),
        name="photo-approve",
    ),
    path("admin/login/", views.AdminLoginView.as_view(), name="admin-login"),
    path("admin/logout/", views.AdminLogoutView.as_view(), name="admin-logout"),
    path("admin/status/", views.AdminStatusView.as_view(), name="admin-status"),
]
