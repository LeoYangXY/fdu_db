from django.urls import path
from . import views

urlpatterns = [
    path('admin_import/', views.admin_import, name='admin_import'),
    path('admin/download-template/<str:data_type>/', views.download_template, name='download_template'),
]