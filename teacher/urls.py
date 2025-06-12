from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('generate_qrcode/', views.generate_course_qrcode, name='generate_qrcode'),
    path('leave/bulk_approval/', views.bulk_leave_approval, name='bulk_leave_approval'),
    path('teacher/records/', views.teacher_check_records, name='teacher_check_records'),
    # 修改为使用course_code的URL
    path('export/<str:course_code>/', views.export_attendance, name='export_attendance'),
]