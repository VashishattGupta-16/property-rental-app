from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Case, When, Value, BooleanField
from django.utils import timezone
from django.contrib import messages
from .models import Rental, PropertyShare, PropertyVisit, PropertyInquiry
from .models import Wishlist
from .forms import RentalForm, GalleryFormSet, ProfileSetupForm
from .decorators import hardware_permission_required
# =========================================================
# HELPERS
# =========================================================


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

    rentals = rentals.annotate(
        is_owner=Case(
            When(user_id=user.id, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
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

    # Bedroom filter
    bedrooms = request.GET.get('bedrooms', '').strip()
    if bedrooms:
        try:
            rentals = rentals.filter(bedrooms=int(bedrooms))
        except ValueError:
            pass

    # Furnishing filter
    furnishing = request.GET.get('furnishing', '').strip()
    if furnishing:
        rentals = rentals.filter(furnishing__icontains=furnishing)

    # Sort filter
    sort = request.GET.get('sort', '').strip()
    if sort == 'price_asc':
        rentals = rentals.order_by('price')
    elif sort == 'price_desc':
        rentals = rentals.order_by('-price')
    elif sort == 'newest':
        rentals = rentals.order_by('-created_at')

    if owner_query == 'me' and request.user.is_authenticated:
        rentals = rentals.filter(user=request.user)

    paginator = Paginator(rentals, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Wishlist state for current user (fast lookup)
    wishlisted_ids = set()
    if request.user.is_authenticated:
        try:
            wishlisted_ids = set(request.user.wishlist_items.values_list('rental_id', flat=True))
        except Exception:
            wishlisted_ids = set()

    # Attach boolean attribute on each rental for templates that expect `rental.is_wishlisted`
    try:
        for r in page_obj.object_list:
            setattr(r, 'is_wishlisted', (r.id in wishlisted_ids))
    except Exception:
        pass

    return render(request, 'rentalList.html', {
        'rentals': page_obj,
        'search_params': request.GET,
        'page_obj': page_obj,
        'wishlisted_ids': wishlisted_ids,
    })


# =========================================================
# RENTAL DETAIL
# =========================================================

def rental_detail(request, slug):
    rental = get_object_or_404(
        Rental.objects.select_related('user').prefetch_related('gallery'),
        slug=slug
    )

    # Determine wishlisted state (support both legacy Wishlist and M2M)
    is_wishlisted = False
    if request.user.is_authenticated:
        try:
            is_wishlisted = Wishlist.objects.filter(user=request.user, rental=rental).exists()
        except Exception:
            # Fallback to M2M if Wishlist table unavailable
            try:
                is_wishlisted = rental.wishlisted_by.filter(pk=request.user.pk).exists()
            except Exception:
                is_wishlisted = False

    return render(request, 'room_describe.html', {
        'rental': rental,
        'is_wishlisted': is_wishlisted,
    })


# =========================================================
# WISHLIST VIEWS
# =========================================================


@require_POST
def toggle_wishlist(request, rental_id):
    if not request.user.is_authenticated:
        login_url = '/accounts/login/'
        if request.headers.get('HX-Request') == 'true':
            response = HttpResponse()
            response['HX-Redirect'] = login_url
            return response
        return JsonResponse({'redirect': login_url}, status=401)

    rental = get_object_or_404(Rental, pk=rental_id)
    user = request.user

    deleted, _ = Wishlist.objects.filter(user=user, rental=rental).delete()
    if deleted:
        wishlisted = False
    else:
        Wishlist.objects.create(user=user, rental=rental)
        wishlisted = True

    if request.headers.get('HX-Request') == 'true':
        from django.middleware.csrf import get_token
        heart = 'fa-solid fa-heart text-red-500' if wishlisted else 'fa-regular fa-heart'
        toggle_url = f'/wishlist/toggle/{rental_id}/'
        csrf = get_token(request)
        html = f'''<form action="{toggle_url}" method="POST"
            class="js-wishlist-form absolute top-3 right-3 z-[100]"
            hx-post="{toggle_url}"
            hx-target="this"
            hx-swap="outerHTML"
            hx-headers=\'{{"HX-Request": "true"}}\'>
            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
            <button type="submit"
                class="wishlist-btn w-9 h-9 rounded-full bg-black/50 backdrop-blur-md border border-white/10 flex items-center justify-center text-white hover:bg-red-500/80 transition-all duration-300 active:scale-90 shadow-lg">
                <i class="{heart} text-sm"></i>
            </button>
        </form>'''
        return HttpResponse(html)

    return JsonResponse({'wishlisted': wishlisted})
@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('rental').order_by('-created_at')

    paginator = Paginator(wishlist_items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'wishlist.html', {
        'wishlist': page_obj,
    })


@login_required
@require_POST
def accept_terms(request):
    """
    API endpoint to record user's acceptance of the Terms & Conditions.
    """
    user = request.user
    if not getattr(user, 'terms_accepted_at', None):
        user.terms_accepted_at = timezone.now()
        user.save(update_fields=['terms_accepted_at'])
    return JsonResponse({'success': True})


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
    PropertyVisit.objects.create(
        share=share,
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
        'required_hardware': getattr(request, 'required_hardware', []),
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

        # Debugging block: Identifies silent validation failures
        if not (form.is_valid() and formset.is_valid()):
            import sys
            print("\n" + "="*40, file=sys.stderr)
            print("CRITICAL: Rental creation validation failed.", file=sys.stderr)
            print(f"Form Errors: {form.errors.as_json()}", file=sys.stderr)
            print(f"Formset Errors: {formset.errors}", file=sys.stderr)
            print("="*40 + "\n", file=sys.stderr)

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

    # Always render the page. Pass required_hardware to the frontend.
    return render(request, 'rental_form.html', {
        'form': form,
        'formset': formset,
        'required_hardware': getattr(request, 'required_hardware', []),
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
    listings = Rental.objects.filter(user_id=request.user.id).order_by('-created_at')
    
    return render(request, 'profile.html', {
        'user': request.user,
        'listings': listings,
        'listings_count': listings.count(),
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
# ABOUT + SYSTEM
# =========================================================

def about(request):
    return render(request, 'about.html')


def ping_view(request):
    return HttpResponse("System Operational", content_type="text/plain")


def offline(request):
    return render(request, "offline.html")
