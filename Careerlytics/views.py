from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
import json
from .models import PlacementCell, PlacementCellStudent, Placement, PlacementActivity, DriveApplication
from .models import ReadinessTestResult, ReadinessTest
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta

def calculate_growth(current_val, previous_val):
    """
    Helper function to calculate percentage growth
    """
    if previous_val == 0:
        return 100 if current_val > 0 else 0
    return int(((current_val - previous_val) / previous_val) * 100)

def index(request):
    """
    Landing page view
    """
    return render(request, 'index.html')

def register_view(request):
    """
    Unified registration view that renders the register.html template
    """
    return render(request, 'register.html')

def unified_login_view(request):
    """
    Unified login view that handles both user and admin login
    """
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'user')
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if user type matches user's role
            if user_type == 'admin' and not user.is_staff:
                messages.error(request, 'You do not have admin privileges.')
                return render(request, 'user_login.html')
            
            if user_type == 'user' and user.is_staff:
                messages.error(request, 'Admin users cannot login as regular users.')
                return render(request, 'user_login.html')
            
            # Login user
            login(request, user)
            
            # Handle remember me
            if not remember:
                request.session.set_expiry(0)  # Session expires on browser close
            else:
                request.session.set_expiry(1209600)  # 2 weeks in seconds
            
            # Redirect based on user type
            if user_type == 'admin':
                messages.success(request, 'Welcome back, Admin!')
                return redirect('AdminHome')  # Use existing admin home URL
            else:
                messages.success(request, 'Welcome back to Careerlytics!')
                return redirect('UserHome_direct')  # Use direct UserHome URL
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'user_login.html')

def UserRegister(request):
    return render(request,'UserRegister.html',{})

def Register(request):
    return render(request,'UserRegister.html',{})

def AdminLogin(request):
    return render(request,'AdminLogin.html',{})

def AdminRegister(request):
    return render(request,'AdminRegister.html',{})

def Logout(request):
    # Handle Django authentication logout
    if request.user.is_authenticated:
        from django.contrib.auth import logout
        logout(request)
    
    messages.success(request, "Logged out successfully.")
    return redirect('home')

def placement_cell_view(request):
    """
    Unified placement cell view that shows both login and register options
    """
    return render(request, 'placement_cell.html', {})

def placement_cell_login_action(request):
    """
    Handle placement cell login
    """
    if request.method == 'POST':
        # Try to get username from either field name
        username_input = request.POST.get('username') or request.POST.get('login-username')
        password = request.POST.get('password') or request.POST.get('login-password')
        remember = request.POST.get('remember')
        
        # Initialize user as None
        user = None
        
        # 1. First, try to authenticate treating input as username/email (standard behavior)
        user = authenticate(request, username=username_input, password=password)
        
        # 2. If that failed, try to find a PlacementCell with this ID and authenticate with its user's username
        if user is None:
            try:
                # Check if the input matches a Placement Cell ID
                placement_cell_obj = PlacementCell.objects.get(placement_cell_id=username_input)
                # If found, try to authenticate using the associated user's username (which is the email)
                user = authenticate(request, username=placement_cell_obj.user.username, password=password)
            except PlacementCell.DoesNotExist:
                # Not a valid Placement Cell ID either
                pass
        
        # 3. If that also failed, try to find a User with this Email and authenticate
        if user is None:
            try:
                # Check if the input matches a User email
                user_obj = User.objects.get(email=username_input)
                # If found, try to authenticate using that user's username
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                # Not a valid email or multiple users with same email
                pass
        
        if user is not None:
            # Check if user has placement cell profile
            try:
                placement_cell = PlacementCell.objects.get(user=user)
                if not placement_cell.is_active:
                    messages.error(request, 'Your placement cell account is not active.')
                    return redirect('placement_cell')
                
                # Login user
                login(request, user)
                
                # Set session variables for AdminRegistration compatibility
                from users.models import AdminRegistration as UserAdminRegistration
                admin_info = UserAdminRegistration.objects.filter(username=user.username).first()
                if admin_info:
                    request.session['admin_username'] = admin_info.username
                    request.session['admin_email'] = admin_info.email
                    request.session['admin_institution'] = admin_info.institution_name
                else:
                    # Fallback if no AdminRegistration found
                    request.session['admin_username'] = user.username
                    request.session['admin_email'] = user.email
                    request.session['admin_institution'] = placement_cell.institution_name

                # Handle remember me
                if not remember:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                
                messages.success(request, f'Welcome back, {placement_cell.institution_name}!')
                return redirect('AdminHome')  # Redirect to admin dashboard
                
            except PlacementCell.DoesNotExist:
                messages.error(request, 'This account is not registered as a placement cell.')
                return redirect('placement_cell')
        else:
            messages.error(request, 'Invalid placement cell ID or password.')
    
    return redirect('placement_cell')

def placement_cell_register_action(request):
    """
    Handle placement cell registration
    """
    if request.method == 'POST':
        # Try to get fields from either field name
        placement_cell_id = request.POST.get('username') or request.POST.get('register-username')
        email = request.POST.get('email') or request.POST.get('register-email')
        password = request.POST.get('password') or request.POST.get('register-password')
        confirm_password = request.POST.get('confirm_password') or request.POST.get('register-confirm-password')
        institution = request.POST.get('institution') or request.POST.get('register-institution') or request.POST.get('institution_name')
        terms = request.POST.get('terms')
        
        # Validation
        if not all([placement_cell_id, email, password, confirm_password, institution]):
            messages.error(request, 'All fields are required.')
            return redirect('placement_cell')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('placement_cell')
        
        if not terms:
            messages.error(request, 'You must agree to the terms and conditions.')
            return redirect('placement_cell')
        
        # Check if placement cell ID already exists
        if PlacementCell.objects.filter(placement_cell_id=placement_cell_id).exists():
            messages.error(request, 'Placement Cell ID already exists.')
            return redirect('placement_cell')
        
        # Check if institution name already exists (case-insensitive)
        if PlacementCell.objects.filter(institution_name__iexact=institution).exists():
            messages.error(request, 'An account for this Institution already exists.')
            return redirect('placement_cell')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('placement_cell')
        
        try:
            # Create user account
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                is_staff=True,  # Placement cell users are staff
                is_active=True
            )
            
            # Create placement cell profile
            placement_cell = PlacementCell.objects.create(
                user=user,
                placement_cell_id=placement_cell_id,
                institution_name=institution,
                email=email
            )

            # Also create AdminRegistration record for compatibility with existing admin views
            from users.models import AdminRegistration as UserAdminRegistration
            UserAdminRegistration.objects.get_or_create(
                username=email,
                defaults={
                    'password': password,
                    'email': email,
                    'institution_name': institution if institution in ['SCCE', 'SCIT'] else 'SCCE',
                    'status': 'Activated'
                }
            )
            
            # Auto-login the user after successful registration
            login(request, user)
            
            # Set session variables for AdminRegistration compatibility
            request.session['admin_username'] = user.username
            request.session['admin_email'] = user.email
            request.session['admin_institution'] = institution

            request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(request, f'Registration successful! Welcome, {institution}!')
            return redirect('AdminHome')  # Redirect to admin dashboard
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('placement_cell')

def placement_cell_dashboard(request):
    """
    Placement cell dashboard view
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('placement_cell')
    
    try:
        placement_cell = PlacementCell.objects.get(user=request.user)
        
        # Get some basic stats (you can enhance these later)
        total_students = 0  # You can calculate actual stats
        active_placements = 0
        pending_approvals = 0
        recent_activities = []  # You can fetch actual activities
        
        context = {
            'placement_cell': placement_cell,
            'total_students': total_students,
            'active_placements': active_placements,
            'pending_approvals': pending_approvals,
            'recent_activities': recent_activities,
        }
        
        return render(request, 'placement_cell_dashboard.html', context)
        
    except PlacementCell.DoesNotExist:
        messages.error(request, 'Placement cell profile not found.')
        return redirect('placement_cell')

# Placement Drive Management Views
def admin_placement_drives(request):
    """Unified admin dashboard for both drives and tests"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
    
    # Get both drives and readiness tests
    drives_qs = PlacementActivity.objects.filter(
        placement_cell=placement_cell,
        activity_type='drive'
    )
    
    tests_qs = PlacementActivity.objects.filter(
        placement_cell=placement_cell,
        activity_type='readiness_test'
    )

    # Apply search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        drives_qs = drives_qs.filter(
            Q(company_name__icontains=search_query) |
            Q(job_role__icontains=search_query) |
            Q(title__icontains=search_query)
        )
        tests_qs = tests_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    drives = drives_qs.order_by('-created_at')
    
    # Update status for each drive before rendering
    for drive in drives:
        drive.save()
        
    tests = tests_qs.order_by('-created_at')
    
    context = {
        'drives': drives,
        'tests': tests,
        'placement_cell': placement_cell,
        'search_query': search_query,
    }
    return render(request, 'admins/placement_drives.html', context)

def admin_analysis(request):
    """View for Executive Analysis & Summary Dashboard"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
    
    # Time ranges for growth calculations
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    # 1. Top Stats
    
    # Total Students & Growth
    total_students = PlacementCellStudent.objects.filter(placement_cell=placement_cell).count()
    
    students_last_30 = PlacementCellStudent.objects.filter(
        placement_cell=placement_cell,
        created_at__gte=thirty_days_ago
    ).count()
    students_prev_30 = PlacementCellStudent.objects.filter(
        placement_cell=placement_cell,
        created_at__gte=sixty_days_ago,
        created_at__lt=thirty_days_ago
    ).count()
    growth_students = calculate_growth(students_last_30, students_prev_30) if students_last_30 > 0 or students_prev_30 > 0 else None

    # Active Drives
    active_drives_qs = PlacementActivity.objects.filter(
        placement_cell=placement_cell, 
        activity_type='drive', 
        status__in=['upcoming', 'ongoing']
    )
    active_drives_count = active_drives_qs.count()
    
    # Students Applied & Growth
    all_drives = PlacementActivity.objects.filter(
        placement_cell=placement_cell,
        activity_type='drive'
    )
    # Total applied from aggregate (as per original logic)
    students_applied = all_drives.aggregate(total=Sum('current_applicants'))['total'] or 0
    
    # Growth based on DriveApplication model
    applied_last_30 = DriveApplication.objects.filter(
        drive__placement_cell=placement_cell,
        application_date__gte=thirty_days_ago
    ).count()
    applied_prev_30 = DriveApplication.objects.filter(
        drive__placement_cell=placement_cell,
        application_date__gte=sixty_days_ago,
        application_date__lt=thirty_days_ago
    ).count()
    growth_applied = calculate_growth(applied_last_30, applied_prev_30) if applied_last_30 > 0 or applied_prev_30 > 0 else None

    # Students Placed & Growth
    students_placed = Placement.objects.filter(placement_cell=placement_cell).count()
    
    placed_last_30 = Placement.objects.filter(
        placement_cell=placement_cell,
        placement_date__gte=thirty_days_ago.date()
    ).count()
    placed_prev_30 = Placement.objects.filter(
        placement_cell=placement_cell,
        placement_date__gte=sixty_days_ago.date(),
        placement_date__lt=thirty_days_ago.date()
    ).count()
    growth_placed = calculate_growth(placed_last_30, placed_prev_30) if placed_last_30 > 0 or placed_prev_30 > 0 else None

    # Pace Message Logic
    pace_message = None
    if growth_placed and growth_placed > 10:
        pace_message = "🚀 Placements are growing faster than last month!"
    elif growth_applied and growth_applied > 20:
        pace_message = "🔥 Student interest is at an all-time high!"
    elif growth_students and growth_students > 5:
        pace_message = "📈 Student database is growing steadily."
    elif students_placed > 0:
        pace_message = f"Consistent progress: {students_placed} students placed so far."

    # 2. Placement Drive Manager (Table Data)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        all_drives = all_drives.filter(
            Q(company_name__icontains=search_query) |
            Q(job_role__icontains=search_query) |
            Q(title__icontains=search_query)
        )
    drives = all_drives.order_by('-drive_date', '-created_at')
    
    # 3. Live Placement Tracker
    today = timezone.now().date()
    placed_today = Placement.objects.filter(
        placement_cell=placement_cell,
        placement_date=today
    ).count()
    
    # Placeholder for shortlisted (use real data from DriveApplication if available)
    shortlisted_count = DriveApplication.objects.filter(
        drive__placement_cell=placement_cell,
        status='shortlisted'
    ).count()
    
    ongoing_drives_count = PlacementActivity.objects.filter(
        placement_cell=placement_cell,
        activity_type='drive',
        status='ongoing'
    ).count()

    # 4. Overall Placement Progress
    # Target: Total Students. Progress: Students Placed.
    placement_percentage = 0
    if total_students > 0:
        placement_percentage = int((students_placed / total_students) * 100)
        
    context = {
        'placement_cell': placement_cell,
        'total_students': total_students,
        'active_drives_count': active_drives_count,
        'students_applied': students_applied,
        'students_placed': students_placed,
        'drives': drives,
        'placed_today': placed_today,
        'shortlisted_count': shortlisted_count,
        'ongoing_drives_count': ongoing_drives_count,
        'placement_percentage': placement_percentage,
        'today': today,
        'growth_students': growth_students,
        'growth_applied': growth_applied,
        'growth_placed': growth_placed,
        'pace_message': pace_message,
        'search_query': search_query,
    }
    return render(request, 'admins/analysis.html', context)

def student_classification(request):
    """View for Student Readiness (Readiness Tests)"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
    
    # In this view, we'll use the results from ReadinessTestResult which is the model
    # where students actually submit their data.
    from .models import ReadinessTestResult, ReadinessTest, PlacementActivity
    
    # Load the readiness test activity for this placement cell
    current_test = PlacementActivity.objects.filter(placement_cell=placement_cell, activity_type='readiness_test').first()
    
    if not current_test:
        # Create a default readiness test activity if none exists
        current_test = PlacementActivity.objects.create(
            placement_cell=placement_cell,
            activity_type='readiness_test',
            title='Global Readiness Assessment',
            description='Standardized assessment for student placement readiness.',
            date=timezone.now().date(),
            time=timezone.now().time(),
            location='Online',
            target_audience='All Students',
            max_participants=1000,
            is_active=False
        )
    
    thresholds = {
        'placement_ready_threshold': 70,
        'needs_improvement_threshold': 40,
        'at_risk_threshold': 0
    }
    
    # Load thresholds (linked to the ReadinessTest model ID for storage)
    rt_model = ReadinessTest.objects.first()
    if rt_model:
        # Sync activity status with test model status for UI consistency
        is_enabled = (rt_model.status == 'enabled')
        if current_test.is_active != is_enabled:
            current_test.is_active = is_enabled
            current_test.save()
            
        try:
            import os, json
            from django.conf import settings
            config_path = os.path.join(settings.BASE_DIR, 'radinesstest', 'config', f'{rt_model.id}.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as cf:
                    thresholds = json.load(cf)
        except Exception:
            pass

    # Student Insights Logic
    search_query = request.GET.get('search', '').strip()
    classification_filter = request.GET.get('classification', '')
    
    # Filter students belonging to this placement cell
    # Students are linked to placement cells via college code in UserRegistration
    college_code = placement_cell.college_code
    
    results = ReadinessTestResult.objects.filter(
        student__college_name=college_code
    ).select_related('student', 'test').order_by('-completed_at')
    
    if search_query:
        results = results.filter(
            Q(student__userid__icontains=search_query) |
            Q(student__email__icontains=search_query)
        )
    
    if classification_filter:
        results = results.filter(classification=classification_filter)
    
    # Process strengths and weaknesses for each result
    # ReadinessTestResult uses aptitude_score, reasoning_score, etc. as raw counts
    # We need to convert them to percentages for the strengths/weaknesses logic
    # Aptitude: 9, Reasoning: 9, English: 6, Core: 36
    for res in results:
        res.strengths = []
        res.weaknesses = []
        
        # Add properties for template compatibility if they don't exist
        # The template expects readiness_classification, aptitude_score as %, etc.
        res.readiness_classification = res.classification
        
        # Calculate percentages for internal logic
        apt_pct = (res.aptitude_score / 9 * 100) if 9 > 0 else 0
        reas_pct = (res.reasoning_score / 9 * 100) if 9 > 0 else 0
        eng_pct = (res.english_score / 6 * 100) if 6 > 0 else 0
        core_pct = (res.core_score / 36 * 100) if 36 > 0 else 0
        
        # Attach percentage and raw scores to result object for template rendering
        res.score = int(res.percentage)
        res.test_title = "Global Readiness Assessment"
        res.aptitude_score_pct = int(apt_pct)
        res.reasoning_score_pct = int(reas_pct)
        res.english_score_pct = int(eng_pct)
        res.core_subjects_score_pct = int(core_pct)
        
        # Raw marks
        res.aptitude_raw = res.aptitude_score
        res.reasoning_raw = res.reasoning_score
        res.english_raw = res.english_score
        res.core_raw = res.core_score
        res.total_correct_raw = res.total_correct
        res.total_questions_raw = res.total_questions
        
        categories = [
            ('Aptitude', apt_pct),
            ('Reasoning', reas_pct),
            ('English', eng_pct),
            ('Core Subjects', core_pct)
        ]
        
        for name, score in categories:
            if score >= 75:
                res.strengths.append(name)
            elif score < 50:
                res.weaknesses.append(name)

    # Summary Metrics
    total_attempts = results.count()
    ready_count = results.filter(classification='placement_ready').count()
    improvement_count = results.filter(classification='needs_improvement').count()
    at_risk_count = results.filter(classification='at_risk').count()

    # 1. Department Readiness Heatmap
    # Aggregate by student__branch (department)
    dept_readiness = results.values('student__branch').annotate(
        total=Count('id'),
        ready=Count('id', filter=Q(classification='placement_ready')),
        improvement=Count('id', filter=Q(classification='needs_improvement')),
        at_risk=Count('id', filter=Q(classification='at_risk'))
    ).order_by('-total')

    for dept in dept_readiness:
        dept['ready_pct'] = int((dept['ready'] / dept['total'] * 100)) if dept['total'] > 0 else 0
        dept['improvement_pct'] = int((dept['improvement'] / dept['total'] * 100)) if dept['total'] > 0 else 0
        dept['at_risk_pct'] = int((dept['at_risk'] / dept['total'] * 100)) if dept['total'] > 0 else 0

    # 2. Year-wise Risk Distribution
    # Aggregate by student__year
    year_risk = results.values('student__year').annotate(
        total=Count('id'),
        at_risk=Count('id', filter=Q(classification='at_risk')),
        needs_improvement=Count('id', filter=Q(classification='needs_improvement')),
        placement_ready=Count('id', filter=Q(classification='placement_ready'))
    ).order_by('student__year')

    # 3. Skill Gap Clusters (Based on Weaknesses)
    skill_gaps = {
        'Aptitude': results.filter(aptitude_score__lt=5).count(), # Assuming < 50% is a gap
        'Reasoning': results.filter(reasoning_score__lt=5).count(),
        'English': results.filter(english_score__lt=3).count(),
        'Core Subjects': results.filter(core_score__lt=18).count()
    }

    # 4. Placement Trend Comparison (Year vs Previous Year)
    # Using Placement model
    current_year = timezone.now().year
    prev_year = current_year - 1
    
    current_placements = Placement.objects.filter(
        placement_cell=placement_cell,
        placement_date__year=current_year
    ).count()
    
    prev_placements = Placement.objects.filter(
        placement_cell=placement_cell,
        placement_date__year=prev_year
    ).count()

    trend_comparison = {
        'current_year': current_year,
        'prev_year': prev_year,
        'current_count': current_placements,
        'prev_count': prev_placements,
        'growth': calculate_growth(current_placements, prev_placements)
    }
    
    # Test Control Actions
    can_reset = results.exists()
    
    context = {
        'results': results,
        'search_query': search_query,
        'classification_filter': classification_filter,
        'thresholds': thresholds,
        'current_test': current_test,
        'can_reset': can_reset,
        'dept_readiness': dept_readiness,
        'year_risk': year_risk,
        'skill_gaps': skill_gaps,
        'trend_comparison': trend_comparison,
        'metrics': {
            'total': total_attempts,
            'ready': ready_count,
            'improvement': improvement_count,
            'at_risk': at_risk_count,
            'ready_percent': int((ready_count / total_attempts * 100)) if total_attempts > 0 else 0
        }
    }
    return render(request, 'admins/studentclassification.html', context)

@require_http_methods(["POST"])
def admin_update_readiness_thresholds(request, activity_id):
    """Update thresholds for a readiness test (no DB field; persisted to filesystem)"""
    if not request.user.is_staff:
        return redirect('unified_login')
    test = get_object_or_404(PlacementActivity, id=activity_id, activity_type='readiness_test')
    try:
        pr = float(request.POST.get('placement_ready_threshold', 70))
        ni = float(request.POST.get('needs_improvement_threshold', 40))
        ar = float(request.POST.get('at_risk_threshold', 0))
        
        # Validation: ensure logical order
        if pr <= ni:
            messages.error(request, 'Ready threshold must be higher than Improvement threshold.')
            return redirect('readiness_admin:student_classification')
        if ni <= ar:
            messages.error(request, 'Improvement threshold must be higher than At Risk floor.')
            return redirect('readiness_admin:student_classification')

        from .models import ReadinessTest
        rt_model = ReadinessTest.objects.first()
        if not rt_model:
            # Create a default one if none exists
            rt_model = ReadinessTest.objects.create(status='disabled')

        import os, json
        from django.conf import settings
        config_dir = os.path.join(settings.BASE_DIR, 'radinesstest', 'config')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, f'{rt_model.id}.json')
        
        config_data = {
            'placement_ready_threshold': pr,
            'needs_improvement_threshold': ni,
            'at_risk_threshold': ar
        }
        
        with open(config_path, 'w', encoding='utf-8') as cf:
            cf.write(json.dumps(config_data, indent=2))
            
        messages.success(request, f'Classification standards updated: Ready ({pr}%), Improve ({ni}%)')
    except Exception as e:
        messages.error(request, f'Failed to update thresholds: {e}')
    return redirect('readiness_admin:student_classification')

def admin_add_placement_drive(request):
    """Add new placement drive"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
    
    if request.method == 'POST':
        # Process drive creation
        form_data = request.POST.copy()
        form_data['activity_type'] = 'drive'
        
        # Handle date/time fields properly
        drive_date = form_data.get('drive_date')
        drive_end_date = form_data.get('drive_end_date')
        application_deadline = form_data.get('application_deadline')
        
        # Create drive with proper placement_cell instance
        drive = PlacementActivity.objects.create(
            placement_cell=placement_cell,  # Pass the instance, not ID
            activity_type='drive',
            title=form_data.get('title'),
            description=form_data.get('description'),
            date=form_data.get('date'),
            time=form_data.get('time'),
            location=form_data.get('location'),
            company_name=form_data.get('company_name'),
            job_role=form_data.get('job_role'),
            package_range=form_data.get('package_range'),
            drive_date=drive_date,
            drive_end_date=drive_end_date,
            application_deadline=application_deadline,
            contact_person=form_data.get('contact_person'),
            contact_email=form_data.get('contact_email'),
            contact_phone=form_data.get('contact_phone'),
            min_cgpa=form_data.get('min_cgpa') or None,
            eligible_departments=form_data.get('eligible_departments'),
            eligible_years=form_data.get('eligible_years'),
            additional_requirements=form_data.get('additional_requirements'),
            max_applicants=form_data.get('max_applicants') or 100,
            # Fix IntegrityError: Provide defaults for required fields from original model
            target_audience=form_data.get('eligible_departments') or "All Students",
            max_participants=form_data.get('max_applicants') or 100,
        )
        messages.success(request, 'Placement drive created successfully!')
        return redirect('admin_placement_drives')
    
    return render(request, 'admins/add_placement_drive.html')

def admin_add_readiness_test(request):
    """Add new readiness test"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
    
    if request.method == 'POST':
        # Process test creation
        form_data = request.POST.copy()
        
        # Create test with proper placement_cell instance
        test = PlacementActivity.objects.create(
            placement_cell=placement_cell,  # Pass the instance, not ID
            activity_type='readiness_test',
            title=form_data.get('title'),
            description=form_data.get('description'),
            date=form_data.get('date'),
            time=form_data.get('time'),
            location=form_data.get('location'),
            target_audience=form_data.get('target_audience'),
            max_participants=form_data.get('max_participants'),
            exam_duration=form_data.get('exam_duration') or 60,
            questions=[],  # Will be populated later
        )
        # Persist thresholds to filesystem (radinesstest/config/<test_id>.json)
        try:
            import os, json
            from django.conf import settings
            config_dir = os.path.join(settings.BASE_DIR, 'radinesstest', 'config')
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, f'{test.id}.json')
            thresholds = {
                'placement_ready_threshold': float(form_data.get('placement_ready_threshold', 70)),
                'needs_improvement_threshold': float(form_data.get('needs_improvement_threshold', 40)),
                'at_risk_threshold': float(form_data.get('at_risk_threshold', 0)),
            }
            with open(config_path, 'w', encoding='utf-8') as cf:
                cf.write(json.dumps(thresholds, indent=2))
        except Exception as e:
            print(f"Error writing thresholds config: {e}")
        messages.success(request, 'Readiness test created successfully!')
        return redirect('readiness_admin:student_classification')
    
    return render(request, 'admins/classification.html')

def admin_delete_activity(request, activity_id):
    """Delete drive or test"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    activity = get_object_or_404(PlacementActivity, id=activity_id)
    activity.delete()
    messages.success(request, f'{activity.get_activity_type_display()} deleted successfully!')
    return redirect('admin_placement_drives')

def admin_view_activity(request, activity_id):
    """View drive or test details"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    activity = get_object_or_404(PlacementActivity, id=activity_id)
    return render(request, 'admins/view_activity.html', {'activity': activity})

def admin_drive_applications(request, drive_id):
    """View applications for a specific drive"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    drive = get_object_or_404(PlacementActivity, id=drive_id, activity_type='drive')
    applications = drive.applications.all().select_related('student')
    
    # Attach student_record (PlacementCellStudent) to each application
    placement_cell = drive.placement_cell
    student_ids = [app.student.student_id for app in applications if app.student.student_id]
    emails = [app.student.email for app in applications]
    
    if student_ids or emails:
        pcs_records = PlacementCellStudent.objects.filter(
            placement_cell=placement_cell
        ).filter(
            Q(student_id__in=student_ids) | Q(email__in=emails)
        )
        
        pcs_map_by_id = {pcs.student_id: pcs for pcs in pcs_records if pcs.student_id}
        pcs_map_by_email = {pcs.email: pcs for pcs in pcs_records if pcs.email}
        
        for app in applications:
            pcs = None
            if app.student.student_id:
                pcs = pcs_map_by_id.get(app.student.student_id)
            if not pcs:
                pcs = pcs_map_by_email.get(app.student.email)
            app.student_record = pcs
    
    context = {
        'drive': drive,
        'applications': applications,
    }
    return render(request, 'admins/opted.html', context)

def admin_test_results(request):
    """View all test results"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
    
    test_id = request.GET.get('test_id')
    search_query = request.GET.get('search', '').strip()
    
    # Filter by student's college name since ReadinessTest is global
    college_code = placement_cell.college_code
    
    results = ReadinessTestResult.objects.filter(
        student__college_name=college_code
    ).select_related('student', 'test').order_by('-completed_at')
    
    if test_id:
        results = results.filter(test_id=test_id)
        
    if search_query:
        results = results.filter(
            Q(student__userid__icontains=search_query) |
            Q(student__email__icontains=search_query)
        )
    
    # Add properties for template compatibility
    for res in results:
        res.score = int(res.percentage)
        res.readiness_classification = res.classification
        # Since ReadinessTest doesn't have a title, we use a default
        res.test_title = "Global Readiness Assessment"
        
        # Calculate percentages and raw marks
        res.aptitude_score_pct = int((res.aptitude_score / 9 * 100) if 9 > 0 else 0)
        res.reasoning_score_pct = int((res.reasoning_score / 9 * 100) if 9 > 0 else 0)
        res.english_score_pct = int((res.english_score / 6 * 100) if 6 > 0 else 0)
        res.core_subjects_score_pct = int((res.core_score / 36 * 100) if 36 > 0 else 0)
        
        res.aptitude_raw = res.aptitude_score
        res.reasoning_raw = res.reasoning_score
        res.english_raw = res.english_score
        res.core_raw = res.core_score
        res.total_correct_raw = res.total_correct
        res.total_questions_raw = res.total_questions
    
    context = {
        'results': results,
        'search_query': search_query,
        'test_id': test_id,
    }
    return render(request, 'admins/test_results.html', context)

def admin_toggle_activity_status(request, activity_id):
    """Toggle activity status (Active/Inactive)"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    activity = get_object_or_404(PlacementActivity, id=activity_id)
    action = request.GET.get('action')
    
    if action == 'activate':
        activity.is_active = True
    elif action == 'deactivate':
        activity.is_active = False
    else:
        # Default toggle behavior
        activity.is_active = not activity.is_active
    
    # Also update choice-based status if it's a drive
    if activity.activity_type == 'drive':
        if activity.is_active:
            activity.status = 'ongoing'
        else:
            activity.status = 'cancelled'
    
    # Sync with ReadinessTest model if this is a readiness test activity
    if activity.activity_type == 'readiness_test':
        from .models import ReadinessTest
        # For simplicity, we assume there's only one global test record
        rt = ReadinessTest.objects.first()
        if rt:
            rt.status = 'enabled' if activity.is_active else 'disabled'
            rt.save()
    
    activity.save()
    
    status_text = "Activated" if activity.is_active else "Deactivated"
    messages.success(request, f'{activity.title} has been {status_text}!')
    
    # Redirect back to where the request came from
    referer = request.META.get('HTTP_REFERER')
    if referer and 'student-classification' in referer:
        return redirect('readiness_admin:student_classification')
    return redirect('admin_placement_drives')

def admin_edit_activity(request, activity_id):
    """Edit drive or test"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    activity = get_object_or_404(PlacementActivity, id=activity_id)
    if request.method == 'POST':
        # Update common fields
        activity.title = request.POST.get('title')
        activity.description = request.POST.get('description')
        activity.date = request.POST.get('date')
        activity.time = request.POST.get('time')
        activity.location = request.POST.get('location')
        activity.min_cgpa = request.POST.get('min_cgpa') or None
        activity.eligible_departments = request.POST.get('eligible_departments')
        
        if activity.activity_type == 'drive':
            activity.company_name = request.POST.get('company_name')
            activity.job_role = request.POST.get('job_role')
            activity.package_range = request.POST.get('package_range')
            activity.drive_date = request.POST.get('drive_date')
            activity.drive_end_date = request.POST.get('drive_end_date')
            activity.application_deadline = request.POST.get('application_deadline')
            activity.contact_person = request.POST.get('contact_person')
            activity.contact_email = request.POST.get('contact_email')
            activity.contact_phone = request.POST.get('contact_phone')
            activity.eligible_years = request.POST.get('eligible_years')
            activity.additional_requirements = request.POST.get('additional_requirements')
            activity.max_applicants = request.POST.get('max_applicants') or 100
        
        elif activity.activity_type == 'readiness_test':
            activity.exam_duration = request.POST.get('exam_duration') or 60
            activity.target_audience = request.POST.get('target_audience')
            activity.max_participants = request.POST.get('max_participants') or 100
        
        activity.save()
        messages.success(request, 'Activity updated successfully!')
        return redirect('admin_placement_drives')
        
    return render(request, 'admins/edit_activity.html', {'activity': activity})

def admin_all_students(request):
    """View and manage all students"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')

    students = PlacementCellStudent.objects.filter(placement_cell=placement_cell).order_by('name')
    
    context = {
        'students': students,
        'total_students': students.count(),
        'active_students': students.filter(is_active=True).count(),
        'inactive_students': students.filter(is_active=False).count(),
    }
    return render(request, 'admins/all_students.html', context)

def admin_reset_readiness_test(request, test_id):
    """Reset all results for a specific readiness test"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    # Check if placement cell exists
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found.')
        return redirect('AdminHome')

    # Delete results for students belonging to this placement cell
    college_code = placement_cell.college_code
    deleted_count, _ = ReadinessTestResult.objects.filter(
        student__college_name=college_code
    ).delete()
    
    messages.success(request, f'Successfully reset readiness test results. {deleted_count} student records have been cleared.')
    return redirect('readiness_admin:student_classification')

def admin_toggle_student_status(request, student_id):
    """Toggle student active status"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')

    student = get_object_or_404(PlacementCellStudent, id=student_id, placement_cell=placement_cell)
    student.is_active = not student.is_active
    student.save()
    
    status_msg = "activated" if student.is_active else "deactivated"
    messages.success(request, f'Student {student.name} has been {status_msg}.')
    return redirect('admin_all_students')

@require_http_methods(["POST"])
def admin_update_student(request, student_id):
    """Update student marks percentage and backlog via AJAX"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        placement_cell = PlacementCell.objects.filter(user=request.user).first()
        if not placement_cell:
            return JsonResponse({'success': False, 'message': 'No placement cell found'})
        
        student = get_object_or_404(PlacementCellStudent, id=student_id, placement_cell=placement_cell)
        
        marks_percentage = request.POST.get('marks_percentage')
        backlog = request.POST.get('backlog')
        year = request.POST.get('year')
        
        if year is not None:
            try:
                year_value = int(year)
                if 1 <= year_value <= 4:
                    student.year = year_value
                else:
                    return JsonResponse({'success': False, 'message': 'Year must be between 1 and 4'})
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid year value'})
        
        if marks_percentage is not None:
            try:
                marks_value = float(marks_percentage)
                if 0 <= marks_value <= 100:
                    student.marks_percentage = marks_value
                else:
                    return JsonResponse({'success': False, 'message': 'Marks percentage must be between 0 and 100'})
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid marks percentage value'})
        
        if backlog is not None:
            try:
                backlog_value = int(backlog)
                if backlog_value >= 0:
                    student.backlog = backlog_value
                else:
                    return JsonResponse({'success': False, 'message': 'Backlog cannot be negative'})
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid backlog value'})
        
        student.save()
        
        # Also update corresponding UserRegistration if it exists
        from users.models import UserRegistration, Student
        try:
            user_reg = UserRegistration.objects.get(student_id=student.student_id)
            # Keep academic_marks in sync with student's marks percentage
            if student.marks_percentage is not None:
                user_reg.academic_marks = float(student.marks_percentage)
            if student.backlog is not None:
                user_reg.backlog = student.backlog
            if student.year is not None:
                user_reg.year = str(student.year)  # Update year as string
            user_reg.save()
            
            # Also sync to Student model
            try:
                student_record = Student.objects.get(userid=user_reg.userid)
                student_record.academic_marks = user_reg.academic_marks
                student_record.backlog = user_reg.backlog
                student_record.year = user_reg.year
                student_record.save()
            except Student.DoesNotExist:
                pass
                
        except UserRegistration.DoesNotExist:
            pass
        
        return JsonResponse({'success': True, 'message': 'Student updated successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def admin_opted_in(request):
    """View all opted-in students across all drives"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
        
    # Fetch all applications for drives belonging to this placement cell
    applications_qs = DriveApplication.objects.filter(
        drive__placement_cell=placement_cell
    ).select_related('student', 'drive')
    
    # Apply search filter if query exists
    search_query = request.GET.get('search', '').strip()
    if search_query:
        applications_qs = applications_qs.filter(
            Q(full_name__icontains=search_query) |
            Q(drive__company_name__icontains=search_query) |
            Q(student__userid__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(hall_ticket_number__icontains=search_query)
        )
    
    applications = applications_qs.order_by('-application_date')
    
    # Attach student_record (PlacementCellStudent) to each application for resume access
    student_ids = [app.student.student_id for app in applications if app.student.student_id]
    emails = [app.student.email for app in applications]
    
    if student_ids or emails:
        # Fetch relevant PlacementCellStudent records
        pcs_records = PlacementCellStudent.objects.filter(
            placement_cell=placement_cell
        ).filter(
            Q(student_id__in=student_ids) | Q(email__in=emails)
        )
        
        # Create lookups
        pcs_map_by_id = {pcs.student_id: pcs for pcs in pcs_records if pcs.student_id}
        pcs_map_by_email = {pcs.email: pcs for pcs in pcs_records if pcs.email}
        
        # Attach records
        for app in applications:
            pcs = None
            if app.student.student_id:
                pcs = pcs_map_by_id.get(app.student.student_id)
            if not pcs:
                pcs = pcs_map_by_email.get(app.student.email)
            app.student_record = pcs
    
    context = {
        'applications': applications,
        'search_query': search_query,
    }
    return render(request, 'admins/all_opted.html', context)

def admin_application_detail(request, application_id):
    """Get application details for AJAX modal"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    application = get_object_or_404(DriveApplication, id=application_id)
    
    # Check if placement activity belongs to this admin's placement cell
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell or application.drive.placement_cell != placement_cell:
        return JsonResponse({'error': 'Unauthorized access to this application'}, status=403)

    data = {
                'full_name': application.full_name or application.student.userid,
                'student_id': application.student.student_id or application.student.userid,
                'hall_ticket': application.hall_ticket_number or "Not Provided",
                'email': application.gmail,
        'phone': application.phone_number,
        'branch': application.branch,
        'cgpa': str(application.percentage_cgpa),
        'company': application.drive.company_name,
        'role': application.drive.title,
        'status': application.status,
        'applied_date': application.application_date.strftime("%B %d, %Y at %I:%M %p"),
        'notes': application.notes or "No notes provided.",
    }
    
    return JsonResponse(data)

@require_POST
def admin_update_application_status(request, application_id):
    """Update application status and sync with outcome registry if placed"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    application = get_object_or_404(DriveApplication, id=application_id)
    new_status = request.POST.get('status')
    
    # Check if placement activity belongs to this admin's placement cell
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell or application.drive.placement_cell != placement_cell:
        return JsonResponse({'success': False, 'message': 'Unauthorized access'}, status=403)

    if new_status not in dict(DriveApplication.APPLICATION_STATUS_CHOICES):
        return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

    application.status = new_status
    application.save()

    # Sync with Placement model (outcome registry) for any status change
    from .models import PlacementCellStudent, Placement
    
    student_id = application.student.student_id
    student_record = PlacementCellStudent.objects.filter(
        placement_cell=placement_cell,
        student_id=student_id
    ).first()

    if not student_record:
        # Create student record if it doesn't exist so they show up in registry
        student_record = PlacementCellStudent.objects.create(
            placement_cell=placement_cell,
            student_id=application.student.student_id or application.student.userid,
            name=application.full_name or application.student.userid,
            email=application.student.email,
            phone=application.phone_number or application.student.phone or "N/A",
            department=application.branch or "General",
            year=application.student_year or 0,
            marks_percentage=application.percentage_cgpa or 0.0
        )

    if student_record:
        # Update student record
        if new_status == 'placed':
            student_record.is_placed = True
            student_record.company_placed = application.drive.company_name
        
        # Try to parse package from drive if available
        try:
            # Basic parsing for package range like "5.5 - 7.0"
            pkg_str = application.drive.package_range.split('-')[0].strip()
            student_record.package_offered = float(pkg_str)
        except:
            if not student_record.package_offered:
                student_record.package_offered = 0.0
        student_record.save()

        # Create or update entry in Outcome Registry (Placement model)
        # We use update_or_create to ensure the record reflects the latest status
        Placement.objects.update_or_create(
            placement_cell=placement_cell,
            student=student_record,
            company_name=application.drive.company_name,
            defaults={
                'job_role': application.drive.job_role or application.drive.title,
                'package_offered': student_record.package_offered or 0.0,
                'location': application.drive.location or "TBD",
                'placement_date': timezone.now().date(),
                'is_verified': True, # Admin updates are considered verified
                'status': new_status # Store the current application status
            }
        )

    return JsonResponse({'success': True, 'message': 'Status updated successfully'})

def outcome_registry(request):
    """View for placed students registry"""
    if not request.user.is_staff:
        return redirect('unified_login')
    
    placement_cell = PlacementCell.objects.filter(user=request.user).first()
    if not placement_cell:
        messages.error(request, 'No placement cell found for your account.')
        return redirect('AdminHome')
        
    # Fetch all confirmed placements or those in active interview rounds
    # Filter for verified placements or statuses that indicate round 1, round 2, etc.
    placements = Placement.objects.filter(
        placement_cell=placement_cell
    ).select_related('student', 'student__placement_cell').order_by('-updated_at')
    
    return render(request, 'admins/outcome_registry.html', {'placements': placements})
