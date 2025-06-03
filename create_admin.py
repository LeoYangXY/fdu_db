#!/usr/bin/env python
import os
import sys

# 设置Django环境（必须！）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wechat_db.settings")
import django
django.setup()

from core.models import Administrator
from django.contrib.auth.hashers import make_password

# 创建管理员
admin, created = Administrator.objects.get_or_create(
    administrator_id="admin001",
    defaults={
        'name': '系统管理员',
        'department': 'IT部',
        'password':'admin001',
    }
)

if created:
    print("✅ 管理员创建成功\n账号: admin\n密码: admin123\n请及时修改密码！")
else:
    print("⚠️ 管理员已存在（如需重置请先删除原账号）")