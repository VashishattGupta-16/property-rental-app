from . import views
from django.urls import path 
from .views import ping_view

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/create/', views.rental_create, name='rental_create'),
    path('rentals/<int:rental_id>/edit/', views.rental_edit, name='rental_edit'),
    path('rentals/<int:rental_id>/delete/', views.rental_delete, name='rental_delete'),
    path('rentals/<int:rental_id>/contact/', views.rental_contact, name='rental_contact'),
    path('rentals/<int:rental_id>/', views.room_describe, name='room_describe'),
    path('register/', views.register, name='register'),
    path('logged-out/', views.logout_success, name='logout_success'),
    path('ping/', ping_view, name='ping'),
]
