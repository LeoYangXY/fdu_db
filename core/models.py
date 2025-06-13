from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Student(models.Model):
    student_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    major = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    wechat_openid = models.CharField(max_length=50, unique=True, blank=True, null=True)
    password = models.CharField(max_length=128, verbose_name="密码")  # 存储明文密码

    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"


class Teacher(models.Model):
    teacher_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    contact = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=128, verbose_name="密码")  # 存储明文密码

    class Meta:
        verbose_name = "教师"
        verbose_name_plural = "教师"


class Administrator(models.Model):
    administrator_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    contact = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=128, verbose_name="密码")  # 存储明文密码

    class Meta:
        verbose_name = "管理员"
        verbose_name_plural = "管理员"


class Course(models.Model):
    course_code = models.CharField(max_length=20, primary_key=True)
    course_name = models.CharField(max_length=100)
    department = models.CharField(max_length=50)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course_time = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_time = models.DateTimeField(auto_now_add=True)
    semester = models.CharField(max_length=20)

    class Meta:
        verbose_name = "选课记录"
        verbose_name_plural = "选课记录"
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course', 'semester'],
                name='uk_student_course_semester'
            )
        ]

class LeaveRequest(models.Model):
    leave_id = models.CharField(max_length=30, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    leave_date = models.DateField()
    leave_reason = models.TextField(blank=True, null=True)
    leave_status = models.CharField(
        max_length=10,
        choices=[('approved', 'Approved'), ('pending', 'Pending'), ('rejected', 'Rejected')],
        default='pending'
    )
    apply_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.leave_id:
            self.leave_id = f"{self.leave_date.strftime('%Y%m%d')}-{self.student.student_id}-{self.course.course_code}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "请假申请"
        verbose_name_plural = "请假申请"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', '出席'),
        ('absent', '缺席'),
        ('approved_leave', '已批准请假'),
    ]
    record_id = models.AutoField(primary_key=True, db_column='record_id')
    student = models.ForeignKey(Student, on_delete=models.RESTRICT)
    course = models.ForeignKey(Course, on_delete=models.RESTRICT)
    date = models.DateField("考勤日期")
    status = models.CharField(
        "考勤状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent'
    )
    scan_time = models.DateTimeField("签到时间", null=True, blank=True)
    leave_request = models.OneToOneField(
        LeaveRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联请假申请"
    )

    class Meta:
        verbose_name = "考勤记录"
        verbose_name_plural = "考勤记录"
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course', 'date'],
                name='unique_student_course_date'
            )
        ]
        indexes = [
            models.Index(
                fields=['student', 'course', 'date'],
                name='idx_student_course_date'
            )
        ]
#
# class Notification(models.Model):
#     notification_id = models.AutoField(primary_key=True)
#     receiver = models.ForeignKey(
#         Student,
#         related_name='received_notifications',
#         on_delete=models.CASCADE
#     )
#     sender = models.ForeignKey(
#         Teacher,
#         related_name='sent_notifications',
#         on_delete=models.CASCADE
#     )
#     content = models.TextField()
#     send_time = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         verbose_name = "通知"
#         verbose_name_plural = "通知"