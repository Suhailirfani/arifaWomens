from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.fee_dashboard, name='fee_dashboard'),
    path('master/', views.fee_master, name='fee_master'),
    path('structures/builder/', views.fee_structure_builder, name='fee_structure_builder'),
    path('structures/<int:pk>/builder/', views.fee_structure_builder, name='fee_structure_builder_edit'),
    path('structures/add/', views.fee_structure_create, name='fee_structure_create'),
    path('structures/<int:pk>/edit/', views.fee_structure_edit, name='fee_structure_edit'),
    path('structures/<int:pk>/delete/', views.fee_structure_delete, name='fee_structure_delete'),
    path('installments/add/', views.fee_installment_create, name='fee_installment_create'),
    path('installments/<int:pk>/edit/', views.fee_installment_edit, name='fee_installment_edit'),
    path('installments/<int:pk>/delete/', views.fee_installment_delete, name='fee_installment_delete'),
    path('installments/<int:pk>/set-active/', views.fee_installment_set_active, name='fee_installment_set_active'),
    path('auto-sync-dues/', views.fee_auto_sync_dues, name='fee_auto_sync_dues'),
    path('categories/add/', views.fee_category_create, name='fee_category_create'),
    path('defaulters/', views.fee_defaulters_list, name='fee_defaulters_list'),
    path('defaulters/pdf/', views.download_defaulters_pdf, name='download_defaulters_pdf'),
    path('collect/', views.fee_collect, name='fee_collect'),
    path('receipt/<str:receipt_number>/', views.receipt_detail, name='receipt_detail'),
    path('receipt/<str:receipt_number>/pdf/', views.receipt_pdf, name='receipt_pdf'),

    # Monthly Vehicle Transport Fees & Bus Stops
    path('vehicle/', views.vehicle_fee_dashboard, name='vehicle_fee_dashboard'),
    path('vehicle/stops/add/', views.bus_stop_create, name='bus_stop_create'),
    path('vehicle/stops/<int:pk>/edit/', views.bus_stop_edit, name='bus_stop_edit'),
    path('vehicle/stops/<int:pk>/delete/', views.bus_stop_delete, name='bus_stop_delete'),
    path('vehicle/passes/add/', views.vehicle_pass_create, name='vehicle_pass_create'),
    path('vehicle/passes/<int:pk>/edit/', views.vehicle_pass_edit, name='vehicle_pass_edit'),
    path('vehicle/passes/<int:pk>/delete/', views.vehicle_pass_delete, name='vehicle_pass_delete'),
    path('vehicle/dues/<int:pk>/customize/', views.vehicle_fee_customize, name='vehicle_fee_customize'),
    path('vehicle/dues/generate/', views.vehicle_dues_generate, name='vehicle_dues_generate'),
    path('vehicle/settings/', views.vehicle_billing_setting_update, name='vehicle_billing_setting_update'),
    path('vehicle/defaulters/pdf/', views.download_vehicle_defaulters_pdf, name='download_vehicle_defaulters_pdf'),
]
