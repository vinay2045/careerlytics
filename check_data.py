import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from Careerlytics.models import DriveApplication
from users.models import UserRegistration

print("\n--- All Students ---")
students = UserRegistration.objects.all()
for s in students:
    print(f"UserID: {s.userid}, StudentID: {s.student_id}, Email: {s.email}")

print("\n--- All Applications ---")
apps = DriveApplication.objects.all()
print(f"Total applications: {apps.count()}")
for app in apps:
    print(f"App ID: {app.id}, Drive: {app.drive.company_name} ({app.drive.title}), Full Name: {app.full_name}, Hall Ticket: {app.hall_ticket_number}, Student ID: {app.student.student_id}, UserID: {app.student.userid}")


