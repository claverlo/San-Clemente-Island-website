from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Listing, LostFound, PointOfInterest, PointOfInterestPhotoRequest, Profile

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
        for field in self.fields.values(): field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
class StyledAuthenticationForm(BootstrapMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
class RegistrationForm(BootstrapMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=True, label="Phone number")
    class Meta: model = User; fields = ["username", "first_name", "last_name", "email", "phone", "password1", "password2"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "data-phone-input": ""})
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email address.")
        return email
    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])
class ListingForm(BootstrapMixin, forms.ModelForm):
    photos = MultipleImageField(
        required=False,
        label="Listing photos",
        help_text="Upload up to 4 photos. New photos are added to the photos already saved.",
    )
    class Meta:
        model = Listing
        fields = ["title", "category", "condition", "price", "location", "description", "contact_email", "contact_phone", "photos", "is_sold"]
        labels = {
            "contact_email": "Seller contact email",
            "contact_phone": "Seller contact phone number",
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
        related_count = self.instance.images.count() if self.instance.pk else 0
        self.existing_photo_count = related_count or (1 if self.instance.pk and self.instance.image else 0)
        self.fields["photos"].widget.attrs.update({"accept": "image/*", "data-max-files": 4, "data-existing-count": self.existing_photo_count})
        self.fields["contact_phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel", "data-phone-input": ""})
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
        return normalize_phone(self.cleaned_data["contact_phone"])
class LostFoundForm(BootstrapMixin, forms.ModelForm):
    class Meta: model = LostFound; fields = ["kind", "item", "description", "location", "date"]; widgets = {"date": forms.DateInput(attrs={"type": "date"})}
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs); self.apply_styles()
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
        profile = super().save(commit=commit)
        user = self.instance.user
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        if commit:
            user.save(update_fields=["first_name", "last_name"])
        return profile

class PointOfInterestForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = PointOfInterest
        fields = ["title", "description", "latitude", "longitude", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["latitude"].widget.attrs.update({"step": "any"})
        self.fields["longitude"].widget.attrs.update({"step": "any"})
        self.fields["title"].required = False
        self.fields["title"].help_text = "Leave blank to auto-name it from the clicked location."

    def clean(self):
        cleaned_data = super().clean()
        title = (cleaned_data.get("title") or "").strip()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        if not title and latitude is not None and longitude is not None:
            cleaned_data["title"] = f"Point of interest at {latitude:.4f}, {longitude:.4f}"
        return cleaned_data

class PointOfInterestPhotoRequestForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = PointOfInterestPhotoRequest
        fields = ["caption", "image"]
        widgets = {"caption": forms.TextInput(attrs={"placeholder": "Short note for approval"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
