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
    try:
        # 参数类型转换
        timestamp_int = int(timestamp)
        limit_minutes = int(limit)
        current_time = timezone.now()
        today = current_time.date()
        # 获取课程对象
        course = Course.objects.get(course_code=course_code)
        # 获取所有选课学生（X）
        enrollments = Enrollment.objects.filter(course=course)
        student_ids = enrollments.values_list('student_id', flat=True)
        students = Student.objects.filter(student_id__in=student_ids)
        # 获取已批准请假的学生（Y）
        approved_leave_student_ids = LeaveRequest.objects.filter(
            course=course,
            leave_date=today,
            leave_status='approved'
        ).values_list('student_id', flat=True)
        # 4. 计算缺勤学生（X - Y）
        absent_students = students.exclude(
            student_id__in=approved_leave_student_ids
        )
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
            print(student)
            print(course)
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

            #============此处需要修改，为什么重复签到或者被批假的还是会显示签到成功了，existing_record弄不出来

            # 检查是否已有 approved_leave 或 present 记录
            existing_record = Attendance.objects.filter(
                student=student,
                course=course,
                date=today,
                status__in=['approved_leave', 'present']
            ).first()
            print(1)
            if existing_record:
                if existing_record.status == 'approved_leave':
                    messages.warning(request, "您已成功请假，无需签到")
                    return redirect('attendance_error')  # 跳转到错误页
                elif existing_record.status == 'present':
                    messages.info(request, "您已签到成功，无需重复签到")
                    return redirect('attendance_error')  # 跳转到错误页
            print(2)

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

        #学号不存在的报错也没有解决
        except Student.DoesNotExist:
            messages.error(request, "学号不存在")
        except Course.DoesNotExist:
            messages.error(request, "课程不存在")
        except Exception as e:
            messages.error(request, f"签到失败：{str(e)}")

        return redirect('scan_qrcode_with_params', course_code=course_code, timestamp=timestamp, limit=limit_minutes)

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
