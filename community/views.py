from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from random import randint
from .forms import ContactMessageForm, ListingForm, LostFoundForm, ProfileForm, RegistrationForm
from .models import Announcement, ContactMessage, ContentReport, Event, Listing, ListingImage, LostFound, Profile
from .moderation import moderate_text_fields, moderate_uploaded_images
from .sms import send_phone_verification_text

CONTACTS = [
    ("Emergency / Fire / Medical", "911", "For immediate life-safety emergencies"),
    ("Island Security", "(619) 545-7418", "Security desk and non-emergency response"),
    ("Medical Clinic", "(619) 545-9550", "Routine medical support"),
    ("MWR Office", "(619) 545-3333", "Programs, recreation, and facilities"),
    ("Air Operations", "(619) 545-7500", "Flight and passenger information"),
]

def send_verification_email(request, profile):
    verification_url = request.build_absolute_uri(
        reverse("verify_email", args=[profile.verification_token])
    )
    send_mail(
        "Verify your SCI List email",
        f"Verify your SCI List account by opening this link:\n\n{verification_url}",
        None,
        [profile.user.email],
        fail_silently=False,
    )
    return verification_url

def run_moderation(text_values, files):
    status, reason = moderate_text_fields(*text_values)
    if status != "approved":
        return status, reason
    return moderate_uploaded_images(files)

def notify_admin_of_report(request, item_label, reporter, reason):
    reporter_label = reporter.username if reporter else "an anonymous visitor"
    admin_url = request.build_absolute_uri(reverse("admin:community_contentreport_changelist"))
    send_mail(
        f"SCI List: content reported - {item_label}",
        f"{reporter_label} reported \"{item_label}\" as inappropriate.\n\n"
        f"Reason given: {reason or 'No reason given.'}\n\n"
        f"Review it here: {admin_url}",
        None,
        [settings.REPORT_ADMIN_EMAIL],
        fail_silently=True,
    )

def home(request):
    Event.purge_expired()
    return render(request, "community/home.html", {
        "listings": Listing.objects.filter(is_sold=False, moderation_status="approved")[:4],
        "events": Event.objects.upcoming()[:3],
        "contacts": CONTACTS[:3],
        "categories": Listing.CATEGORIES,
    })

def marketplace(request):
    listings = Listing.objects.filter(moderation_status__in=["approved", "pending"])
    query, category, condition = request.GET.get("q", "").strip(), request.GET.get("category", ""), request.GET.get("condition", "")
    if query: listings = listings.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
    if category: listings = listings.filter(category=category)
    if condition: listings = listings.filter(condition=condition)
    if request.GET.get("available") == "1": listings = listings.filter(is_sold=False)
    return render(request, "community/marketplace.html", {"listings": listings, "categories": Listing.CATEGORIES, "conditions": Listing.CONDITIONS, "query": query, "selected_category": category, "selected_condition": condition})

def listing_detail(request, pk):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        listing = get_object_or_404(Listing.all_objects, pk=pk)
    else:
        listing = get_object_or_404(Listing.all_objects, pk=pk)
        if listing.moderation_status == "rejected" and listing.seller != request.user:
            raise Http404()
    return render(request, "community/listing_detail.html", {"listing": listing, "photos": listing.images.all()})

@login_required
def listing_create(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    initial = {}
    if request.method == "GET":
        initial = {"contact_email": request.user.email, "contact_phone": profile.phone}
    form = ListingForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False)
        listing.seller = request.user
        status, reason = run_moderation([listing.title, listing.description], form.cleaned_data["photos"])
        listing.moderation_status = status
        listing.moderation_notes = reason
        listing.save()
        for photo in form.cleaned_data["photos"]:
            ListingImage.objects.create(listing=listing, image=photo)
        if status == "approved":
            messages.success(request, "Listing published successfully.")
        else:
            messages.success(request, "Listing submitted and sent to admin for review.")
        return redirect(listing)
    if request.method == "POST":
        messages.error(request, "The listing was not posted. Please correct the highlighted fields.")
    return render(request, "community/listing_form.html", {"form": form, "heading": "Create a listing"})

@login_required
def listing_edit(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    form = ListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False)
        status, reason = run_moderation([listing.title, listing.description], form.cleaned_data["photos"])
        listing.moderation_status = status
        listing.moderation_notes = reason
        listing.save()
        new_photos = form.cleaned_data["photos"]
        if new_photos:
            for photo in new_photos:
                ListingImage.objects.create(listing=listing, image=photo)
        if status == "approved":
            messages.success(request, "Listing updated.")
        else:
            messages.success(request, "Listing updated and sent to admin for review.")
        return redirect("dashboard")
    return render(request, "community/listing_form.html", {"form": form, "heading": "Edit listing"})

@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to delete this listing.")
        return redirect(listing)
    if request.method == "POST": listing.delete(); messages.success(request, "Listing deleted."); return redirect("dashboard")
    return render(request, "community/confirm_delete.html", {"listing": listing})

def events(request):
    Event.purge_expired()
    return render(request, "community/events.html", {"events": Event.objects.upcoming()})
def announcements(request): return render(request, "community/announcements.html", {"announcements": Announcement.objects.all()})
def emergency(request): return render(request, "community/emergency.html", {"contacts": CONTACTS})

def lost_found(request):
    form = LostFoundForm(request.POST or None, request.FILES or None)
    show_post_form = False
    query = request.GET.get("q", "").strip()
    reported_on = request.GET.get("reported_on", "").strip()
    sort = request.GET.get("sort", "newest")
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        items_query = LostFound.objects.filter(resolved=False)
    else:
        items_query = LostFound.objects.filter(resolved=False, moderation_status__in=["approved", "pending"])

    if query:
        items_query = items_query.filter(Q(item__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))

    if reported_on:
        items_query = items_query.filter(created_at__date=reported_on)

    if sort == "oldest":
        items_query = items_query.order_by("created_at")
    else:
        sort = "newest"
        items_query = items_query.order_by("-created_at")

    if request.method == "POST":
        show_post_form = True
        if not request.user.is_authenticated: messages.info(request, "Please log in to post an item."); return redirect("login")
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            status, reason = run_moderation(
                [item.item, item.description],
                [form.cleaned_data.get("image_1"), form.cleaned_data.get("image_2")],
            )
            item.moderation_status = status
            item.moderation_notes = reason
            item.save()
            if status == "approved":
                messages.success(request, "Post added.")
            else:
                messages.success(request, "Post submitted and sent to admin for review.")
            return redirect("lost_found")
    return render(request, "community/lost_found.html", {
        "items_found": items_query.filter(kind="Found"),
        "items_lost": items_query.filter(kind="Lost"),
        "form": form,
        "show_post_form": show_post_form,
        "query": query,
        "reported_on": reported_on,
        "current_sort": sort,
    })


@login_required
def lost_found_delete(request, pk):
    item = get_object_or_404(LostFound, pk=pk)
    if item.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to delete this report.")
        return redirect("lost_found")
    if request.method == "POST":
        item.delete()
        messages.success(request, "Report deleted.")
    return redirect("lost_found")


@login_required
def lost_found_edit(request, pk):
    item = get_object_or_404(LostFound, pk=pk)
    if item.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to edit this report.")
        return redirect("lost_found")
    form = LostFoundForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        status, reason = run_moderation(
            [item.item, item.description],
            [form.cleaned_data.get("image_1"), form.cleaned_data.get("image_2")],
        )
        item.moderation_status = status
        item.moderation_notes = reason
        item.save()
        if status == "approved":
            messages.success(request, "Report updated.")
        else:
            messages.success(request, "Report updated and sent to admin for review.")
        return redirect("dashboard")
    return render(request, "community/lost_found_form.html", {"form": form, "heading": "Edit report"})


def report_listing(request, pk):
    listing = get_object_or_404(Listing.all_objects, pk=pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()[:255]
        reporter = request.user if request.user.is_authenticated else None
        if reporter:
            report, created = ContentReport.objects.get_or_create(
                reporter=reporter,
                listing=listing,
                defaults={"reason": reason},
            )
            if not created and reason:
                report.reason = reason
                report.save(update_fields=["reason"])
        else:
            ContentReport.objects.create(listing=listing, reason=reason)
        listing.moderation_status = "pending"
        listing.moderation_notes = "Flagged by a community report."
        listing.save(update_fields=["moderation_status", "moderation_notes"])
        notify_admin_of_report(request, listing.title, reporter, reason)
        messages.success(request, "Thanks. Your report was sent to admin for review.")
    return redirect("marketplace")


def report_lost_found(request, pk):
    item = get_object_or_404(LostFound, pk=pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()[:255]
        reporter = request.user if request.user.is_authenticated else None
        if reporter:
            report, created = ContentReport.objects.get_or_create(
                reporter=reporter,
                lost_found=item,
                defaults={"reason": reason},
            )
            if not created and reason:
                report.reason = reason
                report.save(update_fields=["reason"])
        else:
            ContentReport.objects.create(lost_found=item, reason=reason)
        item.moderation_status = "pending"
        item.moderation_notes = "Flagged by a community report."
        item.save(update_fields=["moderation_status", "moderation_notes"])
        notify_admin_of_report(request, item.item, reporter, reason)
        messages.success(request, "Thanks. Your report was sent to admin for review.")
    return redirect("lost_found")

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.create(user=user, phone=form.cleaned_data["phone"], email_verified=True)
        login(request, user)
        messages.success(request, "Account created. Add a phone number in your dashboard before posting listings.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})

def verify_email(request, token):
    profile = get_object_or_404(Profile, verification_token=token)
    profile.email_verified = True
    profile.save(update_fields=["email_verified"])
    messages.success(request, "Your email address is verified. You can now post listings.")
    return redirect("dashboard" if request.user.is_authenticated else "login")

@login_required
def resend_verification(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.email_verified:
        messages.info(request, "Your email is already verified.")
    elif request.method == "POST":
        send_verification_email(request, profile)
        messages.success(request, "A new verification email was sent.")
    return redirect("dashboard")

@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    has_phone = bool((profile.phone or "").strip())
    can_post_listing = True
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid(): form.save(); messages.success(request, "Profile updated."); return redirect("dashboard")
    report_queryset = LostFound.objects.all() if (request.user.is_staff or request.user.is_superuser) else LostFound.objects.filter(user=request.user)
    return render(request, "community/dashboard.html", {
        "profile": profile,
        "has_phone": has_phone,
        "can_post_listing": can_post_listing,
        "phone_code_sent": bool(profile.phone_verification_sent_at),
        "profile_form": form,
        "listings": request.user.listings.all(),
        "inquiries": sum((list(x.messages.all()) for x in request.user.listings.all()), []),
        "lost_found_reports": report_queryset,
    })


@login_required
def send_phone_verification(request):
    if request.method != "POST":
        return redirect("dashboard")

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.phone:
        messages.error(request, "Add a phone number first, then request a verification code.")
        return redirect("dashboard")

    code = f"{randint(0, 999999):06d}"
    profile.phone_verified = False
    profile.set_phone_verification_code(code)
    profile.save(update_fields=[
        "phone_verified",
        "phone_verification_code",
        "phone_verification_sent_at",
        "phone_verification_expires_at",
    ])

    sent, error = send_phone_verification_text(profile.phone, code)
    if sent:
        messages.success(request, "Verification code sent by text message.")
    else:
        if settings.DEBUG:
            messages.info(request, f"SMS is not configured. Test code: {code}")
        messages.error(request, error or "Could not send verification text.")
    return redirect("dashboard")


def contact_admin(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {"name": request.user.get_full_name() or request.user.username, "email": request.user.email}
    form = ContactMessageForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        contact_message = form.save()
        send_mail(
            f"SCI List contact message from {contact_message.name}",
            f"{contact_message.message}\n\nReply to: {contact_message.email}",
            None,
            [settings.REPORT_ADMIN_EMAIL],
            fail_silently=True,
        )
        messages.success(request, "Your message was sent. An admin will get back to you soon.")
        return redirect("contact_admin")
    return render(request, "community/contact.html", {"form": form})

@login_required
def verify_phone(request):
    if request.method != "POST":
        return redirect("dashboard")

    profile, _ = Profile.objects.get_or_create(user=request.user)
    submitted_code = (request.POST.get("phone_code") or "").strip()
    if not submitted_code:
        messages.error(request, "Enter the 6-digit verification code from your text message.")
        return redirect("dashboard")

    if profile.is_phone_code_valid(submitted_code):
        profile.phone_verified = True
        profile.clear_phone_verification_code()
        profile.save(update_fields=[
            "phone_verified",
            "phone_verification_code",
            "phone_verification_sent_at",
            "phone_verification_expires_at",
        ])
        messages.success(request, "Phone number verified. You can now post listings.")
    else:
        messages.error(request, "Invalid or expired code. Request a new verification code and try again.")

    return redirect("dashboard")
