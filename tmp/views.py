from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
# Create your views here.

def tmp_try(request):
    return render(request, 'tmp.html', {
        'number': 100,
        'list': ['A', 'B', 'C'],
        'html': '<b>加粗文本</b>'
    })



# 表单
def tmp_search_form(request):
    return render(request, 'tmp_search_form.html')


# 接收请求数据
def tmp_search(request):
    request.encoding = 'utf-8'
    if 'q' in request.GET and request.GET['q']:
        message = '你搜索的内容为: ' + request.GET['q']
    else:
        message = '你提交了空表单'
    return HttpResponse(message)


# views.py
from django.shortcuts import render
from django.http import HttpResponseRedirect
# from .models import Student


def add_student(request):
    if request.method == 'GET':
        # 处理 GET 请求（首次访问/刷新页面）
        return render(request, 'tmp_add_student.html')

    elif request.method == 'POST':
        # 处理 POST 请求（表单提交）
        student_id = request.POST.get('student_id')
        name = request.POST.get('name')
        return render(request, 'tmp_add_student.html',
                      {'message': f'成功添加: {name}(学号:{student_id})'})

    else:
        # 处理其他 HTTP 方法（如 PUT/DELETE，可选）
        return HttpResponse("不支持的请求方法", status=405)