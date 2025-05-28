from django.http import HttpResponse


def hello(request):
    return HttpResponse("签到-请假系统")