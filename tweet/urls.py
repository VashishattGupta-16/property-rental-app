from django.urls import path
from . import views


urlpatterns = [

    # ================= HOME =================

    path(
        '',
        views.index,
        name='home'
    ),

    # ================= RENTAL LIST =================

    path(
        'rentals/',
        views.rental_list,
        name='rental_list'
    ),

    # ================= PROPERTY DETAIL =================

    path(
        'property/<slug:slug>/',
        views.rental_detail,
        name='rental_detail'
    ),

    # ================= CREATE PROPERTY =================

    path(
        'property/create/',
        views.rental_create,
        name='rental_create'
    ),

    # ================= EDIT PROPERTY =================

    path(
        'property/<slug:slug>/edit/',
        views.rental_edit,
        name='rental_edit'
    ),

    # ================= DELETE PROPERTY =================

    path(
        'property/<slug:slug>/delete/',
        views.rental_delete,
        name='rental_delete'
    ),

    # ================= CONTACT OWNER =================

    path(
        'property/<slug:slug>/contact/',
        views.rental_contact,
        name='rental_contact'
    ),

    # ================= PROFILE =================

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'profile/setup/',
        views.profile_setup,
        name='profile_setup'
    ),

    # ================= WISHLIST =================

    path(
        'wishlist/',
        views.wishlist,
        name='wishlist'
    ),

    path(
        'wishlist/toggle/<slug:slug>/',
        views.toggle_wishlist,
        name='toggle_wishlist'
    ),

    # ================= ABOUT =================

    path(
        'about/',
        views.about,
        name='about'
    ),

    # ================= HEALTH CHECK =================

    path(
        'ping/',
        views.ping_view,
        name='ping'
    ),

]