import time

from django.http import HttpResponse
from django.shortcuts import render
from urllib.parse import quote
# Create your views here.
from django.shortcuts import render, redirect
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from .models import Course

#教师访问URL → 输入课程号 → 生成签到二维码
#但是当前实现存在严重的安全漏洞：任何知道URL的人都可以生成签到二维码

def generate_course_qrcode(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        limit_minutes = int(request.POST.get('limit', '30'))

        try:
            course = Course.objects.get(course_code=course_code)

            # 构建带时间戳的签到链接（路径参数格式）
            base_url = request.build_absolute_uri('/attendance/scan/')
            timestamp = int(time.time())

            # 修改为路径参数格式
            qr_url = f"{base_url}{course_code}/{timestamp}/{limit_minutes}/"

            # 生成二维码
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # 返回图片
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return HttpResponse(buffer.getvalue(), content_type="image/png")

        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': '课程不存在，请先创建课程'})
    else:
        return render(request, 'courses/generate_qrcode.html')