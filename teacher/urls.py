from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    path('generate_qrcode/', views.generate_course_qrcode, name='generate_qrcode'),#生成扫码界面

    path('leave/bulk_approval/', views.bulk_leave_approval, name='bulk_leave_approval'),  # 教师管理请假(查看+审批)

    # 教师查询考勤
    path('teacher/records/', views.teacher_check_records, name='teacher_check_records'),
]