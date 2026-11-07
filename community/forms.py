from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .backends import find_accounts, is_locked
from .models import ChatMessage, ContactMessage, Listing, LostFound, Profile, alert_choices

def normalize_phone(value):
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise forms.ValidationError("Enter a 10-digit phone number, such as 808-348-5584.")
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data] if data else []
        cleaned = [super(MultipleImageField, self).clean(item, initial) for item in files]
        if len(cleaned) > 4:
            raise forms.ValidationError("You can upload no more than 4 photos per listing.")
        for image in cleaned:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Each photo must be 5 MB or smaller.")
        return cleaned

class BootstrapMixin:
    def apply_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"
MAX_WRONG_PASSWORDS = 4
LOCKED_MESSAGE = ("Too many wrong passwords, so this account is locked to keep it safe. "
                  "Tap \u201cForgot password?\u201d below to get a code and set a new password.")


class StyledAuthenticationForm(BootstrapMixin, AuthenticationForm):
    error_messages = {**AuthenticationForm.error_messages, "invalid_login": "That email and password don't match. Check them and try again."}
    trust_device = forms.BooleanField(required=False, label="Trust this device (stay signed in for 30 days)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update({"autocomplete": "email", "inputmode": "email", "placeholder": "name@example.com", "data-remember-email": ""})
        self.fields["trust_device"].help_text = "Don't check this on a shared or public computer."

    def clean(self):
        typed = self.cleaned_data.get("username")
        lockable = [user for user in find_accounts(typed) if not user.is_superuser]
        if any(is_locked(user) for user in lockable):
            raise forms.ValidationError(LOCKED_MESSAGE, code="locked")
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            if lockable and self.cleaned_data.get("password"):
                profile, _ = Profile.objects.get_or_create(user=lockable[0])
                profile.failed_logins += 1
                profile.login_locked = profile.failed_logins >= MAX_WRONG_PASSWORDS
                profile.save(update_fields=["failed_logins", "login_locked"])
                if profile.login_locked:
                    raise forms.ValidationError(LOCKED_MESSAGE, code="locked")
                left = MAX_WRONG_PASSWORDS - profile.failed_logins
                raise forms.ValidationError(
                    f"That email and password don't match. {left} more {'try' if left == 1 else 'tries'} before the account locks.",
                    code="invalid_login",
                )
            raise
        profile = getattr(self.get_user(), "profile", None)
        if profile and profile.failed_logins:
            profile.failed_logins = 0
            profile.save(update_fields=["failed_logins"])
        return cleaned


class CodeField(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(max_length=12, label="6-digit code", **kwargs)
        self.widget.attrs.update({
            "class": "form-control code-input", "inputmode": "numeric", "autocomplete": "one-time-code",
            "pattern": "[0-9 ]*", "placeholder": "123456", "autofocus": True,
        })

    def clean(self, value):
        digits = "".join(ch for ch in super().clean(value) if ch.isdigit())
        if len(digits) != 6:
            raise forms.ValidationError("Enter the 6 numbers from the email.")
        return digits


class VerifyCodeForm(forms.Form):
    code = CodeField()


class ResetRequestForm(BootstrapMixin, forms.Form):
    email = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "inputmode": "email", "placeholder": "name@example.com", "data-remember-email": ""})


class ResetCodeForm(BootstrapMixin, forms.Form):
    code = CodeField()
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    new_password2 = forms.CharField(label="New password again", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["code"].widget.attrs["class"] = "form-control code-input"

    def clean(self):
        cleaned = super().clean()
        first, second = cleaned.get("new_password1"), cleaned.get("new_password2")
        if first and second and first != second:
            self.add_error("new_password2", "The two passwords don't match.")
        elif first:
            try:
                validate_password(first, self.user)
            except forms.ValidationError as error:
                self.add_error("new_password1", error)
        return cleaned
class StyledPasswordResetForm(BootstrapMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
class StyledSetPasswordForm(BootstrapMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
class RegistrationForm(BootstrapMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta: model = User; fields = ["email", "first_name", "last_name", "password1", "password2"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["email"].help_text = "You'll use this to log in. Other members won't see it."
        self.fields["email"].widget.attrs.update({"autocomplete": "email", "inputmode": "email", "placeholder": "name@example.com"})
        self.fields["first_name"].required = True
        self.fields["first_name"].help_text = "Shown to other members instead of your email."
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if len(email) > 150:
            raise forms.ValidationError("That email is too long. Please use a shorter one.")
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address. Try logging in or resetting your password.")
        return email
    def _post_clean(self):
        # The email doubles as the login name, so password checks compare against it too.
        self.instance.username = self.cleaned_data.get("email", "")
        super()._post_clean()
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
class ListingForm(BootstrapMixin, forms.ModelForm):
    photos = MultipleImageField(
        required=False,
        label="Listing photos",
        help_text="Upload up to 4 photos. New photos are added to the photos already saved.",
    )
    class Meta:
        model = Listing
        fields = ["title", "category", "price", "location", "description", "contact_email", "contact_phone", "photos", "is_sold"]
        labels = {
            "contact_email": "Contact email",
            "contact_phone": "Contact phone number",
            "is_sold": "Mark this listing as sold",
        }
        help_texts = {
            "contact_email": "Buyers will see this email on the listing.",
            "contact_phone": "Optional. Buyers will see this phone number on the listing.",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        # Community Post does not require contact email or price.
        self.fields["price"].required = False
        self.fields["contact_email"].required = False
        related_count = self.instance.images.count() if self.instance.pk else 0
        self.existing_photo_count = related_count or (1 if self.instance.pk and self.instance.image else 0)
        self.fields["photos"].widget.attrs.update({"accept": "image/*", "data-max-files": 4, "data-existing-count": self.existing_photo_count})
        self.fields["contact_phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "data-phone-input": ""})
        self.fields["category"].widget.attrs.update({"data-listing-category": ""})
        self.fields["price"].widget.attrs.update({"data-listing-price": ""})
        self.fields["contact_email"].widget.attrs.update({"data-listing-email": ""})
        self.fields["price"].help_text = "Not required for Community Post or Volunteer Service."
        self.fields["contact_email"].help_text = "Optional for Community Post."
        if self.instance.pk and self.instance.contact_phone:
            try:
                self.initial["contact_phone"] = normalize_phone(self.instance.contact_phone)
            except forms.ValidationError:
                pass
        for name, field in self.fields.items():
            if field.required:
                field.widget.attrs["aria-required"] = "true"

    def clean_photos(self):
        photos = self.cleaned_data.get("photos", [])
        if self.existing_photo_count + len(photos) > 4:
            remaining = max(0, 4 - self.existing_photo_count)
            raise forms.ValidationError(f"This listing already has photos. You can add only {remaining} more.")
        return photos
    def clean_contact_phone(self):
        value = (self.cleaned_data.get("contact_phone") or "").strip()
        return normalize_phone(value) if value else ""

    def clean(self):
        cleaned_data = super().clean()
        category = (cleaned_data.get("category") or "").strip()
        price = cleaned_data.get("price")
        email = (cleaned_data.get("contact_email") or "").strip()

        # Condition is intentionally hidden from the form; keep existing on edit, default on create.
        cleaned_data["condition"] = self.instance.condition if self.instance.pk else "Good"

        if category in {"Community Post", "Volunteer Service"}:
            cleaned_data["price"] = Decimal("0.00")

        if category == "Community Post":
            return cleaned_data

        if category not in {"Community Post", "Volunteer Service"} and price in (None, ""):
            self.add_error("price", "Price is required unless category is Community Post or Volunteer Service.")
        if not email:
            self.add_error("contact_email", "Contact email is required unless category is Community Post.")

        return cleaned_data
class LostFoundForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LostFound
        fields = [
            "kind",
            "item",
            "description",
            "location",
            "date",
            "contact_name",
            "contact_method",
            "contact_phone",
            "contact_email",
            "image_1",
            "image_2",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["contact_name"].required = True
        self.fields["contact_method"].required = True
        self.fields["contact_method"].initial = self.fields["contact_method"].initial or "phone"
        self.fields["contact_phone"].required = False
        self.fields["contact_phone"].help_text = "Required if contact method is Phone."
        self.fields["contact_email"].required = False
        self.fields["contact_email"].help_text = "Required if contact method is Email."
        self.fields["location"].widget.attrs.update({"placeholder": "Gym, bar, barracks, etc."})
        self.fields["contact_phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "data-phone-input": ""})
        self.fields["contact_email"].widget.attrs.update({"autocomplete": "email", "placeholder": "name@example.com"})
        self.fields["image_1"].widget.attrs.update({"accept": "image/*"})
        self.fields["image_2"].widget.attrs.update({"accept": "image/*"})
        self.fields["image_1"].help_text = "Optional image 1"
        self.fields["image_2"].help_text = "Optional image 2"

    def clean_contact_phone(self):
        value = (self.cleaned_data.get("contact_phone") or "").strip()
        if not value:
            return ""
        return normalize_phone(value)

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get("contact_method")
        phone = (cleaned_data.get("contact_phone") or "").strip()
        email = (cleaned_data.get("contact_email") or "").strip()

        if method == "phone" and not phone:
            self.add_error("contact_phone", "Contact phone is required when Phone is selected.")
        if method == "email" and not email:
            self.add_error("contact_email", "Contact email is required when Email is selected.")

        return cleaned_data
class ProfileForm(BootstrapMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")

    class Meta: model = Profile; fields = ["phone", "department", "bio"]; widgets = {"bio": forms.Textarea(attrs={"rows": 3})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
        self.apply_styles()
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "data-phone-input": ""})
        if self.instance.pk and self.instance.phone:
            try:
                self.initial["phone"] = normalize_phone(self.instance.phone)
            except forms.ValidationError:
                pass
    def clean_phone(self):
        value = (self.cleaned_data.get("phone") or "").strip()
        return normalize_phone(value) if value else ""
    def save(self, commit=True):
        previous_phone = ""
        if self.instance.pk:
            previous_phone = Profile.objects.get(pk=self.instance.pk).phone
        profile = super().save(commit=commit)

        if (previous_phone or "").strip() != (profile.phone or "").strip():
            profile.phone_verified = False
            profile.clear_phone_verification_code()
            if commit:
                profile.save(update_fields=["phone_verified", "phone_verification_code", "phone_verification_sent_at", "phone_verification_expires_at"])

        user = self.instance.user
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        if commit:
            user.save(update_fields=["first_name", "last_name"])
        return profile

class ContactMessageForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5, "placeholder": "How can we help?"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

class ChatMessageForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ["body", "image"]
        labels = {"body": "Message", "image": "Photo"}
        widgets = {"body": forms.Textarea(attrs={"rows": 2, "placeholder": "Ask the island something, or share what you know...", "maxlength": 1000})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["image"].widget = forms.FileInput(attrs={"class": "form-control", "accept": "image/*"})

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Photos must be 10 MB or smaller.")
        return image

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get("body") or "").strip() and not cleaned_data.get("image"):
            raise forms.ValidationError("Type a message or add a photo.")
        return cleaned_data

class AlertSettingsForm(forms.Form):
    alert_categories = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Email me when someone posts in:",
    )

    alert_other = forms.BooleanField(required=False, label="Other")
    alert_keywords = forms.CharField(
        required=False, max_length=300, label="What to watch for",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. shoes, slippers, socks", "data-alert-keywords": ""}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alert_categories"].choices = alert_choices()
        self.fields["alert_other"].widget.attrs.update({"data-alert-other": ""})

    def clean(self):
        cleaned = super().clean()
        words = []
        for word in (cleaned.get("alert_keywords") or "").split(","):
            word = " ".join(word.split())
            if word and word.lower() not in [w.lower() for w in words]:
                words.append(word)
        if any(len(word) > 40 for word in words):
            self.add_error("alert_keywords", "Keep each word or phrase under 40 letters.")
        if len(words) > 10:
            self.add_error("alert_keywords", "You can watch for up to 10 things.")
        if cleaned.get("alert_other") and not words:
            self.add_error("alert_keywords", "Type what you want to hear about, like shoes or slippers.")
        cleaned["alert_keywords"] = ", ".join(words) if cleaned.get("alert_other") else ""
        return cleaned

class DeleteAccountForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}), label="Enter your password to confirm")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("That password is not correct.")
        return password
