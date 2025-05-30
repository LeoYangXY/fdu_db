直接使用http://127.0.0.1:8000/login/进行角色选择
但是目前微信扫码还是需要去访问模拟的网页

剩下的问题：

1.微信扫码！！！！！！！！！！！！
2.用户认证  


3.前端修正  pyh


4.创建数据（使用administor那里的模板进行导入，但要注意数据的合理性） 根据新的7流程写脚本


[//]: # (5.Test)


yxy
6.请假次数过多通知
7.管理员重新导入（管理员修改）   更新数据表student 学号+密码；  teacher  工号+密码    administor  管理号+密码


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