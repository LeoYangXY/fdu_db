from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', '出席'),
        ('absent', '缺席'),
        ('approved_leave', '已批准请假'),
    ]
    record_id = models.AutoField(primary_key=True, db_column='record_id')
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.RESTRICT
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.RESTRICT
    )
    date = models.DateField("考勤日期")
    status = models.CharField(
        "考勤状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent'
    )
    scan_time = models.DateTimeField("签到时间", null=True, blank=True)
    # remark = models.TextField("备注信息", blank=True, null=True)

    # 关联请假申请
    leave_request = models.OneToOneField(
        'LeaveRequest',
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


class LeaveRequest(models.Model):
    leave_id = models.CharField(max_length=30, unique=True)

    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.Teacher', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)

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