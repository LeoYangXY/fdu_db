from django.http import HttpResponse
from django.shortcuts import render, redirect


def hello(request):
    return HttpResponse("签到-请假系统")

def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        if role == 'admin':
            return redirect('/administrator/dashboard/')
        elif role == 'teacher':
            return redirect('/teacher/dashboard/')
        elif role == 'student':
            return redirect('/student/dashboard/')
    return render(request, 'login.html')