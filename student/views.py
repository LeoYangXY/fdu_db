from django.shortcuts import render

#用print代替打断点
#看报错的具体信息，而不是直接喂给ai，不然可能会很麻烦

#render:用一个模板重新渲染当前url，url不变；redirect就是到一个新的url

# Create your views here.
import logging

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


def scan_qrcode_with_params(request, course_code, timestamp, limit):
    """仅展示签到页面，不再初始化数据"""
    try:
        # 参数有效性验证
        if not all([course_code.strip(), timestamp, limit]):
            raise ValueError("课程代码、时间戳和有效期不能为空")

        # 类型转换和计算
        timestamp_int = int(timestamp)
        limit_int = int(limit)
        remaining = timestamp_int + limit_int * 60 - int(time.time())

        return render(request, 'attendance/scan.html', {
            'course_code': course_code,
            'timestamp': timestamp,  # 传递给模板用于后续POST
            'limit': limit,  # 传递给模板用于后续POST
            'remaining_seconds': max(0, remaining)
        })

    except ValueError as e:
        return render(request, 'attendance/error.html', {
            'error': f"参数错误: {str(e)}",
            'course_code': course_code,
            'timestamp': timestamp,
            'limit': limit
        })
    except Exception as e:
        return render(request, 'attendance/error.html', {
            'error': f"系统错误: {str(e)}",
            'course_code': course_code,
            'timestamp': timestamp,
            'limit': limit
        })


def validate_identity(request):
    if request.method == 'POST':
        # 初始化参数（防止后续引用未定义变量）
        student_id = request.POST.get('student_id', '').strip()
        course_code = request.POST.get('course_code', '').strip()
        timestamp = request.POST.get('timestamp', '').strip()
        limit = request.POST.get('limit', '').strip()  # 确保与模板字段名一致

        try:
            # 参数基础验证
            if not all([student_id, course_code, timestamp, limit]):
                raise ValueError("所有参数必须填写")

            # 类型转换
            timestamp_int = int(timestamp)
            limit_int = int(limit)

            # 时效性验证
            if time.time() > timestamp_int + limit_int * 60:
                raise ValueError("签到已超时")

            # 查询记录
            today = timezone.now().date()
            record = Attendance.objects.get(
                student__student_id=student_id,
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

            messages.success(request, "签到成功！")
            return redirect('confirm_attendance')

        except Attendance.DoesNotExist:
            messages.error(request, "未找到考勤记录，请联系教师")
        except Exception as e:
            messages.error(request, str(e))

        # 错误时传递必要参数到模板
        return render(request, 'attendance/error.html', {
            'course_code': course_code,
            'timestamp': timestamp,
            'limit': limit
        })

    # 非POST请求处理
    messages.error(request, "无效请求方法")
    return render(request, 'attendance/error.html', {
        'course_code': '',
        'timestamp': '',
        'limit': ''
    })

def confirm_attendance(request):
    """最简单的确认页面"""
    return render(request, 'attendance/confirm.html')



#学生只能请假一次（此处可以再优化）
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

            # 创建请假记录（leave_id会在save()时自动生成）
            LeaveRequest.objects.create(
                student=student,
                teacher=teacher,
                course=course,
                leave_date=leave_date,
                leave_reason=reason,
                # leave_status默认为'pending'
                # apply_date自动设置为当前时间
            )

            messages.success(request, "请假申请已提交，等待老师审批")
            return redirect('apply_leave')

        except Student.DoesNotExist:
            messages.error(request, "学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")
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