import os
import django
import sys

# Setup Django environment
sys.path.append('d:\\Careerlytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from Careerlytics.models import PlacementCell, PlacementCellStudent
from django.contrib.auth.models import User

def check_data():
    print("Checking Placement Cells:")
    pcs = PlacementCell.objects.all()
    for pc in pcs:
        print(f"Placement Cell: {pc.institution_name} (User: {pc.user.username})")
        students = PlacementCellStudent.objects.filter(placement_cell=pc)
        print(f"  Student Count: {students.count()}")
        for s in students[:3]:
             print(f"    - {s.name} ({s.student_id}) Active: {s.is_active}")
        
    print("\nChecking all PlacementCellStudent records:")
    all_students = PlacementCellStudent.objects.all()
    print(f"Total students in DB: {all_students.count()}")
    
if __name__ == '__main__':
    check_data()
