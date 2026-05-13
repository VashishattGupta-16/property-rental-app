from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Rental, Wishlist
from .forms import RentalForm, GalleryFormSet, ProfileSetupForm


# ================= INDEX / ELITE BRAND ENTRY =================
def index(request):
    """
    Renders the commercial-standard brand landing page.
    Property queries are removed to maintain a clean, GSAP-driven entry.
    """
    return render(request, 'index.html', {
        'hide_navbar': False,
        'hide_sidebar': True,
        'is_hero_active': True
    })


# ================= RENTAL MARKETPLACE (LIST + SEARCH) =================
def rental_list(request):
    """
    The main industrial engine for property discovery and filtering.
    """
    rentals = Rental.objects.select_related('user').all().order_by('-created_at')

    # Extraction of specialized search parameters
    location_query = request.GET.get('location', '').strip()
    type_query = request.GET.get('type', '').strip()
    price_query = request.GET.get('max_price', '').strip()
    owner_query = request.GET.get('owner', '').strip()

    # Advanced Filter Logic
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

    # UI State: Identifying items already in user's wishlist
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


# ================= PROPERTY MANAGEMENT (C.U.D.) =================
@login_required
def rental_create(request):
    """
    Handles industrial-grade property ingestion with image formsets.
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


@login_required
def rental_edit(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)

    # Security Protocol: Validation of ownership
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


@login_required
@require_POST
def rental_delete(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)

    if rental.user != request.user and not request.user.is_staff:
        return HttpResponse('Unauthorized access attempt detected.', status=403)

    rental.delete()
    return redirect('rental_list')


# ================= ENGAGEMENT & PROFILES =================
@login_required
def rental_contact(request, rental_id):
    """
    Monochrome contact portal. Triggers success state on POST.
    """
    rental = get_object_or_404(Rental, pk=rental_id)

    if request.method == "POST":
        return render(request, 'rental_contact.html', {
            'rental': rental,
            'success': True
        })

    return render(request, 'rental_contact.html', {'rental': rental})


def room_describe(request, rental_id):
    """
    Surgical detail view for individual listings.
    """
    rental = get_object_or_404(Rental, pk=rental_id)
    return render(request, 'room_describe.html', {'rental': rental})


@login_required
def profile(request):
    """
    User command center for listings and analytics.
    """
    user = request.user
    listings = Rental.objects.filter(user=user).order_by('-created_at')
    
    return render(request, 'profile.html', {
        'user': user,
        'listings': listings,
        'listings_count': listings.count(),
        'wishlist_count': user.wishlist_items.count(),
    })


# ================= WISHLIST PROTOCOL =================
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

    referer = request.META.get("HTTP_REFERER", "")
    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)

    return redirect("rental_list")


# ================= UTILITY & ONBOARDING =================
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


def ping_view(request):
    return HttpResponse("System Operational", content_type="text/plain")


def about(request):
    return render(request, 'about.html')