from django.shortcuts import render

# Create your views here.
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Attendance
import datetime
from django.shortcuts import render, redirect
from users.models import Student
from courses.models import Course




def scan_qrcode(request):
    """最简单的扫码页面"""
    return render(request, 'attendance/scan.html')

def validate_identity(request):
    #添加验证逻辑
    #避免重复签到
    """
    接收表单提交
    创建记录
    重定向到确认页
    这一部分没有对应的网页要展示
    """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_code = request.POST.get('course_code')

        try:
            # 获取学生和课程对象
            student = Student.objects.get(student_id=student_id)
            course = Course.objects.get(course_code=course_code)

            # 创建考勤记录（包含所有必填字段）
            Attendance.objects.create(
                student=student,
                course=course,
                date=timezone.now().date(),  # 当前日期
                status='present',  # 默认状态
                scan_time=timezone.now(),  # 当前时间
                is_valid=True  # 标记为有效
            )

            return redirect('confirm_attendance')

        except Student.DoesNotExist:
            return render(request, 'error.html', {'error': '学生不存在'})
        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': '课程不存在'})
    else:
        return redirect('scan_qrcode')  # 如果不是POST请求则跳回扫码页


def confirm_attendance(request):
    """最简单的确认页面"""
    return render(request, 'attendance/confirm.html')