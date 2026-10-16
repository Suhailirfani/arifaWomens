from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('marks/entry/', views.marks_entry, name='marks_entry'),
    path('report-card/<int:student_id>/<int:exam_id>/', views.progress_report, name='progress_report'),
    path('report-card/<int:student_id>/<int:exam_id>/pdf/', views.download_progress_report_pdf, name='download_progress_report_pdf'),
]
