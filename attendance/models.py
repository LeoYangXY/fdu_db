from django.db import models

# Create your models here.


class Attendance(models.Model):
    record_id = models.AutoField(primary_key=True)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=[('present', 'Present'), ('absent', 'Absent'), ('leave', 'Leave')],
        default='present'
    )
    scan_time = models.DateTimeField()
    is_valid = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'course', 'date'], name='idx_student_course_date'),
        ]

class LeaveRequest(models.Model):
    leave_id = models.CharField(max_length=30, primary_key=True)
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