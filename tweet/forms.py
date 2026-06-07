import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import inlineformset_factory
from .models import Rental, RentalImage, CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email",)

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone_number", "user_type", "is_active", "is_staff")

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = [
            'title', 'location', 'description', 'price', 'property_type', 
            'contact', 'sqft', 'bedrooms', 'bathrooms', 'furnishing', 
            'floor', 'facing', 'security_deposit', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white', 'placeholder': 'e.g. Modern Luxury Villa'}),
            'location': forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white', 'placeholder': 'City or Neighborhood'}),
            'description': forms.Textarea(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'property_type': forms.Select(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-slate-900 p-4 text-sm text-white'}),
            'contact': forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'sqft': forms.NumberInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'furnishing': forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'floor': forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'facing': forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'}),
            'image': forms.FileInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white', 'data-require-perms': 'camera,files'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove strict model validator to allow cleaning in clean_contact()
        self.fields['contact'].validators = []
        # Explicitly mark all mandatory fields for frontend/backend synchronization
        required_fields = ['title', 'location', 'description', 'price', 'property_type', 'contact', 'sqft', 'bedrooms', 'bathrooms', 'image']
        for field in required_fields:
            self.fields[field].required = True
            self.fields[field].widget.attrs['required'] = 'required'
        if self.instance.pk:
            self.fields['image'].required = False
            self.fields['image'].widget.attrs.pop('required', None)

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be a positive number.")
        return price

    def clean_sqft(self):
        sqft = self.cleaned_data.get('sqft')
        if sqft is not None and sqft <= 0:
            raise forms.ValidationError("Area (Sqft) must be greater than zero.")
        return sqft

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '')
        # Strip spaces, dashes, brackets before validating
        digits_only = re.sub(r'[\s\-\(\)\+]', '', str(contact))
        if not digits_only.isdigit() or not (10 <= len(digits_only) <= 15):
            raise forms.ValidationError(
                'Enter a valid phone number. '
                'Accepted formats: 9876543210, +91 98765 43210'
            )
        return contact

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class ProfileSetupForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'user_type', 'address', 'current_location']
        widgets = {
            field: forms.TextInput(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'})
            for field in ['first_name', 'last_name', 'phone_number', 'address', 'current_location']
        }
        widgets['user_type'] = forms.Select(attrs={'class': 'w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white'})

class RentalImageForm(forms.ModelForm):
    class Meta:
        model = RentalImage
        fields = ['image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow the formset to skip empty extra image slots
        self.fields['image'].required = False

GalleryFormSet = inlineformset_factory(
    Rental, 
    RentalImage, 
    form=RentalImageForm,
    extra=3,
    can_delete=True
)