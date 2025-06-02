直接使用http://127.0.0.1:8000/login/进行角色选择
但是目前微信扫码还是需要去访问模拟的网页

剩下的问题：

1.微信扫码！！！！！！！！！！！！
2.用户认证  


3.前端修正  pyh


4.创建数据（使用administor那里的模板进行导入，但要注意数据的合理性） 根据新的7流程写脚本


[//]: # (5.Test)


[//]: # (7.管理员重新导入（管理员修改）   更新数据表student 学号+密码；  teacher  工号+密码    administor  管理号+密码)
mysql中：先drop掉之前的wechat_db
vscode中：在core/migrations下面的那里，除了__init__.py不要删除，别的如果有就都删掉
mysql中：然后create wechat_db
vscode中：python manage.py makemigrations，然后python manage.py migrate     

上面的流程就是创建完数据库+数据表，下面我们创建实际数据（相当于填写每一行）：

管理员创建：我们简单实现：在vscode中：python create_admin.py硬编码，直接操作数据库
学生，老师，课程，选课信息导入：还是去之前的页面，下载excel表（学生和老师的excel更新了账号密码2个字段）

然后去mysql中检查：core_administrator,core_student,core_teacher,core_courses,core_enrollment是否有填写好对应的数据


！！！！！！！！！！！！！！
（高并发）：架构设计的高并发：原本是每次学生签到都要提取数据库的表，此处是老师生成扫码界面就能预处理，实现了高并发
考虑使用redis在签到那里直接加
！！！！！！！！！！！！！！
我们初步的高并发：针对一些学生的重复签到，添加了Cache处理，但是对于实际的签到过程没有做到高并发
可以使用redis保存签到记录+定期写入



现在对于请假次数过多的提醒：我们是选择自己身份是学生，点击进入查询是否请假次数过多按钮，然后还要再次输入学号
这样子就无法做到按钮标红。并且这样子，学生可以查别的学生的请假次数过多记录，隔离性不好
我们需要在做到用户认证之后，根据一开始填写的学号+密码，如果请假次数过多，那个按钮就会标红
所以要处理用户认证

记得要先生成了qrcode，学生访问对应的网址，才能够进行签到


管理员： 
填表，导入信息：http://127.0.0.1:8000/administrator/admin_import/

学生：
考勤:http://127.0.0.1:8000/student/scan/CS101/1748533684/120/

[//]: 已解决# (!!!!重复签到+请假成功的签到未解决)

[//]: 已解决# (！！！！架构问题：应该是老师生成课程二维码那里去处理X-Y，而不是每个学生扫码去处理X-Y)
提交请假申请：http://127.0.0.1:8000/student/leave/apply/
查看考勤：http://127.0.0.1:8000/student/student/records/
[//]: # (已解决！！！10002请假成功了，表中有记录，但是网页显示不出来；10004请假失败了，表中有记录，但是网页显示不出来)

老师：
产生课程代码：http://127.0.0.1:8000/teacher/generate_qrcode/
[//]: 已解决# (!!可能的问题：老师重新生成这个界面，就会让数据库重填一次，就是已经签到的会消失？？？仔细看下)
批准请假：http://127.0.0.1:8000/teacher/leave/bulk_approval/
!在这里面融入：请假次数过多通知
查看考勤：http://127.0.0.1:8000/teacher/teacher/records/
[//]: # (已解决  (！！！！10002请假成功了，attendance表中有记录，但是网页上10002没有显示 ；请假记录都是未审批状态，无法正确提取数据))



暂时使用：
from django.urls import reverse
import time

course_code = "CS101"
timestamp = str(int(time.time()))
limit = "120"

url = reverse('scan_qrcode_with_params', args=[course_code, timestamp, limit]) 
full_url = f"http://127.0.0.1:8000{url}"
print(full_url)
去替代



确保手机和电脑在同一局域网
获取电脑的本地IP地址（Windows: ipconfig / Mac/Linux: ifconfig）
临时允许所有网络访问Django： python manage.py runserver 0.0.0.0:8000  此时电脑也只能使用真实ip进行访问
此命令让Django监听所有网络接口，但实际访问仍需通过电脑的本地IP（如 192.168.31.163）。
本地IP是私有地址，只能在局域网内访问（即同一WiFi下的设备才能解析此IP）。

在setting中配置：ALLOWED_HOSTS = ['192.168.31.163', 'localhost', '127.0.0.1']#果你需要通过本地IP（如 10.230.32.73）或其他设备访问，则必须添加对应的IP或域名到 ALLOWED_HOSTS，否则会报错 Invalid HTTP_HOST header
手机浏览器访问：http://[电脑本地IP]:8000/...（生成二维码的页面）

ngork内网穿透：
先打开ngork，映射到外网ip
然后pycharm中启动manage.py
然后才能进行扫码