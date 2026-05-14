from django.urls import path
from . import views

urlpatterns = [

    # ================= HOME =================
    # Public facing pages
    path('', views.index, name='index'),

    # ================= RENTALS =================
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/<int:rental_id>/', views.room_describe, name='room_describe'),

    # ================= PROPERTY CRUD =================
    path('property/create/', views.rental_create, name='rental_create'),
    path('property/<slug:slug>/edit/', views.rental_edit, name='rental_edit'),
    path('property/<slug:slug>/delete/', views.rental_delete, name='rental_delete'),

    # ================= PROPERTY DETAIL =================
    path('property/<slug:slug>/', views.rental_detail, name='rental_detail'),

    # ================= CONTACT =================
    path('rentals/<int:pk>/', views.room_describe, name='room_describe'),
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
