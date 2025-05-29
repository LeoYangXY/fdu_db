import os
import django
from django.utils import timezone

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wechat_db.settings')
django.setup()

# 现在可以安全导入Django模型
from users.models import Student, Teacher
from courses.models import Course, Enrollment
from attendance.models import Attendance

# 选课数据
enrollments = [
    {"student_id": "20210001", "course_code": "CS101", "semester": "2023-秋季"},
    {"student_id": "20210004", "course_code": "CS101", "semester": "2023-秋季"},
    {"student_id": "20210002", "course_code": "EE201", "semester": "2023-秋季"},
    {"student_id": "20210003", "course_code": "CS101", "semester": "2023-秋季"},
    {"student_id": "20210003", "course_code": "EE201", "semester": "2023-秋季"}
]


def import_enrollments():
    print("开始导入选课数据...")

    for enroll in enrollments:
        try:
            student = Student.objects.get(student_id=enroll["student_id"])
            course = Course.objects.get(course_code=enroll["course_code"])

            # 使用get_or_create避免重复创建
            obj, created = Enrollment.objects.get_or_create(
                student=student,
                course=course,
                semester=enroll["semester"],
                defaults={"enrollment_time": timezone.now()}
            )

            if created:
                print(f"✅ 成功创建选课记录: {student.name} -> {course.course_name}")
            else:
                print(f"⏩ 记录已存在: {student.name} -> {course.course_name}")

        except Student.DoesNotExist:
            print(f"❌ 学生不存在: {enroll['student_id']}")
        except Course.DoesNotExist:
            print(f"❌ 课程不存在: {enroll['course_code']}")
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")


if __name__ == "__main__":
    import_enrollments()
    print("数据导入完成！")