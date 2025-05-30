管理员： 
填表，导入信息：http://127.0.0.1:8000/administrator/admin_import/

学生：
考勤:http://127.0.0.1:8000/student/scan/CS101/1748533684/120/
!!!!重复签到+请假成功的签到未解决
！！！！架构问题：应该是老师生成课程二维码那里去处理X-Y，而不是每个学生扫码去处理X-Y
提交请假申请：http://127.0.0.1:8000/student/leave/apply/
查看考勤：http://127.0.0.1:8000/student/student/records/
[//]: # (已解决！！！10002请假成功了，表中有记录，但是网页显示不出来；10004请假失败了，表中有记录，但是网页显示不出来)

老师：
产生课程代码：http://127.0.0.1:8000/teacher/generate_qrcode/
批准请假：http://127.0.0.1:8000/teacher/leave/bulk_approval/
!在这里面融入：请假次数过多通知
查看考勤：http://127.0.0.1:8000/teacher/teacher/records/
[//]: # (已解决  &#40;！！！！10002请假成功了，attendance表中有记录，但是网页上10002没有显示 ；请假记录都是未审批状态，无法正确提取数据&#41;)


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