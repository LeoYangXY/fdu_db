from django.db import models

# Create your models here.

class Student(models.Model):
    student_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    major = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    wechat_openid = models.CharField(max_length=50, unique=True, blank=True, null=True)

class Teacher(models.Model):
    teacher_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    contact = models.CharField(max_length=50, blank=True, null=True)