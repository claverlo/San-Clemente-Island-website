from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from .forms import ListingForm, LostFoundForm, PointOfInterestForm, PointOfInterestPhotoRequestForm, ProfileForm, RegistrationForm
from .models import Announcement, Event, Listing, ListingImage, LostFound, PointOfInterest, PointOfInterestPhotoRequest, Profile

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

def home(request):
    return render(request, "community/home.html", {
        "listings": Listing.objects.filter(is_sold=False)[:4],
        "events": Event.objects.filter(date__gte=timezone.now())[:3],
        "contacts": CONTACTS[:3],
        "categories": Listing.CATEGORIES,
        "points_of_interest": PointOfInterest.objects.filter(approved=True)[:12],
    })


def map_view(request):
    can_request_photo = False
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        can_request_photo = bool(profile and profile.phone)
    pending_requests = PointOfInterestPhotoRequest.objects.filter(status="pending")
    return render(request, "community/map.html", {
        "points_of_interest": PointOfInterest.objects.filter(approved=True),
        "poi_form": PointOfInterestForm(),
        "photo_request_form": PointOfInterestPhotoRequestForm(),
        "can_request_photo": can_request_photo,
        "pending_requests": pending_requests,
        "is_admin": request.user.is_staff or request.user.is_superuser,
    })

def marketplace(request):
    listings = Listing.objects.all()
    query, category, condition = request.GET.get("q", "").strip(), request.GET.get("category", ""), request.GET.get("condition", "")
    if query: listings = listings.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
    if category: listings = listings.filter(category=category)
    if condition: listings = listings.filter(condition=condition)
    if request.GET.get("available") == "1": listings = listings.filter(is_sold=False)
    return render(request, "community/marketplace.html", {"listings": listings, "categories": Listing.CATEGORIES, "conditions": Listing.CONDITIONS, "query": query, "selected_category": category, "selected_condition": condition})

def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    return render(request, "community/listing_detail.html", {"listing": listing, "photos": listing.images.all()})

@login_required
def listing_create(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.email_verified:
        messages.error(request, "Verify your email before posting a listing.")
        return redirect("dashboard")
    if not profile.phone:
        messages.error(request, "Add your phone number before posting a listing.")
        return redirect("dashboard")
    initial = {}
    if request.method == "GET":
        initial = {"contact_email": request.user.email, "contact_phone": profile.phone}
    form = ListingForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False)
        listing.seller = request.user
        listing.save()
        for photo in form.cleaned_data["photos"]:
            ListingImage.objects.create(listing=listing, image=photo)
        messages.success(request, "Listing published successfully.")
        return redirect(listing)
    if request.method == "POST":
        messages.error(request, "The listing was not posted. Please correct the highlighted fields.")
    return render(request, "community/listing_form.html", {"form": form, "heading": "Create a listing"})

@login_required
def listing_edit(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    form = ListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        form.save()
        new_photos = form.cleaned_data["photos"]
        if new_photos:
            for photo in new_photos:
                ListingImage.objects.create(listing=listing, image=photo)
        messages.success(request, "Listing updated.")
        return redirect(listing)
    return render(request, "community/listing_form.html", {"form": form, "heading": "Edit listing"})

@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to delete this listing.")
        return redirect(listing)
    if request.method == "POST": listing.delete(); messages.success(request, "Listing deleted."); return redirect("dashboard")
    return render(request, "community/confirm_delete.html", {"listing": listing})

def events(request): return render(request, "community/events.html", {"events": Event.objects.all()})
def announcements(request): return render(request, "community/announcements.html", {"announcements": Announcement.objects.all()})
def emergency(request): return render(request, "community/emergency.html", {"contacts": CONTACTS})

@login_required
def poi_create(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Only admins can create new map points of interest.")
        return redirect("map")
    form = PointOfInterestForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        poi = form.save(commit=False)
        poi.created_by = request.user
        poi.save()
        messages.success(request, "Point of interest added to the community map.")
        return redirect("map")
    if request.method == "POST":
        messages.error(request, "Please fix the highlighted fields before sharing a point of interest.")
    return redirect("map")

@login_required
def poi_photo_request(request, pk=None):
    poi_id = request.POST.get("poi_id") or pk
    if not poi_id:
        messages.error(request, "Please choose a map point before submitting a photo request.")
        return redirect("map")
    poi = get_object_or_404(PointOfInterest, pk=poi_id)
    profile = getattr(request.user, "profile", None)
    if not profile or not profile.phone:
        messages.error(request, "Only registered users with a phone number can submit photo requests.")
        return redirect("map")
    form = PointOfInterestPhotoRequestForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        request_obj = form.save(commit=False)
        request_obj.poi = poi
        request_obj.user = request.user
        request_obj.save()
        messages.success(request, "Your photo request has been submitted for admin approval.")
        return redirect("map")
    if request.method == "POST":
        messages.error(request, "Please add a photo and a short note before submitting.")
    return redirect("map")

@login_required
def poi_request_decision(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Only admins can approve or reject photo requests.")
        return redirect("map")
    photo_request = get_object_or_404(PointOfInterestPhotoRequest, pk=pk)
    if request.method == "POST":
        decision = request.POST.get("decision", "rejected").lower()
        photo_request.status = decision if decision in {"approved", "rejected"} else "rejected"
        photo_request.save()
        if photo_request.status == "approved":
            if photo_request.image:
                photo_request.poi.image.save(photo_request.image.name, photo_request.image, save=False)
                photo_request.poi.save(update_fields=["image"])
            messages.success(request, "Photo request approved and attached to the point of interest.")
        else:
            messages.info(request, "Photo request rejected.")
    return redirect("map")

def lost_found(request):
    form = LostFoundForm(request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated: messages.info(request, "Please log in to post an item."); return redirect("login")
        if form.is_valid(): item = form.save(commit=False); item.user = request.user; item.save(); messages.success(request, "Post added."); return redirect("lost_found")
    return render(request, "community/lost_found.html", {"items": LostFound.objects.filter(resolved=False), "form": form})

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        profile = Profile.objects.create(user=user, phone=form.cleaned_data["phone"])
        login(request, user)
        send_verification_email(request, profile)
        messages.success(request, "Account created. Check your email for the verification link.")
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
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid(): form.save(); messages.success(request, "Profile updated."); return redirect("dashboard")
    return render(request, "community/dashboard.html", {"profile": profile, "profile_form": form, "listings": request.user.listings.all(), "inquiries": sum((list(x.messages.all()) for x in request.user.listings.all()), [])})
