from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from .models import Rental
from .forms import RentalForm, UserRegisteration, GalleryFormSet


# ================= INDEX / HOME =================
def index(request):
    return render(request, 'index.html', {
        'hide_navbar': False,
        'hide_sidebar': True
    })


# ================= RENTAL LIST + SEARCH =================
def rental_list(request):
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

    return render(request, 'rentalList.html', {
        'rentals': rentals,
        'search_params': request.GET
    })


# ================= CREATE RENTAL =================
@login_required
def rental_create(request):
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
    rental = get_object_or_404(Rental, pk=rental_id)

    if request.method == "POST":
        return render(request, 'rental_contact.html', {
            'rental': rental,
            'success': True
        })

    return render(request, 'rental_contact.html', {'rental': rental})


# ================= RENTAL DETAIL =================
def room_describe(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    return render(request, 'room_describe.html', {'rental': rental})


# ================= PROFILE =================
@login_required
def profile(request):
    user = request.user
    user_rentals = Rental.objects.filter(user=user).order_by('-created_at')

    return render(request, 'profile.html', {
        'user': user,
        'rentals': user_rentals
    })


# ================= WISHLIST =================
@login_required
def wishlist(request):
    """
    Assumes User model has:
    wishlist = ManyToManyField(Rental, blank=True)
    """
    wishlist_items = request.user.wishlist.all()

    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items
    })


# ================= AUTH =================
def register(request):
    if request.method == "POST":
        form = UserRegisteration(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserRegisteration()

    return render(request, 'registration/register.html', {'form': form})


def logout_success(request):
    return render(request, 'registration/logout_success.html')


# ================= UTILITY =================
def ping_view(request):
    return HttpResponse("pong", content_type="text/plain")


def about(request):
    return render(request, 'about.html')