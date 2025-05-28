python manage.py runserver 开服务器 后续需要部署在正规的服务器上

老师创建签到码：http://127.0.0.1:8000/courses/generate_qrcode/    输入课程码即可创建出一个二维码，学生需要微信扫码即可跳转到对应的签到界面
（可以理解为二维码就是一个url，老师创建一个微信二维码等价于创建一个用于本课程签到的url。此处暂时没有实现微信跳转，因为还没有挂在正式的服务器上)
因此我们直接让学生访问课程签到的url进行签到（正式流程应该是微信扫码，此处只是简单替代）

如何生成这个课程签到的url呢：
在终端输入python manage.py shell
然后复制粘贴：
#test流程：创建学生，老师，课程；生成签到码；进行签到
import time
from django.urls import reverse

# 获取当前时间戳
current_timestamp = int(time.time())

# 构造 URL（假设 URL name 是 'scan_qrcode'）
url = reverse('scan_qrcode_with_params', args=['EE201', current_timestamp, 120])
full_url = f"http://127.0.0.1:8000{url}"
print(full_url)

就会得到一个url，比如http://127.0.0.1:8000/attendance/scan/EE201/1748404429/120/

学生访问此即可进入签到界面

然后输入学号+课程号即可进行签到
（此处要保证：已经创建了对应的学生+课程实例）
可以用如下代码简单创建：

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



=========================================================
上述是签到流程，下面是请假
=========================================================


学生访问http://127.0.0.1:8000/attendance/leave/apply/即可进行请假
老师访问http://127.0.0.1:8000/attendance/leave/bulk_approval/即可进行审批
学生访问http://127.0.0.1:8000/attendance/records/check/，即可查看自己的签到+请假记录


