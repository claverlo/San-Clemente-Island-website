from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.static import serve
from community.forms import StyledAuthenticationForm, StyledPasswordResetForm, StyledSetPasswordForm
from mapapi.frontend import serve_map_frontend

urlpatterns = [
    path("admin/", admin.site.urls),
    path("map/api/", include("mapapi.urls")),
    path("map/favicon.svg", serve, {"document_root": settings.MAP_FRONTEND_DIST_DIR, "path": "favicon.svg"}),
    path("map/icons.svg", serve, {"document_root": settings.MAP_FRONTEND_DIST_DIR, "path": "icons.svg"}),
    re_path(r"^map/assets/(?P<path>.*)$", serve, {"document_root": settings.MAP_FRONTEND_DIST_DIR / "assets"}),
    re_path(r"^map/(?!api/|assets/|favicon\.svg|icons\.svg).*$", serve_map_frontend),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=StyledAuthenticationForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        form_class=StyledPasswordResetForm,
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html",
    ), name="password_reset_done"),
    path("password-reset/confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
        form_class=StyledSetPasswordForm,
    ), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html",
    ), name="password_reset_complete"),
    path("", include("community.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
