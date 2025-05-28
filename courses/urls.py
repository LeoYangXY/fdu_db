from django.urls import path
from . import views

urlpatterns = [
    path('generate_qrcode/', views.generate_course_qrcode, name='generate_qrcode'),#生成扫码界面
]