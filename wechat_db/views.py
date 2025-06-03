from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from core.models import Student, Teacher, Administrator
from django.contrib.auth import login as auth_login
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.urls import reverse


def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.GET.get('next', '')

        user = None
        error_message = ''

        if role == 'admin':
            try:
                user = Administrator.objects.get(administrator_id=username)
                if user.password != password:
                    user = None
            except Administrator.DoesNotExist:
                error_message = '无效的管理员账号或密码'
        elif role == 'teacher':
            try:
                user = Teacher.objects.get(teacher_id=username)
                if user.password != password:
                    user = None
            except Teacher.DoesNotExist:
                error_message = '无效的教师账号或密码'
        elif role == 'student':
            try:
                user = Student.objects.get(student_id=username)
                if user.password != password:
                    user = None
            except Student.DoesNotExist:
                error_message = '无效的学生账号或密码'

        if user:
            # 手动设置session标记
            request.session['is_logged_in'] = True
            request.session['user_role'] = role
            request.session['user_id'] = username

            # 根据角色设置不同的session字段
            if role == 'student':
                request.session['student_id'] = username
            elif role == 'teacher':
                request.session['teacher_id'] = username
            elif role == 'admin':
                request.session['administrator_id'] = username

            # 优先跳转到next参数指定的页面
            if next_url:
                return redirect(next_url)
            elif role == 'admin':
                return redirect('/administrator/dashboard/')
            elif role == 'teacher':
                return redirect('/teacher/dashboard/')
            elif role == 'student':
                return redirect('/student/dashboard/')
        else:
            error_message = error_message or '无效的账号或密码'

        return render(request, 'login.html', {
            'error': error_message,
            'next': next_url
        })

    # GET请求时传递next参数
    return render(request, 'login.html', {
        'next': request.GET.get('next', '')
    })