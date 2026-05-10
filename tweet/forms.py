from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import inlineformset_factory

from .models import Rental, CustomUser, RentalImage


# =========================
# CUSTOM WIDGETS
# =========================
class ColorStyledSelect(forms.Select):
   
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # Force dropdown options to be black for readability against a white background.
        option['attrs']['style'] = 'color: black; background-color: white;'
        return option

# =========================
# RENTAL FORM
# =========================
class RentalForm(forms.ModelForm):

    image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            "accept": "image/*",
            "class": "main-image-input"
        })
    )

    class Meta:
        model = Rental
        fields = [
            "title",
            "property_type",
            "price",
            "location",
            "address",
            "description",
            "furnishing",
            "sqft",
            "floor",
            "facing",
            "image",
            "contact",
            "bedrooms",
            "bathrooms",
]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "price": forms.NumberInput(),
            "sqft": forms.NumberInput(),
            "property_type": ColorStyledSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base_classes = (
            "w-full rounded-2xl border px-6 py-4 "
            "bg-[var(--input-bg)] text-[var(--text-main)] "
            "outline-none transition duration-300 "
            "focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10"
        )

        for name, field in self.fields.items():
            if not field.widget.is_hidden:
                if name != "image":
                    field.widget.attrs["class"] = base_classes

                if name == "property_type":
                    # The main select text should be white.
                    field.widget.attrs["class"] += " text-white"

                label = field.label or name.replace("_", " ")
                field.widget.attrs.setdefault(
                    "placeholder",
                    f"Enter {label.lower()}..."
                )


# =========================
# GALLERY FORMSET
# =========================
GalleryFormSet = inlineformset_factory(
    Rental,
    RentalImage,
    fields=("image",),
    extra=5,
    max_num=5,
    can_delete=True,
    widgets={
        "image": forms.FileInput(attrs={
            "accept": "image/*",
            "class": "gallery-photo-input"
        })
    }
)


# =========================
# ADMIN FORMS
# =========================
class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("email", "phone_number")


class CustomUserChangeForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = "__all__"


# =========================
# REGISTER FORM
# =========================
class UserRegisteration(UserCreationForm):

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")

        if commit:
            user.save()

        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        auth_classes = (
            "w-full rounded-2xl border px-6 py-4 "
            "bg-[var(--input-bg)] text-[var(--text-main)] "
            "outline-none focus:border-sky-500"
        )

        for name, field in self.fields.items():
            field.widget.attrs["class"] = auth_classes

            label = field.label or name.replace("_", " ")
            field.widget.attrs.setdefault(
                "placeholder",
                f"Enter {label.lower()}..."
            )