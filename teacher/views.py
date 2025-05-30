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
from core.models import LeaveRequest, Attendance, Student, Enrollment
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

# 开始
#   ↓
# 教师生成二维码（调用 scan_qrcode_with_params 视图）
#   ↓
# 获取课程对象和当前日期
#   ↓
# 获取所有选课学生（X）
#   ↓
# 筛选出当天已批准请假的学生（Y）
#   ↓
# 批量插入/更新 Attendance 记录：
#      Y → approved_leave
#      X - Y → absent
#   ↓
# 跳转到扫码页面（scan.html）
#   ↓
# 学生扫码进入 validate_identity 视图
#   ↓
# 检查是否已有 approved_leave 或 present 记录？
#     ↓ 是 → 阻止签到
#     ↓ 否 → 检查是否超时？
#         ↓ 是 → 无变化（保持 absent）
#         ↓ 否 → 更新为 present


from django.db import transaction
from django.utils import timezone
import qrcode
from io import BytesIO
from django.http import HttpResponse
def generate_course_qrcode(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        limit_minutes = int(request.POST.get('limit', '30'))

        try:
            # 获取课程对象
            course = Course.objects.get(course_code=course_code)
            today = timezone.now().date()

            # 1. 获取所有选课学生（通过Enrollment表）
            enrollments = Enrollment.objects.filter(course=course)
            student_ids = enrollments.values_list('student_id', flat=True)
            students = Student.objects.filter(student_id__in=student_ids)

            print(enrollments)

            # 2. 获取已批准请假的学生
            approved_leave_student_ids = LeaveRequest.objects.filter(
                course=course,
                leave_date=today,
                leave_status='approved'
            ).values_list('student_id', flat=True)

            print(approved_leave_student_ids)

            # 3. 批量处理考勤记录
            with transaction.atomic():
                # 3.1 处理请假学生
                for student_id in approved_leave_student_ids:
                    Attendance.objects.update_or_create(
                        student_id=student_id,  # 直接使用student_id赋值
                        course=course,
                        date=today,
                        defaults={'status': 'approved_leave'}
                    )

                # 3.2 处理缺勤学生（X - Y）
                absent_students = students.exclude(student_id__in=approved_leave_student_ids)
                for student in absent_students:
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        course=course,
                        date=today
                    )
                    if created or attendance.status == 'absent':
                        attendance.status = 'absent'
                        attendance.save()

            # 生成二维码（带时间戳）
            qr_url = request.build_absolute_uri(
                f"/attendance/scan/{course_code}/{int(time.time())}/{limit_minutes}/"
            )
            qr_img = qrcode.make(qr_url)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            return HttpResponse(buffer.getvalue(), content_type="image/png")

        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': '课程不存在'})
        except Exception as e:
            return render(request, 'error.html', {'error': f'系统错误: {str(e)}'})

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

            # print(attendance_records)

            # 获取该课程的所有请假记录
            leave_records = LeaveRequest.objects.filter(
                course=course
            ).order_by('-leave_date', 'student__name')

            # print(leave_records)

            # 统计出勤情况
            attendance_stats = {
                'total': attendance_records.count(),
                'present': attendance_records.filter(status='present').count(),
                'absent': attendance_records.filter(status='absent').count(),
                'approved_leave':attendance_records.filter(status='approved_leave').count(),
            }
            leave_stats = {
                'total': leave_records.count(),
                'approved': leave_records.filter(leave_status='approved').count(),
                'pending': leave_records.filter(leave_status='pending').count(),
                'rejected': leave_records.filter(leave_status='rejected').count(),
            }
            return render(request, 'attendance/teacher_record_list.html', {
                'course': course,
                'attendance_records': attendance_records,
                'leave_records': leave_records,
                'attendance_stats': attendance_stats,
                'leave_stats': leave_stats  # 新增统计信息
            })


        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")

    return render(request, 'attendance/teacher_check_records.html')