from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from Careerlytics.models import PlacementCellStudent, DriveApplication
from users.models import UserRegistration


class Command(BaseCommand):
    help = "Convert CGPA values (0–10) stored in placement_cell_students.cgpa to percentage (0–100)."

    def handle(self, *args, **options):
        updated_students = 0
        updated_apps = 0

        with transaction.atomic():
            for s in PlacementCellStudent.objects.all():
                val = s.marks_percentage
                if val is None:
                    continue
                try:
                    dec = Decimal(val)
                except Exception:
                    try:
                        dec = Decimal(str(val))
                    except Exception:
                        continue
                if dec <= Decimal("10"):
                    s.marks_percentage = round(float(dec) * 10.0, 2)
                    s.save(update_fields=["marks_percentage"])
                    updated_students += 1
                    try:
                        user_reg = UserRegistration.objects.get(student_id=s.student_id)
                        user_reg.academic_marks = float(s.marks_percentage)
                        user_reg.save(update_fields=["academic_marks"])
                    except UserRegistration.DoesNotExist:
                        pass

            for app in DriveApplication.objects.all():
                val = app.student_cgpa
                if val is None:
                    continue
                try:
                    dec = Decimal(val)
                except Exception:
                    try:
                        dec = Decimal(str(val))
                    except Exception:
                        continue
                if dec <= Decimal("10"):
                    app.student_cgpa = round(float(dec) * 10.0, 2)
                    app.save(update_fields=["student_cgpa"])
                    updated_apps += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_students} student records"))
        self.stdout.write(self.style.SUCCESS(f"Updated {updated_apps} drive application records"))
