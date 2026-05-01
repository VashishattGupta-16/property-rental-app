from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q
from django.forms import inlineformset_factory  # For multiple images
from .models import Rental, RentalImage         # Imported New Model
from .forms import RentalForm, UserRegisteration

# --- FORMSET CONFIGURATION ---
# Allows 5 images total (extra=5) and enforces a maximum of 5
ImageFormSet = inlineformset_factory(
    Rental, 
    RentalImage, 
    fields=('image',), 
    extra=5, 
    max_num=5, 
    can_delete=True
)

def index(request):
    return render(request, 'index.html', {'hide_navbar': True, 'hide_sidebar': True})

def rental_list(request):
    rentals = Rental.objects.all().order_by('-created_at')

    location_query = request.GET.get('location', '').strip()
    type_query = request.GET.get('type', '').strip()
    price_query = request.GET.get('max_price', '').strip()

    if location_query:
        rentals = rentals.filter(
            Q(location__icontains=location_query) | 
            Q(title__icontains=location_query) |
            Q(description__icontains=location_query)
        )

    if type_query:
        rentals = rentals.filter(property_type=type_query)

    if price_query:
        try:
            rentals = rentals.filter(price__lte=price_query)
        except ValueError:
            pass

    return render(request, 'rentalList.html', {
        'rentals': rentals,
        'search_params': request.GET 
    })

@login_required
def rental_create(request):
    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            new_rental = form.save(commit=False)
            new_rental.user = request.user
            new_rental.save()
            
            images = formset.save(commit=False)
            for img in images:
                img.rental = new_rental
                img.save()
                
            return redirect('rental_list')
    else:
        form = RentalForm()
        formset = ImageFormSet(prefix='gallery')
    
    return render(request, 'rental_form.html', {'form': form, 'formset': formset})

@login_required
def rental_edit(request, rental_id):
    rental_obj = get_object_or_404(Rental, pk=rental_id, user=request.user)
    
    if request.method == 'POST': 
        form = RentalForm(request.POST, request.FILES, instance=rental_obj)
        formset = ImageFormSet(request.POST, request.FILES, instance=rental_obj, prefix='gallery')
        
        if form.is_valid() and formset.is_valid():
            rental_obj = form.save(commit=False)
            rental_obj.user = request.user 
            rental_obj.save()
            formset.save() # Saves new images and deletions
            return redirect('rental_list')
    else: 
        form = RentalForm(instance=rental_obj)
        formset = ImageFormSet(instance=rental_obj, prefix='gallery')
        
    return render(request, 'rental_form.html', {'form': form, 'formset': formset})


def rental_contact(request, rental_id):
    # 1. Fetch the actual rental object from the DB
    rental = get_object_or_404(Rental, id=rental_id)
    
    # 2. Pass the 'rental' object to the template context
    return render(request, 'rental_contact.html', {
        'rental': rental
    })

@login_required
def rental_delete(request, rental_id):
    rental_obj = get_object_or_404(Rental, pk=rental_id, user=request.user)
    if request.method == 'POST':
        rental_obj.delete()
        return redirect('rental_list')
    return render(request, 'rentalDelete.html', {'rental': rental_obj})

def room_describe(request, rental_id):
    rental_obj = get_object_or_404(Rental, pk=rental_id)
    # The scroller will use rental_obj.gallery.all in the template
    return render(request, 'room_describe.html', {'rental': rental_obj})

def logout_success(request):
    # This renders the beautiful glassmorphism page we built
    return render(request, 'registration/logged_out.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisteration(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('rental_list')
    else:
        form = UserRegisteration()
    return render(request, 'registration/register.html', {'form': form})