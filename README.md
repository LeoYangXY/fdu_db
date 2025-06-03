签到那里还需要：根据用户认证的学号，不能签到别人的学号！
用户认证



！！！！！！！！！！！！！！
（高并发）：架构设计的高并发：原本是每次学生签到都要提取数据库的表，此处是老师生成扫码界面就能预处理，实现了高并发
考虑使用redis在签到那里直接加
！！！！！！！！！！！！！！
我们初步的高并发：针对一些学生的重复签到，添加了Cache处理，但是对于实际的签到过程没有做到高并发
可以使用redis保存签到记录+定期写入




确保手机和电脑在同一局域网
获取电脑的本地IP地址（Windows: ipconfig / Mac/Linux: ifconfig）
临时允许所有网络访问Django： python manage.py runserver 0.0.0.0:8000  此时电脑也只能使用真实ip进行访问
此命令让Django监听所有网络接口，但实际访问仍需通过电脑的本地IP（如 192.168.31.163）。
本地IP是私有地址，只能在局域网内访问（即同一WiFi下的设备才能解析此IP）。

在setting中配置：ALLOWED_HOSTS = ['192.168.31.163', 'localhost', '127.0.0.1']#果你需要通过本地IP（如 10.230.32.73）或其他设备访问，则必须添加对应的IP或域名到 ALLOWED_HOSTS，否则会报错 Invalid HTTP_HOST header
手机浏览器访问：http://[电脑本地IP]:8000/...（生成二维码的页面）

ngork内网穿透：
先打开ngork，映射到外网ip

具体：
配置密钥：双击打开ngrok，执行如下命令： ngrok authtoken 2Yh...（Your Authtoken）
映射端口：ngrok http 80

然后pycharm中启动manage.py:python manage.py runserver 0.0.0.0:8000
然后才能进行扫码

当然，要从终端的ngrok那里看到底使用的是ngrok的哪个端口，看清楚是40还是42，然后在teacher的view那里需要修改


使用：python manage.py runserver_with_ip才能得到初始化界面
