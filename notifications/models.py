from django.db import models

# Create your models here.


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    receiver = models.ForeignKey(
        'users.Student',
        related_name='received_notifications',
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        'users.Teacher',
        related_name='sent_notifications',
        on_delete=models.CASCADE
    )
    content = models.TextField()
    send_time = models.DateTimeField(auto_now_add=True)