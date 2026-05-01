from django import forms
from .models import Rental, CustomUser, RentalImage
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory

class RentalForm(forms.ModelForm):
    # 1. Define the main image separately with a clean widget
    image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={'accept': 'image/*', 'class': 'main-image-input'})
    )

    class Meta:
        model = Rental
        # Ensure these match your models.py exactly
        fields = [
            'title', 'property_type', 'price', 'location', 
            'address', 'description', 'furnishing', 
            'sqft', 'floor', 'facing', 'image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(),
            'sqft': forms.NumberInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Design system tokens for text/select inputs
        text_input_classes = (
            'w-full rounded-2xl border transition-all duration-300 '
            'px-6 py-4 focus:outline-none outline-none '
            'bg-[var(--input-bg)] border-[var(--surface-border)] text-[var(--text-main)] '
            'placeholder:opacity-30 focus:border-sky-500 focus:ring-4 focus:ring-sky-500/5'
        )

        for field_name, field in self.fields.items():
            # Skip hidden fields
            if field.widget.is_hidden:
                continue

            # THE CRITICAL FIX: Only apply text styling to non-file fields
            if field_name != 'image':
                field.widget.attrs.update({'class': text_input_classes})
            
            # Safe Label & Placeholder logic
            # Using get() to avoid any potential NoneType errors
            label_text = field.label if field.label else field_name.replace('_', ' ')
            
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = f"Enter {label_text.lower()}..."

# --- MULTI-IMAGE GALLERY ---
# Using a clear prefix ensures this doesn't clash with the main form
GalleryFormSet = inlineformset_factory(
    Rental, 
    RentalImage, 
    fields=('image',), 
    extra=5, 
    max_num=5,
    can_delete=True,
    widgets={'image': forms.FileInput(attrs={'accept': 'image/*', 'class': 'gallery-photo-input'})}
)

class UserRegisteration(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        auth_classes = 'w-full rounded-2xl border bg-[var(--input-bg)] px-6 py-4 text-[var(--text-main)] outline-none focus:border-sky-500'
        for field in self.fields.values():
            field.widget.attrs.update({'class': auth_classes})