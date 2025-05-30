# python manage.py shell

from django.utils import timezone
from datetime import timedelta
import time
from urllib.parse import urljoin
from django.conf import settings

# 模拟参数
course_code = "CS101"  # 替换为你的课程代码
limit_minutes = 30      # 签到有效期(分钟)

# 生成时间戳
timestamp = int(time.time())

# 构建URL路径（与视图中的格式一致）
url_path = f"/student/scan/{course_code}/{timestamp}/{limit_minutes}/"

# 拼接完整URL（假设开发服务器运行在 http://127.0.0.1:8000）
base_url = "http://127.0.0.1:8000"
full_url = urljoin(base_url, url_path)

print("模拟签到URL:", full_url)
print("该URL将在以下时间过期:",
      (timezone.now() + timedelta(minutes=limit_minutes)).strftime("%Y-%m-%d %H:%M:%S"))