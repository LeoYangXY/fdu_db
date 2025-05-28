# attendance/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 原有URL
    path('scan/<str:course>/<str:timestamp>/<str:limit>/', views.scan_qrcode_with_params, name='scan_qrcode_with_params'),
    path('validate/', views.validate_identity, name='validate_identity'),  # 处理签到
    path('confirm/', views.confirm_attendance, name='confirm_attendance'),  # 确认界面

    # 请假相关
    path('leave/apply/', views.apply_leave, name='apply_leave'),  # 学生申请请假

    # 查询相关
    path('records/check/', views.check_records, name='check_records'),  # 学生查询签到记录
    path('leave/bulk_approval/', views.bulk_leave_approval, name='bulk_leave_approval'), # 教师管理请假(查看+审批)

]