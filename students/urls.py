from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.student_create, name='student_create'),
    path('<int:student_id>/', views.student_profile, name='student_profile'),
    path('<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('<int:student_id>/delete/', views.student_delete, name='student_delete'),
    path('bulk-upload/', views.student_bulk_upload, name='student_bulk_upload'),
    path('template/download/', views.download_student_template, name='download_template'),
]
