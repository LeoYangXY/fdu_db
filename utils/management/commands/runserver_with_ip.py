from django.core.management.base import BaseCommand
import socket
import subprocess


class Command(BaseCommand):
    help = 'Start the Django development server with local IP'

    def handle(self, *args, **options):
        local_ip = self.get_local_ip()
        self.stdout.write(f"Starting development server at http://{local_ip}:8000/")
        subprocess.run(["python", "manage.py", "runserver", f"{local_ip}:8000"])

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except socket.error:
            return "127.0.0.1"