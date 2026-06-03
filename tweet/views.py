from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Case, When, Value, BooleanField, Exists, OuterRef
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.contrib import messages
from .models import Rental, Wishlist, PropertyShare, PropertyVisit, PropertyInquiry
from .forms import RentalForm, GalleryFormSet, ProfileSetupForm
from .tasks import record_property_visit


# =========================================================
# HELPERS
# =========================================================


def _wants_json(request):
    accept = (request.headers.get("accept") or "").lower()
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in accept
    )


def _is_htmx(request):
    return (request.headers.get("HX-Request") or "").lower() == "true"


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
    user = request.user
    rentals = (
        Rental.objects
        .filter(is_available=True)
        .order_by('-created_at')
    )

    if user.is_authenticated:
        rentals = rentals.annotate(
            is_owner=Case(
                When(user_id=user.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            is_wishlisted=Exists(
                Wishlist.objects.filter(user_id=user.id, rental_id=OuterRef("pk"))
            ),
        )
    else:
        rentals = rentals.annotate(
            is_owner=Value(False, output_field=BooleanField()),
            is_wishlisted=Value(False, output_field=BooleanField()),
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

    paginator = Paginator(rentals, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)
    pagination_query = pagination_params.urlencode()

    return render(request, 'rentalList.html', {
        'rentals': page_obj,
        'search_params': request.GET,
        'page_obj': page_obj,
        'pagination_query': pagination_query,
    })


# =========================================================
# RENTAL DETAIL
# =========================================================

def rental_detail(request, slug):
    rental = get_object_or_404(
        Rental.objects.select_related('user').prefetch_related('gallery'),
        slug=slug
    )

    # Determine if the current user has wishlisted this rental
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user_id=request.user.id, rental_id=rental.id).exists()

    # DEBUG: log detail view wishlist state
    print("[rental_detail] User:", request.user, "Authenticated:", request.user.is_authenticated, "is_wishlisted:", is_wishlisted)

    return render(request, 'room_describe.html', {
        'rental': rental,
        'is_wishlisted': is_wishlisted,
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
    rental = get_object_or_404(Rental.objects.only("id"), slug=slug)
    platform = request.POST.get('platform')

    if not platform:
        return JsonResponse({'error': 'Platform not specified'}, status=400)

    share = PropertyShare.objects.create(
        user_id=request.user.id if request.user.is_authenticated else None,
        property_id=rental.id,
        platform=platform
    )

    return JsonResponse({'share_id': share.id})


def track_visit(request, share_id):
    """
    This is the destination for a shared link. It records the visit,
    attributes it to the original share, and redirects to the property.
    """
    share = get_object_or_404(
        PropertyShare.objects.select_related('property').only('id', 'property__slug'),
        pk=share_id,
    )

    # Offload write to background task for instant redirect performance
    record_property_visit.delay(
        share_id=share.id,
        user_id=request.user.id if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return redirect('rental_detail', slug=share.property.slug)

# =========================================================
# EDIT PROPERTY
# =========================================================

@login_required
def rental_edit(request, slug):
    rental = get_object_or_404(Rental, slug=slug)

    if rental.user_id != request.user.id and not request.user.is_staff:
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
        'formset': formset,
    })


# =========================================================
# DELETE PROPERTY
# =========================================================

@login_required
@require_POST
def rental_delete(request, slug):
    rental = get_object_or_404(Rental.objects.only("id", "slug", "user_id"), slug=slug)

    if rental.user_id != request.user.id and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)

    rental.delete()
    return redirect('rental_list')


# =========================================================
# CONTACT
# =========================================================

@login_required
def rental_contact(request, rental_id):
    rental = get_object_or_404(Rental.objects.select_related('user'), pk=rental_id)
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
                visit = PropertyVisit.objects.only('id').get(pk=visit_id)
            except PropertyVisit.DoesNotExist:
                visit = None # The visit might have been deleted, proceed without it

        PropertyInquiry.objects.create(
            visit=visit, property_id=rental.id, name=name, phone=phone, message=message
        )
        success = True

    return render(request, 'rental_contact.html', {
        'rental': rental,
        'success': success,
    })


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):
    listings = (
        Rental.objects
        .filter(user_id=request.user.id)
        .only('id', 'title', 'slug', 'image', 'location', 'price', 'created_at')
        .order_by('-created_at')
    )
    paginator = Paginator(listings, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'profile.html', {
        'user': request.user,
        'listings': page_obj,
        'page_obj': page_obj,
        'listings_count': paginator.count,
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
        'form': form,
    })


# =========================================================
# WISHLIST
# =========================================================

@login_required
def wishlist(request):
    # DEBUG: Log wishlist access and current user
    print("[wishlist_view] User:", request.user)
    print("[wishlist_view] Authenticated:", request.user.is_authenticated)

    wishlist_items = (
        request.user.wishlist_items
        .select_related('rental')
        .only(
            'id',
            'created_at',
            'rental__id',
            'rental__slug',
            'rental__title',
            'rental__image',
            'rental__location',
            'rental__price',
        )
        .order_by('-created_at')
    )
    paginator = Paginator(wishlist_items, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'wishlist.html', {
        'wishlist': page_obj,
        'page_obj': page_obj,
    })


@require_POST
def toggle_wishlist(request, rental_id):
    if not request.user.is_authenticated:
        login_url = reverse("account_login")
        # Return JSON 401 for both AJAX and HTMX to allow client-side handling
        if _is_htmx(request) or _wants_json(request):
            # Note: layout.html JS handles response.status === 401
            return JsonResponse({"login_url": login_url}, status=401)
        return redirect_to_login(request.get_full_path(), login_url)

    rental = get_object_or_404(Rental.objects.only("id"), pk=rental_id)

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Wishlist toggle attempt: User {request.user.id} for Rental {rental_id}")

    # DEBUG: Log basic request and identifiers to help trace wishlist flow
    print("[wishlist] User:", request.user)
    print("[wishlist] Authenticated:", request.user.is_authenticated)
    print("[wishlist] Rental ID (param):", rental_id)

    # DEBUG: Log request headers relevant to AJAX/HTMX/CSRF
    try:
        hdrs = {k: v for k, v in request.headers.items() if k.lower().startswith(('x-', 'hx-', 'accept', 'cookie'))}
        print("[wishlist][HEADERS]", hdrs)
    except Exception:
        print("[wishlist][HEADERS] unable to read headers")

    try:
        obj, created = Wishlist.objects.get_or_create(
            user_id=request.user.id,
            rental_id=rental.id
        )
    except Exception as e:
        # Log and return JSON 500 for AJAX callers so frontend can show error
        print("[wishlist][ERROR] get_or_create failed:", repr(e))
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": str(e)}, status=500)
        messages.error(request, "Unable to update wishlist at this time.")
        return redirect('rental_list')

    # DEBUG: Log whether a new wishlist record was created or an existing one removed
    print("[wishlist] Wishlist Created:", created, "Wishlist ID:", getattr(obj, 'id', None))

    if not created:
        try:
            obj.delete()
        except Exception as e:
            print("[wishlist][ERROR] delete failed:", repr(e))
            if _wants_json(request):
                return JsonResponse({"ok": False, "error": str(e)}, status=500)
            messages.error(request, "Unable to update wishlist at this time.")
            return redirect('rental_list')
        wishlisted = False
    else:
        wishlisted = True

    if _is_htmx(request):
        return HttpResponse(status=204) # 204 prevents HTMX from swapping anything if we handle deletion via JS/OOB

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


def offline(request):
    return render(request, "offline.html")
