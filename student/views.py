from django.db.models import Count
from django.shortcuts import render
from django.core.cache import cache
#用print代替打断点
#看报错的具体信息，而不是直接喂给ai，不然可能会很麻烦

#render:用一个模板重新渲染当前url，url不变；redirect就是到一个新的url

# Create your views here.
import logging

from django.urls import reverse
from django.db import IntegrityError
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)  # 确保这行在视图函数之前
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from core.models import Attendance, LeaveRequest, Course, Enrollment, Student
import datetime
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
import time
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db import transaction
from django.utils import timezone

#用print代替打断点
#看报错的具体信息，而不是直接喂给ai，不然可能会很麻烦

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
import time


def scan_qrcode_with_params(request, course_code, timestamp, limit):
    """仅允许已登录学生访问签到页面"""
    # 检查session中的登录标记
    if not request.session.get('is_logged_in') or not request.session.get('student_id'):
        login_url = f"{reverse('login')}?next={request.path}"
        return redirect(login_url)

    try:
        # 从session获取学生信息
        student_id = request.session['student_id']
        student = Student.objects.get(student_id=student_id)

        # 参数处理
        timestamp_int = int(timestamp)
        limit_int = int(limit)
        remaining = timestamp_int + limit_int * 60 - int(time.time())

        return render(request, 'attendance/scan.html', {
            'course_code': course_code,
            'timestamp': timestamp,
            'limit': limit,
            'remaining_seconds': max(0, remaining),
            'student_id': student_id,
            'student_name': student.name  # 添加学生姓名
        })
    except Exception as e:
        return render(request, 'attendance/error.html', {
            'error': str(e),
            'redirect_url': reverse('login') + f'?next={request.path}'
        })


def validate_identity(request):
    if request.method == 'POST':
        # 从session获取学生信息（与scan_qrcode_with_params保持一致）
        if not request.session.get('is_logged_in') or not request.session.get('student_id'):
            messages.error(request, "请先登录")
            return redirect('login')

        try:
            student_id = request.session['student_id']
            current_student = Student.objects.get(student_id=student_id)

            course_code = request.POST.get('course_code', '').strip()
            timestamp = request.POST.get('timestamp', '').strip()
            limit = request.POST.get('limit', '').strip()

            # 参数基础验证
            if not all([course_code, timestamp, limit]):
                raise ValueError("所有参数必须填写")

            # 时效性验证
            timestamp_int = int(timestamp)
            limit_int = int(limit)
            if time.time() > timestamp_int + limit_int * 60:
                raise ValueError("签到已超时")

            # 检查是否已签到（防止重复签到）
            cache_key = f"attendance:{course_code}:{student_id}:{timezone.now().date().isoformat()}"
            if cache.get(cache_key):
                raise PermissionError("请勿重复签到")

            # 查询考勤记录
            today = timezone.now().date()
            record = Attendance.objects.get(
                student=current_student,
                course__course_code=course_code,
                date=today
            )

            # 状态检查
            if record.status == 'approved_leave':
                raise PermissionError("已批准请假，无需签到")
            if record.status == 'present':
                raise PermissionError("请勿重复签到")

            # 更新状态
            record.status = 'present'
            record.scan_time = timezone.now()
            record.save()

            # 写入缓存
            cache.set(cache_key, 'present', timeout=24 * 60 * 60)

            messages.success(request, "签到成功！")
            return redirect('confirm_attendance')

        except Attendance.DoesNotExist:
            messages.error(request, "未找到考勤记录，请联系教师")
        except Exception as e:
            messages.error(request, str(e))

        return render(request, 'attendance/error.html', {
            'course_code': course_code,
            'timestamp': timestamp,
            'limit': limit
        })

    messages.error(request, "无效请求方法")
    return redirect('login')

def confirm_attendance(request):
    """最简单的确认页面"""
    return render(request, 'attendance/confirm.html')


def apply_leave(request):
    """学生请假申请（使用session中的学生信息）"""
    # 手动检查登录状态
    if not request.session.get('is_logged_in'):
        return redirect(f'/login/?next={request.path}')

    # 获取学生信息
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('/login/')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('/login/')

    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        leave_date_str = request.POST.get('leave_date')
        reason = request.POST.get('reason')

        try:
            course = Course.objects.get(course_code=course_code)
            teacher = course.teacher

            # 日期转换
            try:
                leave_date = datetime.strptime(leave_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "日期格式不正确，请使用YYYY-MM-DD格式")
                return redirect('apply_leave')

            # 检查是否已存在请假申请
            existing_leave = LeaveRequest.objects.filter(
                student=student,
                course=course,
                leave_date=leave_date
            ).first()

            if existing_leave:
                if existing_leave.leave_status == 'approved':
                    messages.warning(request, f"您对于该课程在{leave_date}的请假已获批准，无需重复申请")
                elif existing_leave.leave_status == 'pending':
                    messages.warning(request, f"您对于该课程在{leave_date}的请假申请正在处理中，请耐心等待")
                elif existing_leave.leave_status == 'rejected':
                    messages.warning(request, f"您对于该课程在{leave_date}的请假申请已被拒绝，如需重新申请请联系老师")
                return redirect('apply_leave')

            # 创建请假记录
            LeaveRequest.objects.create(
                student=student,
                teacher=teacher,
                course=course,
                leave_date=leave_date,
                leave_reason=reason
            )

            messages.success(request, "请假申请已提交，等待老师审批")
            return redirect('apply_leave')

        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")
        except IntegrityError:
            messages.error(request, "您对于该课程已成功提交请假申请，无需重复提交")
        except Exception as e:
            messages.error(request, f"提交失败: {str(e)}")

    # 自动填充学生信息到模板
    return render(request, 'attendance/apply_leave.html', {
        'student': student
    })


def student_check_records(request):
    """学生查看自己的考勤和请假记录"""
    # 手动检查登录状态
    if not request.session.get('is_logged_in'):
        return redirect(f'/login/?next={request.path}')

    # 获取学生信息
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('/login/')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('/login/')

    if request.method == 'POST':
        course_code = request.POST.get('course_code')

        try:
            course = Course.objects.get(course_code=course_code)

            # 获取考勤记录（按日期倒序）
            attendance_records = Attendance.objects.filter(
                student=student,
                course=course
            ).order_by('-date')

            # 获取请假记录（按请假日期倒序）
            leave_records = LeaveRequest.objects.filter(
                student=student,
                course=course
            ).order_by('-leave_date')

            # 统计考勤状态
            attendance_stats = {
                'total': attendance_records.count(),
                'present': attendance_records.filter(status='present').count(),
                'absent': attendance_records.filter(status='absent').count(),
                'approved_leave': attendance_records.filter(status='approved_leave').count(),
            }

            # 统计请假状态
            leave_stats = {
                'total': leave_records.count(),
                'approved': leave_records.filter(leave_status='approved').count(),
                'pending': leave_records.filter(leave_status='pending').count(),
                'rejected': leave_records.filter(leave_status='rejected').count(),
            }

            return render(request, 'attendance/student_record_list.html', {
                'student': student,
                'course': course,
                'attendance_records': attendance_records,
                'leave_records': leave_records,
                'attendance_stats': attendance_stats,
                'leave_stats': leave_stats
            })

        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")

    # 自动填充学生信息
    return render(request, 'attendance/student_check_records.html', {
        'student': student
    })


def check_whether_too_many_leave(request):
    """学生检查自己的请假次数"""
    # 手动检查登录状态
    if not request.session.get('is_logged_in'):
        return redirect(f'/login/?next={request.path}')

    # 获取学生信息
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('/login/')

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect('/login/')

    # 获取该学生已批准的请假记录，按课程分组统计
    leave_stats = LeaveRequest.objects.filter(
        student=student,
        leave_status='approved'
    ).values(
        'course__course_code',
        'course__course_name'
    ).annotate(
        total_leaves=Count('leave_id')
    ).order_by('-total_leaves')

    # 标记危险课程（请假>=1次）
    for stat in leave_stats:
        stat['is_dangerous'] = stat['total_leaves'] >= 1  # 根据您的原始代码，>=1就标记为危险

    return render(request, 'attendance/leave_check.html', {
        'student': student,
        'leave_stats': leave_stats,
        'searched': True  # 因为自动填充，所以总是显示结果
    })



def student_dashboard(request):
    # 手动检查登录状态
    if not request.session.get('is_logged_in'):
        return redirect(f'/login/?next={request.path}')

    # 获取学生信息
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('/login/')

    try:
        student = Student.objects.get(student_id=student_id)
        return render(request, 'student_dashboard.html', {
            'student': student
        })
    except Student.DoesNotExist:
        return redirect('/login/')
