import logging

logger = logging.getLogger(__name__)  # 确保这行在视图函数之前
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Attendance, LeaveRequest
import datetime
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from users.models import Student
from courses.models import Course,Enrollment
import time
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LeaveRequest,Attendance
from django.db import transaction
from django.db import transaction
from django.utils import timezone

#用print代替打断点
#看报错的具体信息，而不是直接喂给ai，不然可能会很麻烦


def scan_qrcode_with_params(request, course_code, timestamp, limit):
    try:
        # 参数类型转换
        timestamp_int = int(timestamp)
        limit_minutes = int(limit)
        current_time = timezone.now()
        today = current_time.date()
        print(0)
        # 获取课程对象
        course = Course.objects.get(course_code=course_code)
        print(0.1)
        # 获取所有选课学生（X）
        enrollments = Enrollment.objects.filter(course=course)
        print(0.15)
        student_ids = enrollments.values_list('student_id', flat=True)
        print(0.2)
        print(student_ids)
        students = Student.objects.filter(student_id__in=student_ids)
        print(0.25)
        # 获取已批准请假的学生（Y）
        approved_leave_student_ids = LeaveRequest.objects.filter(
            course=course,
            leave_date=today,
            leave_status='approved'
        ).values_list('student_id', flat=True)
        print(0.3)
        # 4. 计算缺勤学生（X - Y）
        absent_students = students.exclude(
            student_id__in=approved_leave_student_ids
        )
        print(0.4)
        # 批量处理考勤记录
        with transaction.atomic():
            # 批量插入/更新请假学生记录
            for student_id in approved_leave_student_ids:
                Attendance.objects.update_or_create(
                    student_id=student_id,
                    course=course,
                    date=today,
                    defaults={'status': 'approved_leave'}
                )

            # 批量插入/更新缺勤学生记录
            for student in absent_students:
                Attendance.objects.update_or_create(
                    student=student,
                    course=course,
                    date=today,
                    defaults={'status': 'absent'}
                )

        # 计算剩余时间
        remaining_seconds = max(0, timestamp_int + limit_minutes * 60 - int(time.time()))
        remaining_minutes = remaining_seconds // 60
        remaining_seconds %= 60

        return render(request, 'attendance/scan.html', {
            'course_code': course_code,
            'timestamp': timestamp_int,
            'limit_minutes': limit_minutes,
            'remaining': remaining_seconds,
            'remaining_minutes': remaining_minutes,
            'remaining_seconds': remaining_seconds
        })
    except Course.DoesNotExist:
        return render(request, 'attendance/error.html', {'error': '课程不存在'})
    except Exception as e:
        return render(request, 'attendance/error.html', {'error': f'参数错误：{str(e)}'})


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



def validate_identity(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code')
        timestamp = request.POST.get('timestamp')
        limit_minutes = request.POST.get('limit_minutes')

        try:
            student = Student.objects.get(student_id=student_id)
            course = Course.objects.get(course_code=course_code)

            # 类型转换
            try:
                timestamp_int = int(timestamp)
                limit_int = int(limit_minutes)
            except ValueError:
                raise ValueError("时间参数格式错误")
            current_time = timezone.now()
            today = current_time.date()
            deadline = timezone.make_aware(datetime.fromtimestamp(timestamp_int)) + timedelta(minutes=limit_int)

            if current_time > deadline:
                messages.error(request, "超出签到时间限制")
                return render(request, 'attendance/error.html', {
                    'error': '超出签到时间，签到系统已关闭'
                })

            # 检查是否已有 approved_leave 或 present 记录
            existing_record = Attendance.objects.filter(
                student=student,
                course=course,
                date=today,
                status__in=['approved_leave', 'present']
            ).first()

            if existing_record:
                if existing_record.status == 'approved_leave':
                    messages.warning(request, "您已成功请假，无需签到")
                elif existing_record.status == 'present':
                    messages.warning(request, "您已成功签到")
                return redirect('confirm_attendance')

            # 更新为出席
            Attendance.objects.update_or_create(
                student=student,
                course=course,
                date=today,
                defaults={
                    'status': 'present',
                    'scan_time': current_time,
                }
            )

            return redirect('confirm_attendance')

        except Student.DoesNotExist:
            messages.error(request, "学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程不存在")
        except Exception as e:
            messages.error(request, f"签到失败：{str(e)}")

        return redirect('scan_qrcode_with_params', course=course_code, timestamp=timestamp, limit=limit_minutes)

    else:
        return render(request, 'attendance/error.html', {
            'error': '请求方法不支持，请通过二维码扫码进入'
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

#GET方法的时候，是到check_records这个网页；POST方法的时候，是到record_list这个网页
def student_check_records(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code')

        try:
            student = Student.objects.get(student_id=student_id)
            course = Course.objects.get(course_code=course_code)

            # 获取该学生在该课程的所有考勤记录
            records = Attendance.objects.filter(
                student=student,
                course=course
            ).order_by('-date')

            # 获取该学生在该课程的请假记录
            leave_records = LeaveRequest.objects.filter(
                student=student,
                course=course
            ).order_by('-leave_date')

            return render(request, 'attendance/student_record_list.html', {
                'student': student,
                'course': course,
                'records': records,
                'leave_records': leave_records
            })

        except Student.DoesNotExist:
            messages.error(request, "学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程代码不存在")

    return render(request, 'attendance/student_check_records.html')


def teacher_check_records(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')

        try:
            course = Course.objects.get(course_code=course_code)

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
                'late': attendance_records.filter(status='late').count(),
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