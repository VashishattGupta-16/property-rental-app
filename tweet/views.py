from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.contrib import messages

from .models import Rental, Wishlist, PropertyShare, PropertyVisit, PropertyInquiry
from .forms import RentalForm, GalleryFormSet, ProfileSetupForm


# =========================================================
# HELPERS
# =========================================================

def _wants_json(request):
    accept = (request.headers.get("accept") or "").lower()
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in accept
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# =========================================================
# HOME
# =========================================================

def index(request):
    return render(request, 'index.html')


# =========================================================
# RENTAL LIST + SEARCH
# =========================================================

def rental_list(request):
    rentals = (
        Rental.objects
        .select_related('user')
        .prefetch_related('gallery')
        .filter(is_available=True)
        .order_by('-created_at')
    )

    search_query = request.GET.get('q', '').strip()
    location_query = request.GET.get('location', '').strip()
    property_type = request.GET.get('type', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    owner_query = request.GET.get('owner', '').strip()

    if search_query:
        rentals = rentals.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    if location_query:
        rentals = rentals.filter(location__icontains=location_query)

    if property_type:
        rentals = rentals.filter(property_type=property_type)

    if max_price:
        try:
            rentals = rentals.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if owner_query == 'me' and request.user.is_authenticated:
        rentals = rentals.filter(user=request.user)

    wishlisted_ids = set()
    if request.user.is_authenticated:
        wishlisted_ids = set(
            request.user.wishlist_items.values_list('rental_id', flat=True)
        )

    for rental in rentals:
        rental.is_owner = (
            request.user.is_authenticated and rental.user == request.user
        )

    return render(request, 'rentalList.html', {
        'rentals': rentals,
        'wishlisted_rental_ids': wishlisted_ids,
        'search_params': request.GET,
    })


# =========================================================
# RENTAL DETAIL
# =========================================================

def rental_detail(request, slug):
    rental = get_object_or_404(
        Rental.objects.select_related('user').prefetch_related('gallery'),
        slug=slug
    )

    return render(request, 'room_describe.html', {
        'rental': rental
    })


# =========================================================
# SHARE & VISIT TRACKING
# =========================================================

@require_POST
def create_share_link(request, slug):
    """
    API endpoint to log a share action and return a unique share ID.
    The frontend calls this via POST, gets a share_id, and constructs
    the shareable URL.
    """
    rental = get_object_or_404(Rental, slug=slug)
    platform = request.POST.get('platform')

    if not platform:
        return JsonResponse({'error': 'Platform not specified'}, status=400)

    share = PropertyShare.objects.create(
        user=request.user if request.user.is_authenticated else None,
        property=rental,
        platform=platform
    )

    return JsonResponse({'share_id': share.id})


def track_visit(request, share_id):
    """
    This is the destination for a shared link. It records the visit,
    attributes it to the original share, and redirects to the property.
    """
    share = get_object_or_404(PropertyShare.objects.select_related('property'), pk=share_id)

    visit = PropertyVisit.objects.create(
        share=share,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    request.session['property_visit_id'] = visit.pk
    return redirect('rental_detail', slug=share.property.slug)

# =========================================================
# EDIT PROPERTY
# =========================================================

@login_required
def rental_edit(request, slug):
    rental = get_object_or_404(Rental, slug=slug)

    if rental.user != request.user and not request.user.is_staff:
        return redirect('index')

    if request.method == 'POST':
        form = RentalForm(request.POST, request.FILES, instance=rental)
        formset = GalleryFormSet(request.POST, request.FILES, instance=rental, prefix='gallery')

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Property updated successfully!")
            return redirect('rental_detail', slug=rental.slug)

    else:
        form = RentalForm(instance=rental)
        formset = GalleryFormSet(instance=rental, prefix='gallery')

    return render(request, 'rental_form.html', {
        'form': form,
        'formset': formset,
        'rental': rental
    })


# =========================================================
# CREATE PROPERTY
# =========================================================

@login_required
def rental_create(request):
    if not request.user.profile_is_complete():
        messages.warning(request, "Complete profile first.")
        return redirect('profile_setup')

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
            return redirect('rental_detail', slug=rental.slug)

    else:
        form = RentalForm()
        formset = GalleryFormSet(prefix='gallery')

    return render(request, 'rental_form.html', {
        'form': form,
        'formset': formset
    })


# =========================================================
# DELETE PROPERTY
# =========================================================

@login_required
@require_POST
def rental_delete(request, slug):
    rental = get_object_or_404(Rental, slug=slug)

    if rental.user != request.user and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)

    rental.delete()
    return redirect('rental_list')


# =========================================================
# CONTACT
# =========================================================

@login_required
def rental_contact(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    success = False

    if request.method == 'POST':
        # This is a simplified example. Use a Django Form for production.
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        # Get the visit_id from the session if it exists
        visit_id = request.session.get('property_visit_id')
        visit = None
        if visit_id:
            try:
                visit = PropertyVisit.objects.get(pk=visit_id)
            except PropertyVisit.DoesNotExist:
                visit = None # The visit might have been deleted, proceed without it

        PropertyInquiry.objects.create(
            visit=visit, property=rental, name=name, phone=phone, message=message
        )
        success = True

    return render(request, 'rental_contact.html', {
        'rental': rental, 'success': success
    })


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):
    listings = Rental.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'profile.html', {
        'user': request.user,
        'listings': listings,
        'listings_count': listings.count(),
        'wishlist_count': request.user.wishlist_items.count(),
    })


@login_required
def profile_setup(request):
    if request.user.profile_is_complete():
        return redirect('index')

    form = ProfileSetupForm(request.POST or None, instance=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('index')

    return render(request, 'profile_setup.html', {
        'form': form
    })


# =========================================================
# WISHLIST
# =========================================================

@login_required
def wishlist(request):
    wishlist_items = request.user.wishlist_items.select_related('rental')

    return render(request, 'wishlist.html', {
        'wishlist': wishlist_items
    })


@require_POST
def toggle_wishlist(request, rental_id):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), reverse("index"))

    rental = get_object_or_404(Rental, pk=rental_id)

    obj, created = Wishlist.objects.get_or_create(
        user=request.user,
        rental=rental
    )

    if not created:
        obj.delete()
        wishlisted = False
    else:
        wishlisted = True

    if _wants_json(request):
        return JsonResponse({
            "ok": True,
            "wishlisted": wishlisted,
            "wishlist_count": request.user.wishlist_items.count()
        })

    return redirect('rental_list')


# =========================================================
# ABOUT + SYSTEM
# =========================================================

def about(request):
    return render(request, 'about.html')


def ping_view(request):
    return HttpResponse("System Operational", content_type="text/plain")