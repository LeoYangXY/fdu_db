# attendance/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 原有URL
    path('scan/<str:course>/<str:timestamp>/<str:limit>/', views.scan_qrcode_with_params, name='scan_qrcode_with_params'),
    path('validate/', views.validate_identity, name='validate_identity'),  # 处理签到
    path('confirm/', views.confirm_attendance, name='confirm_attendance'),  # 确认界面

    # 新增请假功能URL
    path('submit_leave/', views.submit_leave, name='submit_leave'),  # 提交请假
    path('approve_leave/<leave_id>/', views.approve_leave, name='approve_leave'),  # 批准请假
    path('reject_leave/<leave_id>/', views.reject_leave, name='reject_leave'),  # 拒绝请假
    path('leave_requests/', views.list_leave_requests, name='list_leave_requests'),  # 请假列表
]