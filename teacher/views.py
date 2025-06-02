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

def get_ngrok_public_url():
    """
    动态获取当前 Ngrok 的公网 URL
    返回格式: "https://xxxx-xxx-xxx-xxx-xxx.ngrok.io" 或 None（失败时）
    """
    try:
        response = requests.get("http://127.0.0.1:4042/api/tunnels", timeout=3)
        #此处是4042端口，这和我们django的8000端口的关系是：
        #本地 Django 项目运行在8000端口（通过 python manage.py runserver 0.0.0.0:8000 启动）
        #4042端口是Ngrok的管理后台端口，用于提供 API 查询公网 URL（如 https://xxx.ngrok-free.app）
        if response.status_code == 200:
            print(f"获取 Ngrok URL 成功")
            tunnels = response.json()
            for tunnel in tunnels['tunnels']:
                if tunnel['proto'] == 'https':
                    return tunnel['public_url']
    except Exception as e:
        print(f"获取 Ngrok URL 失败: {str(e)}")
    return None


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
            # 动态获取 Ngrok 公网 URL 或 fallback 到本地
            ngrok_url = get_ngrok_public_url()
            if ngrok_url:
                # 使用 Ngrok 公网 URL
                qr_url = f"{ngrok_url}/student/scan/{course_code}/{int(time.time())}/{limit_minutes}/"
                print(qr_url)
            else:
                # Fallback: 使用本地地址（仅限同一局域网）
                qr_url = request.build_absolute_uri(
                    f"/student/scan/{course_code}/{int(time.time())}/{limit_minutes}/"
                )
                print(qr_url)
                print("警告: 使用本地地址生成二维码，外网设备无法访问")
            #根据当前项目所处在的ip地址，生成一个完整的url，那么其实前缀就是本机的ip地址。
            #就是将相对路径（如 /student/scan/...）转换为 完整 URL，格式为： http://<当前服务器的IP或域名>:<端口>/student/scan/...
            #而由于我们的项目使用runserver那个命令简单启动，因此是跑在192.168.xx.xx这个ip下面的
            #而192.168.x.x  10.x.x.x  172.16.x.x是私有IP（局域网专用），具有以下特性：
            #仅限同一局域网内访问（如连接同一路由器 / 交换机的设备）
            #公网无法直接访问（互联网上的设备无法通过私有 IP 找到你的电脑）
            #然后处于同一局域网的手机对其进行扫码，就可以跳转到这个完整的url（如果不是同一局域网，那么就无法跳转）
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


def teacher_dashboard(request):
    return render(request, 'teacher_dashboard.html')