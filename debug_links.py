import os
import django
import sys

# Setup Django environment
sys.path.append('d:\\Careerlytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from Careerlytics.models import PlacementCell, PlacementCellStudent
from users.models import UserRegistration, Student
from django.db.models import Q

def check_missing_links():
    print("Checking for unlinked students...")
    
    # Get all placement cells and their names/codes
    placement_cells = PlacementCell.objects.all()
    pc_map = {}
    for pc in placement_cells:
        # Map institution name and code to PC object
        name = pc.institution_name.strip().upper()
        pc_map[name] = pc
        if pc.college_code:
            pc_map[pc.college_code] = pc
            
    print(f"Active Placement Cells: {list(pc_map.keys())}")
    
    # Get all students
    students = UserRegistration.objects.filter(user_type='student')
    print(f"Total Registered Students: {students.count()}")
    
    linked_count = 0
    unlinked_count = 0
    potential_links = 0
    
    for student in students:
        # Check if already linked
        is_linked = PlacementCellStudent.objects.filter(
            Q(email=student.email) | Q(student_id=student.student_id)
        ).exists()
        
        if is_linked:
            linked_count += 1
        else:
            unlinked_count += 1
            college = student.college_name.strip().upper() if student.college_name else ""
            if college in pc_map:
                print(f"Found unlinked student: {student.userid} ({college}) -> Matches PC: {pc_map[college].institution_name}")
                potential_links += 1
            else:
                print(f"Unlinked student: {student.userid} ({college}) -> No PC match")

    print(f"\nSummary:")
    print(f"Linked: {linked_count}")
    print(f"Unlinked: {unlinked_count}")
    print(f"Potential new links (matching college name): {potential_links}")

if __name__ == '__main__':
    check_missing_links()
