# attendance/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('scan/<str:course_code>/<str:timestamp>/<str:limit>/', views.scan_qrcode_with_params, name='scan_qrcode_with_params'),
    path('validate/', views.validate_identity, name='validate_identity'),  # 处理签到
    path('confirm/', views.confirm_attendance, name='confirm_attendance'),  # 确认界面

    # 请假相关
    path('leave/apply/', views.apply_leave, name='apply_leave'),  # 学生申请请假


    path('leave/bulk_approval/', views.bulk_leave_approval, name='bulk_leave_approval'), # 教师管理请假(查看+审批)


    # 学生考勤查询
    path('student/records/', views.student_check_records, name='student_check_records'),
    # 教师考勤查询
    path('teacher/records/', views.teacher_check_records, name='teacher_check_records'),

]