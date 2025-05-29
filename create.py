from django.urls import reverse
import time

course_code = "CS101"
timestamp = str(int(time.time()))
limit = "120"

url = reverse('scan_qrcode_with_params', args=[course_code, timestamp, limit]) 
full_url = f"http://127.0.0.1:8000{url}"
print(full_url)
