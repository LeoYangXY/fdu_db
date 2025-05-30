from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)  # 确保这行在视图函数之前
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import datetime
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
import time
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import LeaveRequest,Attendance
from django.db import transaction
from django.db import transaction
from django.utils import timezone


# Create your views here.
import time

from django.http import HttpResponse
from django.shortcuts import render
from urllib.parse import quote
# Create your views here.
from django.shortcuts import render, redirect
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from core.models import Course

#教师访问URL → 输入课程号 → 生成签到二维码
#但是当前实现存在严重的安全漏洞：任何知道URL的人都可以生成签到二维码
def generate_course_qrcode(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        limit_minutes = int(request.POST.get('limit', '30'))

        try:
            course = Course.objects.get(course_code=course_code)

            # 构建带时间戳的签到链接（路径参数格式）
            base_url = request.build_absolute_uri('/attendance/scan/')
            timestamp = int(time.time())

            # 修改为路径参数格式
            qr_url = f"{base_url}{course_code}/{timestamp}/{limit_minutes}/"

            # 生成二维码
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # 返回图片
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return HttpResponse(buffer.getvalue(), content_type="image/png")

        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': '课程不存在，请先创建课程'})
    else:
        return render(request, 'courses/generate_qrcode.html')




#老师批准完毕之后，会在LeaveRequest表更新
def bulk_leave_approval(request):
    course = None
    leave_requests = []

    if request.method == 'POST':
        # 处理课程查询
        if 'query_course' in request.POST:
            course_code = request.POST.get('course_code')
            try:
                course = Course.objects.get(course_code=course_code)
                leave_requests = LeaveRequest.objects.filter(
                    course=course,
                    leave_status='pending'
                ).order_by('leave_date')

                if not leave_requests:
                    messages.info(request, "该课程没有待审批的请假申请")

            except Course.DoesNotExist:
                messages.error(request, "课程代码不存在")

        # 处理批量审批提交
        elif 'submit_approvals' in request.POST:
            course_code = request.POST.get('course_code')
            decisions = request.POST.getlist('decisions')

            try:
                course = Course.objects.get(course_code=course_code)
                pending_requests = LeaveRequest.objects.filter(
                    course=course,
                    leave_status='pending'
                ).order_by('leave_date')

                approved_count = 0
                rejected_count = 0

                for i, leave in enumerate(pending_requests):
                    if i < len(decisions):
                        decision = decisions[i]

                        if decision == 'approve':
                            leave.leave_status = 'approved'
                            approved_count += 1
                        else:
                            leave.leave_status = 'rejected'
                            rejected_count += 1

                        leave.save()  # ✅ 确保更新保存

                messages.success(
                    request,
                    f"成功处理审批: 批准 {approved_count} 条, 拒绝 {rejected_count} 条"
                )
                return redirect('bulk_leave_approval')

            except Exception as e:
                messages.error(request, f"处理出错: {str(e)}")

    return render(request, 'attendance/bulk_leave_approval.html', {
        'course': course,
        'leave_requests': leave_requests
    })



def teacher_check_records(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')

        try:
            course = Course.objects.get(course_code=course_code)

            # 获取该课程的所有考勤记录
            attendance_records = Attendance.objects.filter(
                course=course
            ).order_by('-date', 'student__name')

            print(attendance_records)

            # 获取该课程的所有请假记录
            leave_records = LeaveRequest.objects.filter(
                course=course
            ).order_by('-leave_date', 'student__name')

            print(leave_records)

            # 统计出勤情况
            attendance_stats = {
                'total': attendance_records.count(),
                'present': attendance_records.filter(status='present').count(),
                'absent': attendance_records.filter(status='absent').count(),
            }

            return render(request, 'attendance/teacher_record_list.html', {
                'course': course,
                'attendance_records': attendance_records,
                'leave_records': leave_records,
                'attendance_stats': attendance_stats
            })

        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")

    return render(request, 'attendance/teacher_check_records.html')