from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_import/', views.admin_import, name='admin_import'),
    path('admin/download-template/<str:data_type>/', views.download_template, name='download_template'),
]