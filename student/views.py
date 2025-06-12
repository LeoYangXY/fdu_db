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
    """学生请假申请（整合提交功能）"""
    if request.method == 'POST':
        # 获取表单数据
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code')
        leave_date_str = request.POST.get('leave_date')
        reason = request.POST.get('reason')

        try:
            # 验证学生和课程
            student = Student.objects.get(student_id=student_id)
            course = Course.objects.get(course_code=course_code)
            teacher = course.teacher  # 从课程获取教师

            # 将字符串转换为日期对象
            try:
                leave_date = datetime.strptime(leave_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "日期格式不正确，请使用YYYY-MM-DD格式")
                return redirect('apply_leave')

            # 检查是否已经存在相同的请假申请
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

        except Student.DoesNotExist:
            messages.error(request, "学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")
        except IntegrityError:
            messages.error(request, "您对于该课程已成功提交请假申请，无需重复提交")
        except Exception as e:
            messages.error(request, f"提交失败: {str(e)}")

    return render(request, 'attendance/apply_leave.html')

#GET方法的时候，是到check_records这个网页；POST方法的时候，是到record_list这个网页
def student_check_records(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code')

        try:
            student = Student.objects.get(student_id=student_id)
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

            # 统计请假状态（使用leave_status字段）
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

        except Student.DoesNotExist:
            messages.error(request, "学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")

    return render(request, 'attendance/student_check_records.html')


def student_dashboard(request):
    return render(request, 'student_dashboard.html')


def check_whether_too_many_leave(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')

        try:
            student = Student.objects.get(student_id=student_id)

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

            # 标记危险课程（请假>=3次）
            for stat in leave_stats:
                stat['is_dangerous'] = stat['total_leaves'] >=1

            context = {
                'student': student,
                'leave_stats': leave_stats,
                'searched': True
            }
            return render(request, 'attendance/leave_check.html', context)

        except Student.DoesNotExist:
            return render(request, 'attendance/leave_check.html', {
                'error': '找不到该学号的学生',
                'searched': True
            })

    return render(request, 'attendance/leave_check.html', {'searched': False})