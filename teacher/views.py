from django.shortcuts import render, get_object_or_404
import logging
from django.http import HttpResponse
from openpyxl import Workbook
from django.utils import timezone

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
from core.models import LeaveRequest, Attendance, Student, Enrollment, Teacher
from django.db import transaction
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.cache import cache
from django.contrib import messages
from django.db import transaction
from io import BytesIO
import qrcode
import time
import hashlib
import base64

# Create your views here.
import time
import requests
from django.http import HttpResponse
from django.shortcuts import render
from urllib.parse import quote
# Create your views here.
from django.shortcuts import render, redirect
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from core.models import Course

from django.db import transaction
from django.utils import timezone
import qrcode
from io import BytesIO
from django.http import HttpResponse


def generate_course_qrcode(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        limit_seconds = 120  # 二维码有效期120秒

        # 获取当前教师
        teacher_id = request.session.get('teacher_id')
        if not teacher_id:
            return JsonResponse({'error': '请先登录'}, status=401)

        try:
            current_teacher = Teacher.objects.get(teacher_id=teacher_id)
            # 检查课程是否属于当前教师
            course = Course.objects.get(course_code=course_code, teacher=current_teacher)

            today = timezone.now().date()

            # 1. 获取所有选课学生
            enrollments = Enrollment.objects.filter(course=course)
            student_ids = enrollments.values_list('student_id', flat=True)
            students = Student.objects.filter(student_id__in=student_ids)

            # 2. 获取已批准请假的学生
            approved_leave_student_ids = LeaveRequest.objects.filter(
                course=course,
                leave_date=today,
                leave_status='approved'
            ).values_list('student_id', flat=True)

            # 3. 批量处理考勤记录
            with transaction.atomic():
                # 处理请假学生
                for student_id in approved_leave_student_ids:
                    Attendance.objects.update_or_create(
                        student_id=student_id,
                        course=course,
                        date=today,
                        defaults={'status': 'approved_leave'}
                    )

                # 处理缺勤学生
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

            # 生成动态二维码
            timestamp = int(time.time())
            nonce = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

            # 构建带时效的签到URL
            qr_url = request.build_absolute_uri(
                f"/student/scan/{course_code}/{timestamp}/{nonce}/"
            )

            # 生成二维码图片
            qr_img = qrcode.make(qr_url)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")

            # 缓存nonce防止重放
            cache.set(f'qrcode_nonce_{nonce}', 1, timeout=limit_seconds)

            return JsonResponse({
                'qr_image': base64.b64encode(buffer.getvalue()).decode('utf-8'),
                'expires_at': timestamp + limit_seconds,
                'refresh_interval': 110  # 前端每110秒刷新一次(留10秒缓冲)
            })

        except Teacher.DoesNotExist:
            return JsonResponse({'error': '教师信息不存在'}, status=400)
        except Course.DoesNotExist:
            return JsonResponse({'error': '课程不存在或不属于当前教师'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'courses/generate_qrcode.html')


def bulk_leave_approval(request):
    course = None
    leave_requests = []

    # 获取当前教师
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        messages.error(request, "请先登录")
        return redirect('login')

    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, "教师信息不存在")
        return redirect('login')

    if request.method == 'POST':
        # 处理课程查询
        if 'query_course' in request.POST:
            course_code = request.POST.get('course_code')
            try:
                # 检查课程是否属于当前教师
                course = Course.objects.get(course_code=course_code, teacher=current_teacher)
                leave_requests = LeaveRequest.objects.filter(
                    course=course,
                    leave_status='pending'
                ).order_by('leave_date')

                if not leave_requests:
                    messages.info(request, "该课程没有待审批的请假申请")

            except Course.DoesNotExist:
                messages.error(request, "课程代码不存在或不属于当前教师")

        # 处理批量审批提交
        elif 'submit_approvals' in request.POST:
            course_code = request.POST.get('course_code')

            try:
                # 检查课程是否属于当前教师
                course = Course.objects.get(course_code=course_code, teacher=current_teacher)
                pending_requests = LeaveRequest.objects.filter(
                    course=course,
                    leave_status='pending'
                ).order_by('leave_date')

                approved_count = 0
                rejected_count = 0

                for leave in pending_requests:
                    decision = request.POST.get(f'decision_{leave.id}')

                    if decision == 'approve':
                        leave.leave_status = 'approved'
                        approved_count += 1
                    elif decision == 'reject':
                        leave.leave_status = 'rejected'
                        rejected_count += 1

                    leave.save()

                messages.success(
                    request,
                    f"成功批量处理审批: 批准 {approved_count} 条, 拒绝 {rejected_count} 条"
                )
                return redirect('bulk_leave_approval')

            except Course.DoesNotExist:
                messages.error(request, "课程代码不存在或不属于当前教师")
            except Exception as e:
                messages.error(request, f"处理出错: {str(e)}")

    return render(request, 'attendance/bulk_leave_approval.html', {
        'course': course,
        'leave_requests': leave_requests
    })


def teacher_check_records(request):
    # 获取当前教师
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        messages.error(request, "请先登录")
        return redirect('login')

    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, "教师信息不存在")
        return redirect('login')

    if request.method == 'POST':
        course_code = request.POST.get('course_code')

        try:
            # 检查课程是否属于当前教师
            course = Course.objects.get(course_code=course_code, teacher=current_teacher)

            # 获取该课程的所有考勤记录
            attendance_records = Attendance.objects.filter(
                course=course
            ).order_by('-date', 'student__name')

            # 获取该课程的所有请假记录
            leave_records = LeaveRequest.objects.filter(
                course=course
            ).order_by('-leave_date', 'student__name')

            # 统计出勤情况
            attendance_stats = {
                'total': attendance_records.count(),
                'present': attendance_records.filter(status='present').count(),
                'absent': attendance_records.filter(status='absent').count(),
                'approved_leave': attendance_records.filter(status='approved_leave').count(),
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
                'leave_stats': leave_stats
            })

        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在或不属于当前教师")

    return render(request, 'attendance/teacher_check_records.html')


def export_attendance(request, course_code):
    # 获取当前教师
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        messages.error(request, "请先登录")
        return redirect('login')

    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, "教师信息不存在")
        return redirect('login')

    # 检查课程是否属于当前教师
    course = get_object_or_404(Course, course_code=course_code, teacher=current_teacher)

    attendance_records = Attendance.objects.filter(course=course).select_related('student')
    leave_records = LeaveRequest.objects.filter(course=course).select_related('student')

    # 创建工作簿和工作表
    wb = Workbook()
    ws_attendance = wb.active
    ws_attendance.title = "考勤记录"
    ws_leave = wb.create_sheet(title="请假记录")

    # 设置考勤记录表头
    ws_attendance.append(['日期', '学号', '姓名', '状态', '签到时间'])

    # 填充考勤数据
    for record in attendance_records:
        status_map = {
            'present': '出席',
            'absent': '缺席',
            'approved_leave': '已批准请假'
        }
        status = status_map.get(record.status, record.status)
        scan_time = record.scan_time.strftime("%H:%M") if record.scan_time else "-"
        leave_id = record.leave_request.leave_id if record.leave_request else ""

        ws_attendance.append([
            record.date.strftime("%Y-%m-%d"),
            record.student.student_id,
            record.student.name,
            status,
            scan_time,
            leave_id
        ])

    # 设置请假记录表头
    ws_leave.append(['请假ID', '请假日期', '学号', '姓名', '原因', '状态', '申请时间'])

    # 填充请假数据
    for record in leave_records:
        status_map = {
            'approved': '已批准',
            'pending': '待审批',
            'rejected': '已拒绝'
        }
        status = status_map.get(record.leave_status, record.leave_status)

        ws_leave.append([
            record.leave_id,
            record.leave_date.strftime("%Y-%m-%d"),
            record.student.student_id,
            record.student.name,
            record.leave_reason or "",
            status,
            record.apply_date.strftime("%Y-%m-%d %H:%M")
        ])

    # 设置文件名和响应
    filename = f"{course.course_name}_{course.course_code}_考勤记录_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    # 保存工作簿到响应
    wb.save(response)
    return response


def teacher_dashboard(request):
    # 获取当前教师
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        messages.error(request, "请先登录")
        return redirect('login')

    try:
        current_teacher = Teacher.objects.get(teacher_id=teacher_id)
    except Teacher.DoesNotExist:
        messages.error(request, "教师信息不存在")
        return redirect('login')

    # 获取教师教授的课程
    courses = Course.objects.filter(teacher=current_teacher)

    return render(request, 'teacher_dashboard.html', {
        'teacher': current_teacher,
        'courses': courses
    })

def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html')