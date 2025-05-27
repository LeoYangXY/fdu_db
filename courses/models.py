from django.db import models

# Create your models here.


class Course(models.Model):
    course_code = models.CharField(max_length=20, primary_key=True)
    course_name = models.CharField(max_length=100)
    department = models.CharField(max_length=50)
    teacher = models.ForeignKey('users.Teacher', on_delete=models.CASCADE)
    course_time = models.CharField(max_length=50, blank=True, null=True)

class Enrollment(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    enrollment_time = models.DateTimeField(auto_now_add=True)
    semester = models.CharField(max_length=20)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course', 'semester'], name='uk_student_course_semester')
        ]