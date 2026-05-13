from django.urls import path
from . import views

urlpatterns = [

    # ================= HOME =================
    path('', views.index, name='index'),

    # ================= RENTALS =================
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/<int:rental_id>/', views.room_describe, name='room_describe'),

    # ================= PROPERTY DETAIL =================
    path('property/<slug:slug>/', views.rental_detail, name='rental_detail'),

    # ================= PROPERTY CRUD =================
    path('property/create/', views.rental_create, name='rental_create'),
    path('property/<int:rental_id>/edit/', views.rental_edit, name='rental_edit'),
    path('property/<int:rental_id>/delete/', views.rental_delete, name='rental_delete'),

    # ================= CONTACT =================
    path('rentals/<int:rental_id>/contact/', views.rental_contact, name='rental_contact'),

    # ================= USER =================
    path('profile/', views.profile, name='profile'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),

    # ================= WISHLIST =================
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:rental_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # ================= ABOUT =================
    path('about/', views.about, name='about'),

    # ================= HEALTH CHECK =================
    path('ping/', views.ping_view, name='ping'),
]
