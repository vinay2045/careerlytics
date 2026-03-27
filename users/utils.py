from Careerlytics.models import PlacementCell, PlacementCellStudent
from users.models import UserRegistration

def link_student_to_placement_cell(user):
    """
    Links a student user to a placement cell based on their college name.
    """
    if user.user_type != 'student':
        return False, "User is not a student"

    # Check if already linked
    if PlacementCellStudent.objects.filter(student_id=user.student_id).exists():
         # Also check email just in case student_id isn't unique enough or missing
         if PlacementCellStudent.objects.filter(email=user.email).exists():
             return True, "Already linked"

    # Determine institution name from college code/name
    institution_name = None
    college_name = user.college_name
    
    if not college_name:
        return False, "No college name provided"
        
    if 'SCCE' in college_name:
        institution_name = 'SREE CHAITANYA COLLEGE OF ENGINEERING'
    elif 'SCIT' in college_name:
        institution_name = 'SREE CHAITANYA INSTITUTE OF TECHNOLOGICAL SCIENCES'
    
    if not institution_name:
        return False, f"Unknown college: {college_name}"
        
    # Find placement cell
    placement_cell = PlacementCell.objects.filter(institution_name__icontains=institution_name).first()
    
    if not placement_cell:
        # Fallback: try to match by exact code if stored as SCCE/SCIT in institution_name
        placement_cell = PlacementCell.objects.filter(institution_name__iexact=college_name).first()
        
    if not placement_cell:
        # Last resort: Try partial match on the code part
        if 'SCCE' in college_name:
             placement_cell = PlacementCell.objects.filter(institution_name__icontains='SCCE').first()
        elif 'SCIT' in college_name:
             placement_cell = PlacementCell.objects.filter(institution_name__icontains='SCIT').first()

    if not placement_cell:
        return False, "Placement cell not found"

    # Create linkage
    try:
        PlacementCellStudent.objects.create(
            placement_cell=placement_cell,
            student_id=user.student_id,
            name=user.userid, # UserRegistration doesn't have name, using userid or we can fetch first/last if available
            email=user.email,
            phone=user.mobile,
            department=user.branch if user.branch else "Unknown",
            year=int(user.year) if user.year and (isinstance(user.year, int) or (isinstance(user.year, str) and user.year.isdigit())) else 1, # Default to 1 if missing/invalid
            marks_percentage=user.academic_marks if user.academic_marks is not None else 0.0,
            backlog=user.backlog if hasattr(user, 'backlog') else 0,
            is_active=True # Default to active so they show up
        )
        return True, f"Linked to {placement_cell.institution_name}"
    except Exception as e:
        return False, f"Error creating link: {str(e)}"

def get_user_registration(request):
    """
    Safely retrieves the UserRegistration object for the currently logged-in user.
    Checks session first, then Django auth username.
    Returns None if no UserRegistration is found.
    """
    from users.models import UserRegistration
    
    # 1. Try to get from session (custom login primary method)
    userid = request.session.get('userid')
    if userid:
        try:
            return UserRegistration.objects.get(userid=userid)
        except UserRegistration.DoesNotExist:
            pass
            
    # 2. Try to get from Django auth (fallback for standard/admin/staff logins)
    if request.user.is_authenticated:
        try:
            return UserRegistration.objects.get(userid=request.user.username)
        except UserRegistration.DoesNotExist:
            pass
            
    return None
