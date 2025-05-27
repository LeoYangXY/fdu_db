# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.scan_qrcode, name='scan_qrcode'),#扫码页面
    path('validate/', views.validate_identity, name='validate_identity'),#处理过程
    path('confirm/', views.confirm_attendance, name='confirm_attendance'),#确认界面
]