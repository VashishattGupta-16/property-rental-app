from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Rental, Wishlist
from .forms import RentalForm, GalleryFormSet, ProfileSetupForm


# ================= INDEX / ELITE HOME =================
def index(request):
    """
    Renders the elite landing page with dynamic category filters.
    """
    # Fetching latest rentals for the 'Live Market' section
    featured_rentals = Rental.objects.all().order_by('-created_at')[:6]
    
    # Specific category items for the grid
    latest_villa = Rental.objects.filter(property_type='VILLA').first()
    latest_flat = Rental.objects.filter(property_type='APARTMENT').first()
    latest_pg = Rental.objects.filter(property_type='PG').first()

    return render(request, 'index.html', {
        'featured_rentals': featured_rentals,
        'latest_villa': latest_villa,
        'latest_flat': latest_flat,
        'latest_pg': latest_pg,
        'hide_navbar': False,
        'hide_sidebar': True
    })


# ================= RENTAL LIST + SEARCH =================
def rental_list(request):
    """
    Handles property browsing with advanced filtering for locations and pricing.
    """
    rentals = Rental.objects.select_related('user').all().order_by('-created_at')

    location_query = request.GET.get('location', '').strip()
    type_query = request.GET.get('type', '').strip()
    price_query = request.GET.get('max_price', '').strip()
    owner_query = request.GET.get('owner', '').strip()

    if location_query:
        rentals = rentals.filter(
            Q(location__icontains=location_query) |
            Q(title__icontains=location_query) |
            Q(description__icontains=location_query)
        )

    if owner_query == 'me' and request.user.is_authenticated:
        rentals = rentals.filter(user=request.user)

    if type_query:
        rentals = rentals.filter(property_type=type_query)

    if price_query:
        try:
            rentals = rentals.filter(price__lte=float(price_query))
        except ValueError:
            pass

    # Wishlist integration for UI heart icons
    wishlisted_rental_ids = set()
    if request.user.is_authenticated:
        wishlisted_rental_ids = set(
            request.user.wishlist_items.values_list("rental_id", flat=True)
        )

    return render(request, 'rentalList.html', {
        'rentals': rentals,
        'wishlisted_rental_ids': wishlisted_rental_ids,
        'search_params': request.GET
    })


# ================= CREATE RENTAL =================
@login_required
def rental_create(request):
    """
    Enterprise-level form handling for new property listings.
    """
    if request.method == "POST":
        form = RentalForm(request.POST, request.FILES)
        formset = GalleryFormSet(request.POST, request.FILES, prefix='gallery')

        if form.is_valid() and formset.is_valid():
            rental = form.save(commit=False)
            rental.user = request.user
            rental.save()

            formset.instance = rental
            formset.save()

            return redirect('rental_list')
    else:
        form = RentalForm()
        formset = GalleryFormSet(prefix='gallery')

    return render(request, 'rental_form.html', {
        'form': form,
        'formset': formset
    })


# ================= EDIT RENTAL =================
@login_required
def rental_edit(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)

    # Security: Ensure only the owner or staff can edit
    if rental.user != request.user and not request.user.is_staff:
        return redirect('index')

    if request.method == "POST":
        form = RentalForm(request.POST, request.FILES, instance=rental)
        formset = GalleryFormSet(request.POST, request.FILES, instance=rental, prefix='gallery')

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('rental_list')
    else:
        form = RentalForm(instance=rental)
        formset = GalleryFormSet(instance=rental, prefix='gallery')

    return render(request, 'rental_form.html', {
        'form': form,
        'formset': formset,
        'rental': rental
    })


# ================= DELETE RENTAL =================
@login_required
@require_POST
def rental_delete(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)

    if rental.user != request.user and not request.user.is_staff:
        return HttpResponse('Forbidden', status=403)

    rental.delete()
    return redirect('rental_list')


# ================= CONTACT RENTAL =================
@login_required
def rental_contact(request, rental_id):
    """
    Industrial contact page. Returns a success flag for the UI on POST.
    """
    rental = get_object_or_404(Rental, pk=rental_id)

    if request.method == "POST":
        return render(request, 'rental_contact.html', {
            'rental': rental,
            'success': True
        })

    return render(request, 'rental_contact.html', {'rental': rental})


# ================= DETAIL & PROFILE =================
def room_describe(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    return render(request, 'room_describe.html', {'rental': rental})


@login_required
def profile(request):
    user = request.user
    listings = Rental.objects.filter(user=user).order_by('-created_at')
    wishlist_count = user.wishlist_items.count()

    return render(request, 'profile.html', {
        'user': user,
        'listings': listings,
        'listings_count': listings.count(),
        'wishlist_count': wishlist_count,
    })


# ================= WISHLIST LOGIC =================
@login_required
def wishlist(request):
    wishlist_items = request.user.wishlist_items.select_related('rental').all()
    return render(request, 'wishlist.html', {
        'wishlist': wishlist_items
    })


@login_required
@require_POST
def toggle_wishlist(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    existing = Wishlist.objects.filter(user=request.user, rental=rental)
    
    if existing.exists():
        existing.delete()
    else:
        Wishlist.objects.create(user=request.user, rental=rental)

    # Redirect back to the page the user was on
    referer = request.META.get("HTTP_REFERER", "")
    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)

    return redirect("rental_list")


# ================= ONBOARDING =================
@login_required
def profile_setup(request):
    if request.user.profile_is_complete():
        return redirect('index')

    if request.method == "POST":
        form = ProfileSetupForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ProfileSetupForm(instance=request.user)

    return render(request, 'profile_setup.html', {'form': form})


# ================= UTILITY =================
def ping_view(request):
    return HttpResponse("pong", content_type="text/plain")


def about(request):
    return render(request, 'about.html')