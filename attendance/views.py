import logging
logger = logging.getLogger(__name__)  # 确保这行在视图函数之前
from django.shortcuts import render

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Attendance, LeaveRequest
import datetime
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from users.models import Student
from courses.models import Course

import time
from django.utils import timezone

#用print代替打断点
#看报错的具体信息，而不是直接喂给ai，不然可能会很麻烦

#补充error（签到失败）的前端界面

def scan_qrcode_with_params(request, course, timestamp, limit):
    try:
        # 参数类型转换
        timestamp_int = int(timestamp)
        limit_minutes = int(limit)

        # 计算剩余时间
        current_time = int(time.time())
        remaining_seconds = max(0, timestamp_int + limit_minutes * 60 - current_time)
        remaining_minutes = remaining_seconds // 60
        remaining_seconds %= 60

        return render(request, 'attendance/scan.html', {
            'course_code': course,
            'timestamp': timestamp_int,
            'limit_minutes': limit_minutes,
            'remaining': remaining_seconds,
            'remaining_minutes': remaining_minutes,
            'remaining_seconds': remaining_seconds
        })
    except Exception as e:
        return render(request, 'attendance/error.html', {'error': f'参数错误：{str(e)}'})


    #添加验证逻辑
    #避免重复签到


# 暂时的验证代码：
# 测试URL生成示例
# import time
# from django.urls import reverse
#
# # 假设参数
# course_code = "CS101"         # 课程编号
# limit_minutes = 30            # 签到有效时间（分钟）
# timestamp = int(time.time())  # 当前时间戳
#
# # 构造路径参数格式的 URL
# base_url = "/attendance/scan/"  # Django 中的路径前缀
# test_url = f"{base_url}{course_code}/{timestamp}/{limit_minutes}/"
#
# print("测试URL：", test_url)

# 接收表单提交
# 创建记录
# 重定向到确认页
# 这一部分没有对应的网页要展示
# attendance/views.py
def validate_identity(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code', '')
        timestamp = request.POST.get('timestamp', '')
        limit_minutes = request.POST.get('limit_minutes', '')

        try:
            # 参数验证
            if not all([student_id, course_code, timestamp, limit_minutes]):
                raise ValueError("缺少必要参数")

            # 类型转换
            try:
                timestamp_int = int(timestamp)
                limit_int = int(limit_minutes)
            except ValueError:
                raise ValueError("时间参数格式错误")

            # 获取对象
            student = Student.objects.get(student_id=student_id)
            course = Course.objects.get(course_code=course_code)

            # 时间有效性验证
            current_time = timezone.now()
            # 正确使用 datetime.fromtimestamp
            deadline = timezone.make_aware(
                datetime.fromtimestamp(timestamp_int)  # 注意这里是 datetime.datetime.fromtimestamp
            ) + timedelta(minutes=limit_int)

            if current_time > deadline:
                messages.error(request, "超出签到时间限制")
                return render(request, 'attendance/error.html', {
                    'error': '参数丢失，无法继续签到'
                })

            if Attendance.objects.filter(
                student=student,
                course=course,
                date=current_time.date(),
                status='present'  # 明确检查已签到状态
            ).exists():
                messages.error(request, "今日已签到，请勿重复操作")
                return render(request, 'attendance/error.html', {
                    'specific_error': '您今天已经完成签到，无需重复操作'
                })

            # print(1)
            # 检查请假
            has_valid_leave = LeaveRequest.objects.filter(
                student=student,
                course=course,
                leave_date=current_time.date(),
                leave_status='approved'
            ).exists()

            if has_valid_leave:
                messages.warning(request, "您已成功请假，无需签到")
                return redirect('confirm_attendance')
            # print(2)
            # 创建记录
            Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=current_time.date(),
                defaults={'status': 'present', 'scan_time': current_time}
            )
            # print(3)
            return redirect('confirm_attendance')

        except Student.DoesNotExist:
            messages.error(request, "学生不存在")
            logger.warning("Student.DoesNotExist: 学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程不存在")
            logger.warning("Course.DoesNotExist: 课程不存在")
        except Exception as e:
            messages.error(request, f"签到失败：{str(e)}")
            logger.error(f"签到失败: {str(e)}", exc_info=True)

        # ✅ 确保参数存在再调用 redirect
        if course_code and timestamp and limit_minutes:
            return redirect('scan_qrcode_with_params',
                            course=course_code,
                            timestamp=int(timestamp),
                            limit=int(limit_minutes))
        else:
            # 如果参数丢失，抛出错误或跳转到错误页面
            return render(request, 'attendance/error.html', {
                'error': '参数丢失，无法继续签到'
            })

    else:  # GET 请求
        # ✅ 强制跳转到错误页面或返回 405 Method Not Allowed
        return render(request, 'attendance/error.html', {
            'error': '请求方法不支持，请通过二维码扫码进入'
        })

def confirm_attendance(request):
    """最简单的确认页面"""
    return render(request, 'attendance/confirm.html')


def submit_leave(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code')
        reason = request.POST.get('reason')
        timestamp = request.POST.get('timestamp')
        limit_minutes = request.POST.get('limit_minutes')

        try:
            student = Student.objects.get(student_id=student_id)
            course = Course.objects.get(course_code=course_code)

            # 获取教师（假设Course模型有teacher字段）
            teacher = course.teacher

            # 创建请假ID（格式：20230820-STU-COURSE）
            leave_id = f"{timezone.now().strftime('%Y%m%d')}-{student.student_id}-{course.course_code}"

            # 检查是否已有记录
            existing, created = LeaveRequest.objects.get_or_create(
                leave_id=leave_id,
                defaults={
                    'student': student,
                    'course': course,
                    'teacher': teacher,
                    'leave_date': timezone.now().date(),
                    'leave_reason': reason,
                    'leave_status': 'pending'
                }
            )

            if not created:
                existing.leave_reason = reason
                existing.save()
                messages.warning(request, "请假申请已更新")
            else:
                messages.success(request, "请假申请已提交")

            return redirect('confirm_attendance')

        except Student.DoesNotExist:
            messages.error(request, "学生不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程不存在")

    return redirect('scan_qrcode_with_params',
                    course=course_code,
                    timestamp=timestamp,
                    limit=limit_minutes)


def approve_leave(request, leave_id):
    try:
        leave_request = LeaveRequest.objects.get(leave_id=leave_id)

        if leave_request.leave_status != 'pending':
            messages.warning(request, "该申请已被处理")
            return redirect('list_leave_requests')

        # 更新请假状态
        leave_request.leave_status = 'approved'
        leave_request.save()

        # 更新考勤记录
        Attendance.objects.update_or_create(
            student=leave_request.student,
            course=leave_request.course,
            date=leave_request.leave_date,
            defaults={
                'status': 'approved_leave',
                'remark': '已批准请假'
            }
        )

        messages.success(request, "请假已批准")

    except LeaveRequest.DoesNotExist:
        messages.error(request, "记录不存在")

    return redirect('list_leave_requests')


def reject_leave(request, leave_id):
    try:
        leave_request = LeaveRequest.objects.get(leave_id=leave_id)

        if leave_request.leave_status != 'pending':
            messages.warning(request, "该申请已被处理")
            return redirect('list_leave_requests')

        # 更新请假状态
        leave_request.leave_status = 'rejected'
        leave_request.save()

        # 更新考勤记录
        Attendance.objects.update_or_create(
            student=leave_request.student,
            course=leave_request.course,
            date=leave_request.leave_date,
            defaults={
                'status': 'absent',
                'remark': '请假被拒绝'
            }
        )

        messages.success(request, "请假已拒绝")

    except LeaveRequest.DoesNotExist:
        messages.error(request, "记录不存在")

    return redirect('list_leave_requests')


def list_leave_requests(request):
    # 获取待处理请假申请（按教师过滤）
    pending_requests = LeaveRequest.objects.filter(
        leave_status='pending',
        teacher=request.user.teacher_profile  # 假设使用user.teacher_profile获取教师信息
    ).order_by('apply_date')

    return render(request, 'attendance/leave_requests.html', {
        'pending_requests': pending_requests
    })