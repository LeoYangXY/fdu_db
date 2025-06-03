from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from core.models import Student, Teacher, Administrator

def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')  # 改为使用学号/工号作为用户名
        password = request.POST.get('password')

        # print(role)
        # print(username)
        # print(password)
        # print(type(role))
        # print(type(username))
        # print(type(password))
        # print()
        user = None
        error_message = ''

        if role == 'admin':
            try:
                user = Administrator.objects.get(administrator_id=username)
                if user.password != password:  # 直接比较明文密码
                    user = None
            except Administrator.DoesNotExist:
                error_message = '无效的管理员账号或密码'
        elif role == 'teacher':
            try:
                user = Teacher.objects.get(teacher_id=username)
                if user.password != password:  # 直接比较明文密码
                    user = None
            except Teacher.DoesNotExist:
                error_message = '无效的教师账号或密码'
        elif role == 'student':
            try:
                user = Student.objects.get(student_id=username)
                if user.password != password:  # 直接比较明文密码
                    user = None
            except Student.DoesNotExist:
                error_message = '无效的学生账号或密码'
        # print(user)
        if user:
            if role == 'admin':
                return redirect('/administrator/dashboard/')
            elif role == 'teacher':
                return redirect('/teacher/dashboard/')
            elif role == 'student':
                return redirect('/student/dashboard/')
        else:
            error_message = '无效的账号或密码'

        return render(request, 'login.html', {'error': error_message})

    return render(request, 'login.html')