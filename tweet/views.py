from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Q
from django.http import HttpResponse

from .models import Rental
from .forms import RentalForm, UserRegisteration, GalleryFormSet



def index(request):
    return render(request, 'index.html', {
        'hide_navbar': True,
        'hide_sidebar': True
    })


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
            rentals = rentals.filter(price__lte=float(price_query))
        except ValueError:
            pass

    return render(request, 'rentalList.html', {
        'rentals': rentals,
        'search_params': request.GET
    })


# ================= CREATE =================
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


# ================= EDIT (FIXED) =================
@login_required
def rental_edit(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id, user=request.user)

    if request.method == "POST":
        form = RentalForm(request.POST, request.FILES, instance=rental)
        formset = GalleryFormSet(request.POST, request.FILES, instance=rental, prefix='gallery')

        if form.is_valid() and formset.is_valid():
            rental = form.save()

            formset.instance = rental   # 🔥 CRITICAL FIX
            formset.save()

            return redirect('rental_list')

    else:
        form = RentalForm(instance=rental)
        formset = GalleryFormSet(instance=rental, prefix='gallery')

    return render(request, 'rental_form.html', {
        'form': form,
        'formset': formset
    })


# ================= DELETE =================
@login_required
def rental_delete(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id, user=request.user)

    if request.method == "POST":
        rental.delete()
        return redirect('rental_list')

    return render(request, 'rentalDelete.html', {
        'rental': rental
    })


# ================= DETAIL =================
def room_describe(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    return render(request, 'room_describe.html', {
        'rental': rental
    })


def rental_contact(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    return render(request, 'rental_contact.html', {
        'rental': rental
    })


# ================= AUTH =================
def register(request):
    if request.method == "POST":
        form = UserRegisteration(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('rental_list')
    else:
        form = UserRegisteration()

    return render(request, 'registration/register.html', {
        'form': form
    })


def logout_success(request):
    return render(request, 'registration/logged_out.html')

def ping_view(request):
    return HttpResponse("pong", content_type="text/plain")
