from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('add/', views.staff_create, name='staff_create'),
    path('<int:staff_id>/', views.staff_profile, name='staff_profile'),
    path('<int:staff_id>/edit/', views.staff_edit, name='staff_edit'),
    path('<int:staff_id>/delete/', views.staff_delete, name='staff_delete'),
]
