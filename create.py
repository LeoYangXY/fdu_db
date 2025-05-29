#test流程：创建学生，老师，课程；生成签到码；进行签到
from django.urls import reverse
import time

# 参数均为字符串类型（即使数字也转为字符串）
course_code = "EE201"
timestamp = str(int(time.time()))  # 时间戳转为字符串
limit = "120"  # 字符串形式

# 生成URL
url = reverse('scan_qrcode_with_params', args=[course_code, timestamp, limit])
full_url = f"http://127.0.0.1:8000{url}"
print(full_url)


# 1. 导入必要的模块和模型
from django.utils import timezone
from users.models import Student, Teacher
from courses.models import Course

# 2. 创建教师（严格匹配你的模型定义）
teacher_obj, teacher_created = Teacher.objects.get_or_create(
    teacher_id="T1001",  # 必须提供，因为这是primary_key
    defaults={
        'name': "Jack",
        'department': "CS_department"
        # contact 留空不写
    }
)
print(f"教师 {'创建成功' if teacher_created else '已存在'}：{teacher_obj}")

# 3. 创建课程（修正course_time格式）
course_obj, course_created = Course.objects.get_or_create(
    course_code="CS101",
    defaults={
        'course_name': "CSAPP",
        'department': "CS_department",
        'teacher': teacher_obj,  # 使用上面创建的教师实例
        'course_time': "周三 9:00-11:00"  # 改为符合实际的字符串格式
    }
)
print(f"课程 {'创建成功' if course_created else '已存在'}：{course_obj}")

# 4. 创建学生
student_obj, student_created = Student.objects.get_or_create(
    student_id="20210001",
    defaults={
        'name': "Leo",
        'department': "CS_department",
        'major': "CS",
        'gender': "M"
        # wechat_openid 留空不写
    }
)
print(f"学生 {'创建成功' if student_created else '已存在'}：{student_obj}")



# 1. 创建第二位教师
teacher2, t2_created = Teacher.objects.get_or_create(
    teacher_id="T1002",
    defaults={
        'name': "Alice",
        'department': "EE_department",
        'contact': "alice@example.com"
    }
)
print(f"教师2 {'创建成功' if t2_created else '已存在'}：{teacher2}")

# 2. 创建第二门课程
course2, c2_created = Course.objects.get_or_create(
    course_code="EE201",
    defaults={
        'course_name': "电路原理",
        'department': "EE_department",
        'teacher': teacher2,
        'course_time': "周四 14:00-16:00"
    }
)
print(f"课程2 {'创建成功' if c2_created else '已存在'}：{course2}")

# 3. 创建第二位学生
student2, s2_created = Student.objects.get_or_create(
    student_id="20210002",
    defaults={
        'name': "Lily",
        'department': "EE_department",
        'major': "Electronic",
        'gender': "F",
        'wechat_openid': "wx_lily_2021"
    }
)
print(f"学生2 {'创建成功' if s2_created else '已存在'}：{student2}")

# 4. 可选：创建关联的考勤记录
from attendance.models import Attendance
attendance2, a2_created = Attendance.objects.get_or_create(
    student=student2,
    course=course2,
    date=timezone.now().date(),
    defaults={
        'status': 'present',
        'scan_time': timezone.now()
    }
)
print(f"考勤记录2 {'创建成功' if a2_created else '已存在'}：{attendance2}")