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

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.contrib import messages
from django.urls import reverse
import time
import hashlib

def scan_qrcode_with_params(request, course_code, timestamp, nonce):
    """扫码签到页面（兼容教师端生成的二维码）"""
    # 检查session中的登录标记
    if not request.session.get('is_logged_in') or not request.session.get('student_id'):
        login_url = f"{reverse('login')}?next={request.path}"
        return redirect(login_url)

    try:
        # 从session获取学生信息
        student_id = request.session['student_id']
        student = Student.objects.get(student_id=student_id)
        course = Course.objects.get(course_code=course_code)

        # 参数处理
        timestamp_int = int(timestamp)
        current_time = int(time.time())
        remaining = timestamp_int + 120 - current_time  # 固定120秒有效期

        # 验证nonce有效性
        if not cache.get(f'qrcode_nonce_{nonce}'):
            raise ValueError("二维码已失效，请获取最新二维码")

        # 如果是AJAX请求，返回JSON数据
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'remaining_seconds': max(0, remaining),
                'is_valid': remaining > 0
            })

        return render(request, 'attendance/scan.html', {
            'course': course,
            'timestamp': timestamp,
            'nonce': nonce,
            'remaining_seconds': max(0, remaining),
            'student': student,
            'refresh_interval': 5000  # 5秒刷新一次
        })

    except Exception as e:
        return render(request, 'attendance/error.html', {
            'error': str(e),
            'redirect_url': reverse('login') + f'?next={request.path}'
        })


def validate_identity(request):
    """签到验证（保持原有稳定逻辑）"""
    if request.method == 'POST':
        # 从session获取学生信息
        if not request.session.get('is_logged_in') or not request.session.get('student_id'):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': '请先登录'}, status=401)
            messages.error(request, "请先登录")
            return redirect('login')

        try:
            student_id = request.session['student_id']
            current_student = Student.objects.get(student_id=student_id)

            course_code = request.POST.get('course_code', '').strip()
            timestamp = request.POST.get('timestamp', '').strip()
            nonce = request.POST.get('nonce', '').strip()

            # 参数基础验证
            if not all([course_code, timestamp, nonce]):
                error = "所有参数必须填写"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error}, status=400)
                raise ValueError(error)

            # 时效性验证(120秒内有效)
            if time.time() > int(timestamp) + 120:
                error = "签到已超时"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error}, status=400)
                raise ValueError(error)

            # 验证nonce有效性
            if not cache.get(f'qrcode_nonce_{nonce}'):
                error = "二维码已失效"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error}, status=400)
                raise ValueError(error)

            # 检查是否已签到
            today = timezone.now().date()
            cache_key = f"attendance:{course_code}:{student_id}:{today.isoformat()}"
            if cache.get(cache_key):
                error = "请勿重复签到"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error}, status=400)
                raise PermissionError(error)

            # 查询考勤记录
            course = Course.objects.get(course_code=course_code)
            record = Attendance.objects.get(
                student=current_student,
                course=course,
                date=today
            )

            # 状态检查
            if record.status == 'approved_leave':
                error = "已批准请假，无需签到"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error}, status=400)
                raise PermissionError(error)
            if record.status == 'present':
                error = "请勿重复签到"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error}, status=400)
                raise PermissionError(error)

            # 更新状态
            record.status = 'present'
            record.scan_time = timezone.now()
            record.save()

            # 写入缓存防止重复签到
            cache.set(cache_key, 'present', timeout=24 * 60 * 60)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('confirm_attendance')
                })

            messages.success(request, "签到成功！")
            return redirect('confirm_attendance')

        except Attendance.DoesNotExist:
            error = "未找到考勤记录，请联系教师"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error}, status=404)
            messages.error(request, error)
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            messages.error(request, str(e))

        return redirect('student_dashboard')

    error = "无效请求方法"
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': error}, status=405)
    messages.error(request, error)
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

            # 生成leave_id（与模型中的逻辑一致）
            leave_id = f"{leave_date.strftime('%Y%m%d')}-{student.student_id}-{course.course_code}"

            # 检查是否已存在相同leave_id的请假申请
            existing_leave = LeaveRequest.objects.filter(leave_id=leave_id).first()

            if existing_leave:
                if existing_leave.leave_status == 'approved':
                    messages.warning(request, f"您对于该课程在{leave_date}的请假已获批准，无需重复申请")
                elif existing_leave.leave_status == 'pending':
                    if reason != existing_leave.leave_reason:
                        existing_leave.leave_reason = reason
                        existing_leave.save()
                        messages.info(request, f"已更新请假原因，等待老师审批")
                    else:
                        messages.warning(request, f"您对于该课程在{leave_date}的请假申请正在处理中")
                    return redirect('apply_leave')
                elif existing_leave.leave_status == 'rejected':
                    # 更新被拒绝的请假申请而不是创建新的
                    existing_leave.leave_reason = reason
                    existing_leave.leave_status = 'pending'  # 重置为待审批状态
                    existing_leave.apply_date = timezone.now()  # 更新申请时间
                    existing_leave.save()
                    messages.info(request,
                        f"您对于该课程在{leave_date}的请假申请曾被拒绝，现已更新并重新提交。"
                        f"如需详细沟通，请联系{teacher.name}老师。"
                    )
                return redirect('apply_leave')
            else:
                # 如果没有现有记录，创建新记录
                LeaveRequest.objects.create(
                    student=student,
                    teacher=teacher,
                    course=course,
                    leave_date=leave_date,
                    leave_reason=reason,
                    leave_id=leave_id  # 显式设置leave_id以避免save()时再次生成
                )
                messages.success(request, "请假申请已提交，等待老师审批")
                return redirect('apply_leave')

        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")
        except Exception as e:
            messages.error(request, f"提交失败: {str(e)}")

    # 获取学生最近的请假申请状态用于提示
    recent_leaves = LeaveRequest.objects.filter(
        student=student
    ).order_by('-apply_date')[:5]

    # 自动填充学生信息到模板
    return render(request, 'attendance/apply_leave.html', {
        'student': student,
        'recent_leaves': recent_leaves
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
