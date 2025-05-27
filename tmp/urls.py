# tmp/urls.py
from django.urls import path
from . import views  # 👈 从当前 app 导入 views

urlpatterns = [
    path('tmp_try/', views.tmp_try, name='tmp_try'),  # 示例路径
    path('search_form/', views.tmp_search_form, name='tmp_search_form'),  # 显示搜索表单
    path('search/', views.tmp_search, name='tmp_search'),  # 处理搜索请求
    path('add_student',views.add_student,name='tmp_add_student')
]