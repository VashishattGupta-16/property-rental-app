from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.contrib import messages

from .models import Rental, Wishlist
from .forms import (
    RentalForm,
    GalleryFormSet,
    ProfileSetupForm
)


# =========================================================
# HOME / ELITE LANDING PAGE
# =========================================================

# Dummy views for context - replace with actual implementations
def index(request):
    """Landing page showing featured and categorized properties."""
    featured_rentals = Rental.objects.filter(is_available=True).select_related('user').order_by('-created_at')[:6]
    latest_villa = Rental.objects.filter(property_type='VILLA', is_available=True).order_by('-created_at').first()
    latest_flat = Rental.objects.filter(property_type='APARTMENT', is_available=True).order_by('-created_at').first()
    latest_pg = Rental.objects.filter(property_type='PG', is_available=True).order_by('-created_at').first()
    latest_showroom = Rental.objects.filter(property_type='SHOWROOM', is_available=True).order_by('-created_at').first()
    premium_properties = Rental.objects.filter(price__gte=5000000, is_available=True).order_by('-created_at')[:4]

    wishlisted_rental_ids = set()
    if request.user.is_authenticated:
        wishlisted_rental_ids = set(request.user.wishlist_items.values_list('rental_id', flat=True))

    context = {
        'featured_rentals': featured_rentals,
        'latest_villa': latest_villa,
        'latest_flat': latest_flat,
        'latest_pg': latest_pg,
        'latest_showroom': latest_showroom,
        'premium_properties': premium_properties,
        'wishlisted_rental_ids': wishlisted_rental_ids,
    }
    return render(request, 'index.html', context)


def _wants_json(request):
    accept = (request.headers.get("accept") or "").lower()
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in accept
    )


# =========================================================
# RENTAL LIST + SEARCH ENGINE
# =========================================================

def rental_list(request):
    """Main rental browser with search and filtering logic."""
    rentals = Rental.objects.select_related('user').prefetch_related('gallery').filter(is_available=True).order_by('-created_at')

    search_query = request.GET.get('q', '').strip()
    location_query = request.GET.get('location', '').strip()
    property_type = request.GET.get('type', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    owner_query = request.GET.get('owner', '').strip()

    # SMART SEARCH
    if search_query:
        rentals = rentals.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query) | Q(location__icontains=search_query))

    # LOCATION FILTER
    if location_query: rentals = rentals.filter(location__icontains=location_query)

    # PROPERTY TYPE FILTER
    if property_type: rentals = rentals.filter(property_type=property_type)

    # MAX PRICE FILTER
    if max_price:
        try: rentals = rentals.filter(price__lte=float(max_price))
        except ValueError: pass

    # OWNER FILTER
    if owner_query == 'me' and request.user.is_authenticated:
        rentals = rentals.filter(user=request.user)

    # USER WISHLIST IDS
    wishlisted_rental_ids = set()
    if request.user.is_authenticated:
        wishlisted_rental_ids = set(request.user.wishlist_items.values_list('rental_id', flat=True))

    # Add an 'is_owner' flag to each rental for template rendering
    for rental in rentals:
        rental.is_owner = (request.user.is_authenticated and rental.user == request.user)

    context = {
        'rentals': rentals,
        'wishlisted_rental_ids': wishlisted_rental_ids,
        'search_params': request.GET,
    }
    return render(request, 'rentalList.html', context)

# =========================================================
# RENTAL DETAIL PAGE
# =========================================================

def rental_detail(request, slug):

    rental = get_object_or_404(
        Rental.objects
        .select_related('user')
        .prefetch_related('gallery'),
        slug=slug
    )

    return render(
        request,
        'room_describe.html',
        {
            'rental': rental,
        }
    )


def room_describe(request, rental_id):

    rental = get_object_or_404(
        Rental.objects
        .select_related('user')
        .prefetch_related('gallery'),
        pk=rental_id
    )

    return render(
        request,
        'room_describe.html',
        {
            'rental': rental,
        }
    )


# =========================================================
# EDIT PROPERTY
# =========================================================

@login_required
def rental_edit(request, slug):
    rental = get_object_or_404(
        Rental,
        slug=slug
    )

    # SECURITY LAYER
    if (
        rental.user != request.user and
        not request.user.is_staff
    ):
        return redirect('index')

    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES, instance=rental)
        formset = GalleryFormSet(request.POST, request.FILES, instance=rental, prefix='gallery')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Property updated successfully!")
            return redirect(
                'rental_detail',
                slug=rental.slug
            )

    else:

        form = RentalForm(instance=rental)

        formset = GalleryFormSet(
            instance=rental,
            prefix='gallery'
        )
    context = {
        'form': form,
        'formset': formset,
        'rental': rental,
    }
    return render(request, 'rental_form.html', context)


# =========================================================
# CREATE PROPERTY
# =========================================================

@login_required
def rental_create(request):
    if request.user.profile_is_complete():
        if request.method == 'POST':
            form = RentalForm(request.POST, request.FILES)
            formset = GalleryFormSet(request.POST, request.FILES, prefix='gallery')
            if form.is_valid() and formset.is_valid():
                rental = form.save(commit=False)
                rental.user = request.user
                rental.save()
                formset.instance = rental
                formset.save()
                messages.success(request, "Property created successfully!")
                return redirect(
                    'rental_detail',
                    slug=rental.slug
                )
        else:
            form = RentalForm()
            formset = GalleryFormSet(prefix='gallery')
        context = {
            'form': form,
            'formset': formset,
        }
        return render(request, 'rental_form.html', context)
    else:
        messages.warning(request, "Please complete your profile before creating a rental.")
        return redirect('profile_setup')


# =========================================================
# DELETE PROPERTY
# =========================================================

@login_required
@require_POST
def rental_delete(request, slug):

    rental = get_object_or_404(
        Rental,
        slug=slug
    )

    if (
        rental.user != request.user and
        not request.user.is_staff
    ):
        return HttpResponse(
            'Unauthorized Access',
            status=403
        )

    rental.delete()

    return redirect('rental_list')


# =========================================================
# CONTACT PROPERTY OWNER
# =========================================================

@login_required
def rental_contact(request, rental_id):
    rental = get_object_or_404(
        Rental, pk=rental_id
    )

    if request.method == 'POST':

        return render(
            request,
            'rental_contact.html',
            {
                'rental': rental,
                'success': True
            }
        )
    return render(
        request,
        'rental_contact.html',
        {
            'rental': rental
        }
    )


# =========================================================
# PROFILE SETUP
# =========================================================

@login_required
def profile_setup(request):

    if request.user.profile_is_complete():
        return redirect('index')

    if request.method == 'POST':

        form = ProfileSetupForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            return redirect('index')

    else:

        form = ProfileSetupForm(
            instance=request.user
        )

    return render(
        request,
        'profile_setup.html',
        {
            'form': form
        }
    )


# =========================================================
# USER PROFILE DASHBOARD
# =========================================================

@login_required
def profile(request):

    listings = (
        Rental.objects
        .filter(user=request.user)
        .order_by('-created_at')
    )

    context = {
        'user': request.user,
        'listings': listings,
        'listings_count': listings.count(),
        'wishlist_count': request.user.wishlist_items.count(),
    }
    return render(request, 'profile.html', context)

# =========================================================
# WISHLIST
# =========================================================

@login_required
def wishlist(request):

    wishlist_items = (
        request.user
        .wishlist_items
        .select_related('rental')
        .all()
    )

    return render(
        request,
        'wishlist.html',
        {
            'wishlist': wishlist_items
        }
    )


# =========================================================
# TOGGLE WISHLIST
# =========================================================

@require_POST
def toggle_wishlist(request, rental_id):

    wants_json = _wants_json(request)

    if not request.user.is_authenticated:
        next_url = request.META.get('HTTP_REFERER') or request.get_full_path()
        if wants_json:
            return JsonResponse(
                {
                    "ok": False,
                    "login_required": True,
                    "login_url": reverse("account_login"),
                    "next": next_url,
                },
                status=401,
            )
        return redirect_to_login(next_url, login_url=reverse("account_login"))

    rental = get_object_or_404(
        Rental,
        pk=rental_id
    )

    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        rental=rental
    )

    if created:
        wishlisted = True
    else:
        wishlist_item.delete()
        wishlisted = False

    if wants_json:
        return JsonResponse(
            {
                "ok": True,
                "rental_id": rental_id,
                "wishlisted": wishlisted,
                "wishlist_count": request.user.wishlist_items.count(),
            }
        )

    referer = request.META.get('HTTP_REFERER')

    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect('rental_list')


# =========================================================
# ABOUT PAGE
# =========================================================

def about(request):

    return render(
        request,
        'about.html'
    )


# =========================================================
# SYSTEM HEALTH CHECK
# =========================================================

def ping_view(request):

    return HttpResponse(
        "System Operational",
        content_type="text/plain"
    )
