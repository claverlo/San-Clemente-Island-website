from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from .models import ContactMessage, Listing, LostFound, Profile

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
class StyledAuthenticationForm(BootstrapMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
class StyledPasswordResetForm(BootstrapMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
class StyledSetPasswordForm(BootstrapMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
class RegistrationForm(BootstrapMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=False, label="Phone number (required to post)")
    consent_privacy = forms.BooleanField(
        required=True,
        label=(
            "I understand that text/email messages may be sent for account and listing activity, "
            "and my phone number will not be sold or shared with third-party marketing services."
        ),
        error_messages={"required": "You must accept the privacy disclaimer before signing up."},
    )
    class Meta: model = User; fields = ["username", "first_name", "last_name", "email", "phone", "password1", "password2"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "data-phone-input": ""})
        self.fields["phone"].help_text = "Optional for signup. Required before posting listings."
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email
    def clean_phone(self):
        value = (self.cleaned_data.get("phone") or "").strip()
        if not value:
            return ""
        return normalize_phone(value)
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
            "contact_phone": "Buyers will see this phone number on the listing.",
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
        return normalize_phone(value)

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
        return normalize_phone(self.cleaned_data["phone"])
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
