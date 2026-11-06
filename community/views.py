from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from random import randint
from .chat import ai_answer, matching_messages, shrink_photo, with_replies
from .forms import AlertSettingsForm, ChatMessageForm, DeleteAccountForm, ContactMessageForm, ListingForm, LostFoundForm, ProfileForm, RegistrationForm
from .models import Announcement, ChatMessage, ContactMessage, ContentReport, Event, Listing, ListingImage, LostFound, Profile, LOST_FOUND_ALERT
from .notifications import notify_subscribers
from .moderation import moderate_text_fields, moderate_uploaded_images
from .sms import send_phone_verification_text

CONTACTS = [
    ("Command Duty Officer", "(619) 571-9512", "Command Duty Officer (CDO) desk"),
    ("Security", "(619) 572-6930", "Security desk and non-emergency response"),
    ("Air Terminal", "(619) 524-9182", "Flight and passenger information"),
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

def needs_verified_email(request):
    """Return a redirect for signed-in members who haven't verified their email yet, else None."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.can_post:
        return None
    messages.error(request, "Please verify your email before posting. Check your inbox for the link, or resend it below.")
    return redirect("dashboard")

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

    grouped = None
    if not query and not category and not condition:
        grouped = []
        for value, label in Listing.CATEGORIES:
            category_listings = listings.filter(category=value)
            total = category_listings.count()
            if total:
                grouped.append({"value": value, "label": label, "listings": category_listings[:4], "total": total})

    return render(request, "community/marketplace.html", {"listings": listings, "grouped": grouped, "categories": Listing.CATEGORIES, "conditions": Listing.CONDITIONS, "query": query, "selected_category": category, "selected_condition": condition})

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
    if blocked := needs_verified_email(request): return blocked
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
            notify_subscribers(request, listing.category, listing.title, listing.get_absolute_url(), request.user)
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
        if blocked := needs_verified_email(request): return blocked
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
                notify_subscribers(request, LOST_FOUND_ALERT, f"{item.kind}: {item.item}", reverse("lost_found"), request.user)
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

def app_manifest(request):
    return render(request, "pwa/manifest.webmanifest", content_type="application/manifest+json")

def service_worker(request):
    response = render(request, "pwa/sw.js", content_type="application/javascript")
    response["Cache-Control"] = "no-cache"
    return response

def offline(request): return render(request, "pwa/offline.html")

def visible_chat_messages(user):
    messages_qs = ChatMessage.objects.select_related("user")
    if user.is_authenticated and (user.is_staff or user.is_superuser):
        return messages_qs
    if user.is_authenticated:
        return messages_qs.filter(Q(moderation_status="approved") | Q(user=user))
    return messages_qs.filter(moderation_status="approved")

@xframe_options_sameorigin
def chat(request):
    ChatMessage.purge_old_photos()
    form = ChatMessageForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if not request.user.is_authenticated: messages.info(request, "Please log in to post in the chat."); return redirect("login")
        if not Profile.objects.get_or_create(user=request.user)[0].can_post:
            messages.error(request, "Please verify your email before posting. The link is in your inbox.")
            return redirect("chat")
        if form.is_valid():
            chat_message = form.save(commit=False)
            chat_message.user = request.user
            image = form.cleaned_data.get("image")
            status, reason = run_moderation([chat_message.body], [image])
            chat_message.moderation_status = "approved" if status == "approved" else "pending"
            chat_message.moderation_notes = reason
            if image:
                chat_message.image = shrink_photo(image)
            chat_message.save()
            if chat_message.moderation_status != "approved":
                messages.success(request, "Your message was sent to admin for review before others can see it.")
            return redirect(reverse("chat") + "#chat-bottom")

    visible = visible_chat_messages(request.user)
    query = request.GET.get("q", "").strip()[:200]
    answer, cited = None, []
    if query:
        chat_messages = with_replies(visible, list(matching_messages(visible, query).order_by("-created_at")[:15]))[:40]
        recent_photos = list(visible.filter(moderation_status="approved", created_at__gte=timezone.now() - ChatMessage.PHOTO_LIFETIME).exclude(image="").order_by("-created_at")[:4])
        answer, cited_ids = ai_answer(query, chat_messages, recent_photos)
        by_id = {m.pk: m for m in chat_messages + recent_photos}
        cited = [by_id[i] for i in cited_ids if i in by_id]
        chat_messages += [m for m in cited if m not in chat_messages]
        chat_messages.sort(key=lambda m: m.created_at, reverse=True)
    else:
        chat_messages = list(visible.order_by("-created_at")[:100])[::-1]
    return render(request, "community/chat.html", {
        "form": form,
        "chat_messages": chat_messages,
        "query": query,
        "answer": answer,
        "cited": cited,
        "can_post": request.user.is_authenticated and Profile.objects.get_or_create(user=request.user)[0].can_post,
        "last_id": max((m.pk for m in chat_messages), default=0),
    })

def chat_updates(request):
    try:
        after = int(request.GET.get("after", 0))
    except ValueError:
        after = 0
    new_messages = list(visible_chat_messages(request.user).filter(pk__gt=after).order_by("created_at")[:50])
    html = "".join(render_to_string("community/_chat_message.html", {"message": m}, request=request) for m in new_messages)
    return JsonResponse({"html": html, "last_id": new_messages[-1].pk if new_messages else after})

@login_required
def chat_delete(request, pk):
    chat_message = get_object_or_404(ChatMessage, pk=pk)
    if chat_message.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You can only delete your own messages.")
    elif request.method == "POST":
        chat_message.image.delete(save=False)
        chat_message.delete()
        messages.success(request, "Message deleted.")
    return redirect("chat")

def report_chat_message(request, pk):
    chat_message = get_object_or_404(ChatMessage, pk=pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()[:255]
        reporter = request.user if request.user.is_authenticated else None
        if reporter:
            report, created = ContentReport.objects.get_or_create(
                reporter=reporter,
                chat_message=chat_message,
                defaults={"reason": reason},
            )
            if not created and reason:
                report.reason = reason
                report.save(update_fields=["reason"])
        else:
            ContentReport.objects.create(chat_message=chat_message, reason=reason)
        chat_message.moderation_status = "pending"
        chat_message.moderation_notes = "Flagged by a community report."
        chat_message.save(update_fields=["moderation_status", "moderation_notes"])
        notify_admin_of_report(request, f"chat message by {chat_message.user.username}", reporter, reason)
        messages.success(request, "Thanks. Your report was sent to admin for review.")
    return redirect("chat")

def alerts_off(request, token):
    profile = get_object_or_404(Profile, alerts_token=token)
    if request.method == "POST":
        profile.alert_categories = []
        profile.save(update_fields=["alert_categories"])
        messages.success(request, "All email alerts are turned off. You can turn them back on from your dashboard.")
        return redirect("home")
    return render(request, "community/alerts_off.html", {"profile": profile})

@login_required
def delete_account(request):
    user = request.user
    if user.is_superuser:
        messages.error(request, "The main admin account can't be deleted from the website.")
        return redirect("dashboard")
    form = DeleteAccountForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        for chat_message in user.chat_messages.all(): chat_message.image.delete(save=False)
        for photo in ListingImage.objects.filter(listing__seller=user): photo.image.delete(save=False)
        for listing in Listing.all_objects.filter(seller=user): listing.image.delete(save=False)
        for item in LostFound.objects.filter(user=user): item.image_1.delete(save=False); item.image_2.delete(save=False)
        logout(request)
        user.delete()
        messages.success(request, "Your account and everything you posted have been deleted.")
        return redirect("home")
    return render(request, "community/delete_account.html", {"form": form})

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        profile = Profile.objects.create(user=user, phone=form.cleaned_data["phone"])
        login(request, user)
        try:
            send_verification_email(request, profile)
            messages.success(request, f"Account created! We sent a link to {user.email}. Open it to verify your email, then you can post.")
        except Exception:
            messages.warning(request, "Account created, but we couldn't send the verification email. Use Resend below to try again.")
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
    alerts_post = request.method == "POST" and request.POST.get("form_type") == "alerts"
    form = ProfileForm(request.POST if request.method == "POST" and not alerts_post else None, instance=profile)
    alerts_form = AlertSettingsForm(request.POST if alerts_post else None, initial={"alert_categories": profile.alert_categories})
    if alerts_post and alerts_form.is_valid():
        profile.alert_categories = alerts_form.cleaned_data["alert_categories"]
        profile.save(update_fields=["alert_categories"])
        messages.success(request, "Email alerts saved." if profile.alert_categories else "Email alerts turned off.")
        return redirect(reverse("dashboard") + "#email-alerts")
    if request.method == "POST" and not alerts_post and form.is_valid(): form.save(); messages.success(request, "Profile updated."); return redirect("dashboard")
    report_queryset = LostFound.objects.all() if (request.user.is_staff or request.user.is_superuser) else LostFound.objects.filter(user=request.user)
    return render(request, "community/dashboard.html", {
        "profile": profile,
        "has_phone": has_phone,
        "can_post_listing": can_post_listing,
        "phone_code_sent": bool(profile.phone_verification_sent_at),
        "profile_form": form,
        "alerts_form": alerts_form,
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
