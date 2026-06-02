from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("rentals/", views.rental_list, name="rental_list"),
    path("rentals/create/", views.rental_create, name="rental_create"),
    path("rentals/<slug:slug>/", views.rental_detail, name="rental_detail"),
    path("rentals/<slug:slug>/edit/", views.rental_edit, name="rental_edit"),
    path("rentals/<slug:slug>/delete/", views.rental_delete, name="rental_delete"),
    path("rentals/<int:rental_id>/contact/", views.rental_contact, name="rental_contact"),
    # Share and Visit Tracking URLs
    path("api/share/<slug:slug>/", views.create_share_link, name="create_share_link"),
    path("track/<int:share_id>/", views.track_visit, name="track_visit"),

    path("profile/", views.profile, name="profile"),
    path("profile/setup/", views.profile_setup, name="profile_setup"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:rental_id>/", views.toggle_wishlist, name="toggle_wishlist"),

    path("about/", views.about, name="about"),
    path("offline/", views.offline, name="offline"),
    path("ping/", views.ping_view, name="ping"),
]
