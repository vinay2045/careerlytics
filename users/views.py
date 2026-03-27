from django.shortcuts import render,HttpResponse, redirect
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.template import RequestContext
from django.http import HttpResponse
import json
import pickle
from django.urls import reverse
from users.models import UserRegistration,Document,Student,NonStudent
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import secrets
import os, time
from base64 import urlsafe_b64decode
from .models import Document, DocumentPerformance, UserRegistration

import smtplib
from email.mime.text import MIMEText
from Careerlytics.models import PlacementActivity, DriveApplication, PlacementCellStudent, ReadinessTest, ReadinessTestResult
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import io, base64
import re, os
from django.views.decorators.http import require_http_methods
from decimal import Decimal
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import requests
import random
from google import genai

# Import Google OAuth functions
from .google_auth import google_login_redirect, google_callback, google_complete_registration, google_register_redirect

def UserRegister(request):
    return render(request, 'UserRegister.html')


def send_emaill(sender_email, sender_password, recipient_email, subject, body, attachment_path):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))
    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read()) 
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename= {attachment_path.split("/")[-1]}'
    )

    message.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())




def UserRegisterAction(request):
    if request.method == 'POST':
        userid = request.POST.get('userid', '').strip()
        password = request.POST.get('pass')
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        # DOB is now optional
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        pic = request.FILES.get('pic')
        
        # New fields for user type
        user_type = request.POST.get('user_type', 'student')
        student_id = request.POST.get('student_id', '').strip()
        college_name = request.POST.get('college_name')
        year = request.POST.get('year')
        branch = request.POST.get('branch')
        academic_marks = request.POST.get('academic_marks')
        
        # Non-student specific fields
        profession = request.POST.get('profession')
        company = request.POST.get('company')
        experience_years = request.POST.get('experience_years')

        if not all([userid, password, email, mobile, gender, user_type]):
            messages.error(request, "All fields are required!")
            return redirect('user_register')

        # Additional validation for students
        if user_type == 'student':
            if not all([student_id, college_name, year, branch, academic_marks]):
                messages.error(request, "All student fields are required!")
                return redirect('user_register')
            try:
                academic_marks = float(academic_marks)
                if academic_marks < 0 or academic_marks > 100:
                    messages.error(request, "Academic marks must be between 0 and 100!")
                    return redirect('user_register')
            except ValueError:
                messages.error(request, "Invalid academic marks format!")
                return redirect('user_register')

        # Check if userid already exists in both models
        if UserRegistration.objects.filter(userid=userid).exists() or Student.objects.filter(userid=userid).exists() or NonStudent.objects.filter(userid=userid).exists():
            messages.error(request, "User ID already exists! Please choose a different User ID.")
            return redirect('user_register')
        
        # Check if email already exists in both models
        if UserRegistration.objects.filter(email=email).exists() or Student.objects.filter(email=email).exists() or NonStudent.objects.filter(email=email).exists():
            messages.error(request, "Email already registered! Please use a different email or try logging in.")
            return redirect('user_register')

        # Check if student_id already exists (only for students)
        if user_type == 'student' and student_id:
            if UserRegistration.objects.filter(student_id=student_id).exists() or Student.objects.filter(student_id=student_id).exists():
                messages.error(request, "Student ID already registered! Please check if you already have an account.")
                return redirect('user_register')

        try:
            # Parse DOB only if provided
            if dob:
                dob_parsed = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob_parsed = None
            
            # Save to appropriate model based on user type
            if user_type == 'student':
                # Validate student fields
                if not all([student_id, college_name, year, branch, academic_marks]):
                    messages.error(request, "All student fields are required!")
                    return redirect('user_register')
                try:
                    academic_marks = float(academic_marks)
                    if academic_marks < 0 or academic_marks > 100:
                        messages.error(request, "Academic marks must be between 0 and 100!")
                        return redirect('user_register')
                except ValueError:
                    messages.error(request, "Invalid academic marks format!")
                    return redirect('user_register')
                
                # Create UserRegistration (Legacy/Base)
                user_reg = UserRegistration.objects.create(
                    userid=userid,
                    password=password,
                    email=email,
                    mobile=mobile,
                    dob=dob_parsed,
                    gender=gender,
                    pic=pic,
                    status='Activated',
                    user_type='student',
                    student_id=student_id,
                    college_name=college_name,
                    year=year,
                    branch=branch,
                    academic_marks=academic_marks
                )

                # Link to placement cell
                try:
                    from .utils import link_student_to_placement_cell
                    link_success, link_msg = link_student_to_placement_cell(user_reg)
                    if link_success:
                        print(f"Successfully linked {userid} to placement cell: {link_msg}")
                    else:
                        print(f"Failed to link {userid} to placement cell: {link_msg}")
                except Exception as e:
                    print(f"Error linking student to placement cell: {e}")

                # Create Student record
                new_user = Student.objects.create(
                    userid=userid,
                    password=password,
                    email=email,
                    mobile=mobile,
                    dob=dob_parsed,
                    gender=gender,
                    pic=pic,
                    status='Activated',
                    student_id=student_id,
                    college_name=college_name,
                    year=year,
                    branch=branch,
                    academic_marks=academic_marks
                )
            else:
                # Create UserRegistration (Legacy/Base)
                UserRegistration.objects.create(
                    userid=userid,
                    password=password,
                    email=email,
                    mobile=mobile,
                    dob=dob_parsed,
                    gender=gender,
                    pic=pic,
                    status='Activated',
                    user_type='non_student'
                )

                # Create NonStudent record
                new_user = NonStudent.objects.create(
                    userid=userid,
                    password=password,
                    email=email,
                    mobile=mobile,
                    dob=dob_parsed,
                    gender=gender,
                    pic=pic,
                    status='Activated',
                    profession=profession,
                    company=company,
                    experience_years=float(experience_years) if experience_years else None
                )
           
            messages.success(request, "Registration successful! Welcome to your dashboard.")
            
            # Auto-login
            request.session['userid'] = new_user.userid
            request.session['email'] = new_user.email
            request.session['username'] = new_user.userid
            request.session['user_type'] = user_type
            
            return redirect('users:UserHome')
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('user_register')
    else:
        return render(request, 'UserRegister.html')


def UserLogin(request):
    return render(request, 'user_login.html')


def UserLoginCheck(request):
    if request.method == "POST":
        login_id = request.POST.get('userid', '').strip()  # This can be userid, email, or student_id
        pswd = request.POST.get('password')
        print("Login ID =", login_id, "Password =", pswd)
        
        try:
            # Try to get user by userid, email, or student_id
            user = UserRegistration.objects.filter(
                Q(userid=login_id) | 
                Q(email=login_id) | 
                Q(student_id=login_id)
            ).first()
            
            if not user:
                print("User not found")
                messages.error(request, "Invalid Student ID/Email or Password.")
                return redirect('users:user_login')
                
            print("Status =", user.status)
            print("User Type =", user.user_type)
            print("Database user found:", user)
            
            # Check password separately
            if user.password == pswd:
                if user.status == "Activated":
                    request.session['userid'] = user.userid
                    request.session['email'] = user.email
                    request.session['username'] = user.userid
                    request.session['user_type'] = user.user_type
                    
                    messages.success(request, f"Welcome {user.userid} ({user.get_user_type_display()})!")
                    
                    return redirect('users:UserHome')
                else:
                    messages.error(request, "Your account is not activated. Please wait for Placement Cell approval.")
                    return redirect('users:user_login')
            else:
                messages.error(request, "Invalid Student ID/Email or Password.")
                return redirect('users:user_login')
                
        except Exception as e:
            print(f"Login Error: {e}")
            messages.error(request, "An error occurred during login.")
            return redirect('users:user_login')
            
    return redirect('users:user_login')


def UserLogout(request):
    # Handle Django authentication logout
    if request.user.is_authenticated:
        from django.contrib.auth import logout
        logout(request)
    
    # Handle custom session logout
    for key in ['userid', 'email', 'username', 'user_type']:
        if key in request.session:
            del request.session[key]
    
    messages.success(request, "Student logged out successfully.")
    return redirect('home')  # Redirect to home page


def UserHome(request):
    # Check for custom session authentication first (UserRegistration model)
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if user:
        try:
            user_type = user.user_type
            
            # Get student data for dynamic messages
            student_record = None
            dashboard_message = None
            message_color = None
            
            if user.user_type == 'student':
                try:
                    student_record = PlacementCellStudent.objects.filter(email=user.email, is_active=True).first()
                    if not student_record and user.student_id:
                        student_record = PlacementCellStudent.objects.filter(student_id=user.student_id, is_active=True).first()
                    
                    if student_record:
                        backlog_count = student_record.backlog if student_record.backlog is not None else 0
                        percentage = float(student_record.marks_percentage or 0)
                        
                        print(f"DEBUG: Student record found - Backlog: {backlog_count}, Percentage: {percentage}")  # Debug line
                        
                        # Determine message based on backlogs and percentage
                        if backlog_count >= 2:
                            dashboard_message = "Work hard and increase focus to clear your backlogs!"
                            message_color = "red"
                        elif backlog_count > 0:
                            dashboard_message = "Increase focus and clear your backlogs soon!"
                            message_color = "orange"
                        else:  # No backlogs
                            if percentage >= 65:
                                dashboard_message = "You are going on good path, continue!"
                                message_color = "green"
                            elif percentage >= 55:
                                dashboard_message = "Increase your academic performance!"
                                message_color = "orange"
                            else:
                                dashboard_message = "Increase your percentage to improve placement chances!"
                                message_color = "red"
                    else:
                        print(f"DEBUG: No student_record found for user: {user.email}")  # Debug line
                        # Set message so the alert div appears (showing the "Data not available" state)
                        dashboard_message = "Please reach out to the placement cell to update your academic record."
                        message_color = "red"
                        
                    # Check for drive application updates (Congratulatory messages)
                    success_statuses = ['placed', 'hr_round', 'round_3', 'round_2', 'round_1', 'selected']
                    
                    # Fetch applications with these statuses
                    applications = DriveApplication.objects.filter(student=user, status__in=success_statuses)
                    
                    placement_message = None  # Initialize new variable
                    
                    if applications.exists():
                        # Define priority to show the most significant achievement
                        # Higher number = higher priority
                        status_priority = {
                            'placed': 6,
                            'hr_round': 5,
                            'round_3': 4,
                            'round_2': 3,
                            'round_1': 2,
                            'selected': 1
                        }
                        
                        best_app = None
                        max_priority = 0
                        
                        for app in applications:
                            priority = status_priority.get(app.status, 0)
                            if priority > max_priority:
                                max_priority = priority
                                best_app = app
                        
                        if best_app:
                             # Construct the message
                             status_display = best_app.get_status_display()
                             company_name = best_app.drive.company_name if best_app.drive.company_name else best_app.drive.title
                             
                             if best_app.status == 'placed':
                                 placement_message = f"Congratulations! You are Placed in {company_name}!"
                             elif best_app.status == 'selected':
                                 placement_message = f"Congratulations! You are Selected for {company_name}!"
                             else:
                                 placement_message = f"Congratulations! You have cleared {status_display} for {company_name}!"
                                  
                except Exception as e:
                    print(f"Error fetching student record for dashboard: {e}")
            
            context = {
                'user': user, 
                'user_type': user_type,
                'student_record': student_record,
                'dashboard_message': dashboard_message,
                'message_color': message_color,
                'placement_message': placement_message
            }
            return render(request, 'users/UserHome.html', context)
        except UserRegistration.DoesNotExist:
            messages.error(request, "Student not found.")
            return redirect('unified_login')
    # Check for Django authentication (built-in User model)
    elif request.user.is_authenticated and not request.user.is_staff:
        return render(request, 'users/UserHome.html', {'user': request.user})
    else:
        messages.error(request, "Please login first.")
        return redirect('unified_login')


def user_profile(request):
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please login first.")
        return redirect('users:user_login')

    # Fetch additional data based on user type
    student_data = None
    non_student_data = None
    
    if user.user_type == 'student':
        student_data = Student.objects.filter(userid=user.userid).first()
    else:
        non_student_data = NonStudent.objects.filter(userid=user.userid).first()
        
    context = {
        'user': user,
        'student_data': student_data,
        'non_student_data': non_student_data
    }
    
    return render(request, 'users/UserProfile.html', context)

def edit_user_profile(request):
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please login first.")
        return redirect('users:user_login')

    # Fetch additional data based on user type
    student_data = None
    non_student_data = None
    
    if user.user_type == 'student':
        student_data = Student.objects.filter(userid=user.userid).first()
    else:
        non_student_data = NonStudent.objects.filter(userid=user.userid).first()

    if request.method == 'POST':
        # Update UserRegistration data
        # Note: email and userid are read-only
        user.mobile = request.POST.get('mobile', user.mobile)
        user.gender = request.POST.get('gender', user.gender)
        dob = request.POST.get('dob', None)
        if dob:
            from datetime import datetime
            try:
                user.dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format")
        if 'pic' in request.FILES:
            user.pic = request.FILES['pic']
        
        
        # Update Student/NonStudent specific data
        if user.user_type == 'student' and student_data:
            # Update student fields in Student model
            student_data.college_name = request.POST.get('college_name', student_data.college_name)
            student_data.year = request.POST.get('year', student_data.year)
            student_data.branch = request.POST.get('branch', student_data.branch)
            student_data.academic_marks = request.POST.get('academic_marks', student_data.academic_marks)
            student_data.backlog = request.POST.get('backlog', student_data.backlog)
            student_data.save()
            
            # Also update redundant fields in UserRegistration model to keep them in sync
            user.college_name = student_data.college_name
            user.year = student_data.year
            user.branch = student_data.branch
            user.academic_marks = student_data.academic_marks
            user.backlog = student_data.backlog

            # Sync to PlacementCellStudent
            try:
                placement_cell_student = PlacementCellStudent.objects.get(student_id=user.student_id)
                placement_cell_student.marks_percentage = student_data.academic_marks
                placement_cell_student.backlog = student_data.backlog
                placement_cell_student.year = student_data.year
                placement_cell_student.save()
            except PlacementCellStudent.DoesNotExist:
                pass
            
        elif user.user_type == 'non_student' and non_student_data:
            non_student_data.profession = request.POST.get('profession', non_student_data.profession)
            non_student_data.company = request.POST.get('company', non_student_data.company)
            non_student_data.experience_years = request.POST.get('experience_years', non_student_data.experience_years)
            non_student_data.save()
        
        user.save()
            
        messages.success(request, "Profile updated successfully!")
        return redirect('users:UserProfile')

    context = {
        'user': user,
        'student_data': student_data,
        'non_student_data': non_student_data
    }
    return render(request, 'users/EditUserProfile.html', context)








def user_documents(request):
    from users.utils import get_user_registration
    user_obj = get_user_registration(request)
    
    if not user_obj:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')

    docs = Document.objects.all()
    
    # Get selected document ID from URL parameter
    selected_doc_id = request.GET.get('selected', None)
    print(f"UserDocuments view - selected_doc_id from URL: {selected_doc_id}")
    
    return render(request, 'users/UserDocuments.html', {
        'docs': docs, 
        'user': user_obj,
        'selected_doc_id': selected_doc_id
    })

def user_view_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    master_seed_b64 = request.GET.get("key", "")
    view_url = (
        request.build_absolute_uri(
            reverse('UserViewDocument', kwargs={'doc_id': document.id})
        ) + f"?key={master_seed_b64}"
    )
    return HttpResponse(f"Document view URL: {view_url}")






import os, time
from base64 import urlsafe_b64decode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import json

# Import Google OAuth functions
from .google_auth import google_login_redirect, google_callback, google_complete_registration, google_register_redirect

def UserCanViewDocusActions(request):
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')

    # Redirect to UserDocuments since UserViewDocs was removed
    return redirect('UserDocuments')


from Careerlytics.models import PlacementActivity, DriveApplication, PlacementCellStudent, ReadinessTest, ReadinessTestResult

def campus_drives(request):
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')
    
    # Verify user is a student
    if user.user_type != 'student':
        messages.warning(request, "Campus drives are only available for students.")
        return redirect('users:UserHome')
        
    # Find the placement cell student record
    try:
        student_record = PlacementCellStudent.objects.filter(email=user.email, is_active=True).first()
        if not student_record:
            # Try matching by student_id if email fails
            if user.student_id:
                student_record = PlacementCellStudent.objects.filter(student_id=user.student_id, is_active=True).first()
    except Exception as e:
        print(f"Error finding student record: {e}")
        student_record = None
        
    if not student_record:
        # If no placement cell record found, show empty state
        context = {
            'user': user,
            'drives': [],
            'exams': [],
            'applications': [],
            'test_results': [],
            'placement_cell': None
        }
        return render(request, 'users/campus_drives.html', context)
        
    placement_cell = student_record.placement_cell
    
    # Fetch Drives
    drives = list(PlacementActivity.objects.filter(
        placement_cell=placement_cell, 
        activity_type='drive'
    ).order_by('-date'))
    
    # Debug: Print drives to console
    print(f"DEBUG: Found {len(drives)} drives for user {userid}")
    for drive in drives:
        print(f"DEBUG: Drive - {drive.title} (ID: {drive.id})")
    
    # Fetch Readiness Tests
    readiness_test = ReadinessTest.objects.first()
    exams = []
    if readiness_test:
        # Create a mock exam object for template compatibility
        exams = [{
            'id': readiness_test.id,
            'title': 'Student Readiness Assessment',
            'description': 'Comprehensive assessment of aptitude, reasoning, English, and core subjects',
            'exam_duration': 60,
            'date': readiness_test.updated_at,
            'status': readiness_test.status,
            'result': None
        }]
    
    # Check if student already took the test
    existing_result = ReadinessTestResult.objects.filter(student=user).first()
    if existing_result and exams:
        exams[0]['result'] = existing_result
    
    # Debug: Print to console
    print(f"DEBUG: Found {len(exams)} readiness tests for user {userid}")
    for exam in exams:
        print(f"DEBUG: Exam - {exam['title']} (ID: {exam['id']})")
    
    # Fetch User's Applications and Results
    applications = DriveApplication.objects.filter(student=user)
    application_map = {app.drive_id: app.status for app in applications}
    
    # Attach status/results to objects
    for drive in drives:
        drive.application_status = application_map.get(drive.id)
    
    # Result is already attached to exam object above
    
    context = {
        'user': user,
        'drives': drives,
        'exams': exams,
        'placement_cell': placement_cell,
        'student_record': student_record
    }
    
    return render(request, 'users/campus_drives.html', context)

def apply_drive(request, drive_id):
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please log in to apply.")
        return redirect('users:user_login')
    
    drive = get_object_or_404(PlacementActivity, id=drive_id, activity_type='drive')
    
    # Check if already applied
    if DriveApplication.objects.filter(student=user, drive=drive).exists():
        messages.warning(request, "You have already applied for this drive.")
        return redirect('users:campus_drives')
    
    from .forms import DriveApplicationForm
    form = DriveApplicationForm()
    
    if request.method == 'POST':
        form = DriveApplicationForm(request.POST)
        if form.is_valid():
            # Create application with form data
            application = form.save(commit=False)
            application.student = user
            application.drive = drive
            application.status = 'applied'
            
            # Also populate the tracking fields from the form data
            application.student_cgpa = form.cleaned_data['percentage_cgpa']
            application.student_department = form.cleaned_data['branch']
            application.student_year = int(user.year) if user.year and (isinstance(user.year, int) or (isinstance(user.year, str) and user.year.isdigit())) else 1
            
            application.save()
            
            # Update drive participant count
            drive.current_applicants += 1
            drive.save()
            
            messages.success(request, f"Successfully applied for {drive.company_name}! Your details have been sent to the placement dashboard.")
            # Don't redirect, stay on the page to show success message
            form = DriveApplicationForm() # Reset form
            context = {
                'form': form,
                'drive': drive,
                'user': user,
                'applied_successfully': True
            }
            return render(request, 'users/apply_drive.html', context)
    
    context = {
        'form': form,
        'drive': drive,
        'user': user
    }
    return render(request, 'users/apply_drive.html', context)

def take_readiness_test(request, test_id):
    """Render readiness test interface using existing HTML in radinesstest folder"""
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')
    
    # Check if student already took the test
    existing_result = ReadinessTestResult.objects.filter(student=user).first()
    if existing_result:
        # Redirect to results page with a message
        messages.info(request, "You have already completed the Readiness Test. You can view your results below.")
        return redirect('users:my_test_results')
    
    # Check if test is enabled
    test = get_object_or_404(ReadinessTest, id=test_id)
    if test.status != 'enabled':
        messages.warning(request, "The Readiness Test is currently deactivated by the administrator. Please check back later.")
        return redirect('users:campus_drives')
    
    # Load questions
    all_questions = load_readiness_test_questions()
    
    # Select specific number of questions from each category
    selected_questions = []
    
    # Aptitude: 9
    for q in all_questions['aptitude'][:9]:
        q['category'] = 'aptitude'
        selected_questions.append(q)
        
    # Reasoning: 9
    for q in all_questions['reasoning'][:9]:
        q['category'] = 'reasoning'
        selected_questions.append(q)
        
    # English: 6
    for q in all_questions['english'][:6]:
        q['category'] = 'english'
        selected_questions.append(q)
        
    # Core: 36
    for q in all_questions['core'][:36]:
        q['category'] = 'core'
        selected_questions.append(q)
        
    # Add title and name to test object for template compatibility
    test.name = "Student Readiness Assessment"
    
    import json
    context = {
        'test': test,
        'questions_json': json.dumps(selected_questions),
        'total_questions': len(selected_questions),
        'time_limit': 60, # Standard 60 minutes
    }
    return render(request, 'users/readytest.html', context)

@require_http_methods(["POST"])
def submit_readiness_test(request, test_id):
    """Submit readiness test answers, compute category scores, classification, and persist results"""
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        return JsonResponse({'success': False, 'message': 'Please log in first'})
    
    test = get_object_or_404(ReadinessTest, id=test_id)
    
    # Prevent duplicate submissions
    if ReadinessTestResult.objects.filter(student=user, test=test).exists():
        return JsonResponse({'success': False, 'message': 'Test already submitted'})
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = request.POST.dict()
    
    # Expected payload: {'answers': [{'category': 'aptitude', 'is_correct': true, ...}, ...]}
    answers = payload.get('answers', [])
    
    categories = {'aptitude': {'total': 0, 'correct': 0},
                  'reasoning': {'total': 0, 'correct': 0},
                  'english': {'total': 0, 'correct': 0},
                  'core': {'total': 0, 'correct': 0}}
    submission_answers = []
    for ans in answers:
        cat = ans.get('category')
        is_correct = bool(ans.get('is_correct'))
        if cat in categories:
            categories[cat]['total'] += 1
            if is_correct:
                categories[cat]['correct'] += 1
        
        submission_answers.append({
            'question_text': ans.get('question_text', ''),
            'options': ans.get('options', []),
            'category': ans.get('category', ''),
            'selected_index': ans.get('selected_index'),
            'correct_index': ans.get('correct_index'),
            'is_correct': is_correct
        })

    total_questions = len(answers) if answers else 60
    correct_answers = sum(v['correct'] for v in categories.values())
    score_percentage = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0.0
    
    # Load thresholds from filesystem config; fallback to defaults
    ready_thr = 70.0
    needs_thr = 40.0
    try:
        config_path = os.path.join(settings.BASE_DIR, 'radinesstest', 'config', f'{test.id}.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as cf:
                rules = json.load(cf)
                ready_thr = float(rules.get('placement_ready_threshold', ready_thr))
                needs_thr = float(rules.get('needs_improvement_threshold', needs_thr))
    except Exception:
        pass
    
    if score_percentage >= ready_thr:
        classification = 'placement_ready'
    elif score_percentage >= needs_thr:
        classification = 'needs_improvement'
    else:
        classification = 'at_risk'
    
    # Persist DB record using ReadinessTestResult model
    time_taken = payload.get('time_taken', 60)
    result = ReadinessTestResult.objects.create(
        test=test,
        student=user,
        percentage=score_percentage,
        total_correct=correct_answers,
        total_questions=total_questions,
        classification=classification,
        aptitude_score=categories['aptitude']['correct'],
        reasoning_score=categories['reasoning']['correct'],
        english_score=categories['english']['correct'],
        core_score=categories['core']['correct'],
        started_at=timezone.now() - timezone.timedelta(minutes=time_taken),
        completed_at=timezone.now(),
        time_taken=time_taken,
        answers=submission_answers
    )
    
    # Also save to filesystem for compatibility/legacy reasons
    result_data = {
        'student_id': user.userid,
        'test_id': test.id,
        'score_percentage': score_percentage,
        'classification': classification,
        'categories': {
            'aptitude': {'total': 9, 'correct': categories['aptitude']['correct'], 'percentage': round((categories['aptitude']['correct']/9)*100, 2) if categories['aptitude']['total'] > 0 else 0},
            'reasoning': {'total': 9, 'correct': categories['reasoning']['correct'], 'percentage': round((categories['reasoning']['correct']/9)*100, 2) if categories['reasoning']['total'] > 0 else 0},
            'english': {'total': 6, 'correct': categories['english']['correct'], 'percentage': round((categories['english']['correct']/6)*100, 2) if categories['english']['total'] > 0 else 0},
            'core': {'total': 36, 'correct': categories['core']['correct'], 'percentage': round((categories['core']['correct']/36)*100, 2) if categories['core']['total'] > 0 else 0}
        },
        'completed_at': timezone.now().isoformat()
    }
    
    result_dir = os.path.join(settings.BASE_DIR, 'radinesstest', 'results')
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    result_path = os.path.join(result_dir, f'{user.userid}_{test.id}.json')
    with open(result_path, 'w', encoding='utf-8') as rf:
        rf.write(json.dumps(result_data, indent=2))
    
    return JsonResponse({'success': True, 'result_url': reverse('users:my_test_results')})

def my_drive_applications(request):
    return HttpResponse("My Drive Applications Placeholder")


def ai_interviewer(request):
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')
        
    eleven_voice_id = os.environ.get('ELEVENLABS_VOICE_ID', os.environ.get('ELEVEN_VOICE_ID', ''))
    return render(request, 'users/aiinterviewer.html', {'user': user, 'eleven_voice_id': eleven_voice_id})

@csrf_exempt
@require_http_methods(["POST"])
def ai_interview_generate_question(request):
    try:
        data = json.loads(request.body)
        role = data.get('role', '')
        experience = data.get('experience', 0)
        jd = data.get('jd', '')
        history = data.get('history', [])
        phase = data.get('phase', 'behavior')
        session_id = data.get('sessionId')
        prompt = (
            "You are an AI interviewer. Generate one interview question. "
            "For the first 5 minutes ask behavior questions. For the next 25 minutes ask technical questions. "
            "Consider role, years of experience, and job description. "
            "Do not include explanations. Return only the question text."
        )
        context = f"Role: {role}\nExperience: {experience} years\nJob Description: {jd}\nPhase: {phase}\nHistory: {history}"
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt + "\n" + context}]}
            ]
        }
        api_key = os.environ.get('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        q = ""
        try:
            if api_key:
                r = requests.post(url, params={"key": api_key}, json=body, timeout=30)
                j = r.json()
                q = j.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "") or ""
        except Exception:
            q = ""
        # Fallback to local curated questions if LLM failed or no key
        if not q.strip():
            try:
                questions_path = os.path.join(settings.BASE_DIR, 'aimockagent', 'questions.json')
                with open(questions_path, 'r', encoding='utf-8') as f:
                    bank = json.load(f)
                if phase == 'behavior':
                    cats = {'behavior', 'communication', 'role_fit'}
                else:
                    cats = {'technical', 'problem_solving', 'role_fit'}
                pool = [item for item in bank if item.get('category') in cats]
                if not pool:
                    q = "Tell me about your most impactful recent project."
                else:
                    q = random.choice(pool).get('question', "Describe a recent challenge and how you addressed it.")
            except Exception:
                q = "Describe a recent challenge and how you addressed it."
        return HttpResponse(json.dumps({"question": q}), content_type="application/json")
    except Exception:
        return HttpResponse(json.dumps({"question": "Please introduce yourself."}), content_type="application/json", status=200)

@csrf_exempt
@require_http_methods(["POST"])
def ai_interview_tts(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        api_key = os.environ.get('ELEVENLABS_API_KEY', '')
        voice_id = data.get('voice_id') or os.environ.get('ELEVENLABS_VOICE_ID', os.environ.get('ELEVEN_VOICE_ID', ''))
        if not api_key or not voice_id:
            return HttpResponse(json.dumps({"data_url": None, "error": "missing_api_or_voice"}), content_type="application/json")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        ct = r.headers.get('Content-Type', '')
        if r.status_code == 200 and r.content and ('audio' in ct.lower() or ct.lower() == 'application/octet-stream'):
            b64 = base64.b64encode(r.content).decode('utf-8')
            return HttpResponse(json.dumps({"data_url": "data:audio/mpeg;base64," + b64, "voice": voice_id}), content_type="application/json")
        try:
            err = r.json()
        except Exception:
            err = {"status_code": r.status_code, "content_type": ct}
        return HttpResponse(json.dumps({"data_url": None, "error": err}), content_type="application/json")
    except Exception:
        return HttpResponse(json.dumps({"data_url": None, "error": "exception"}), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def ai_interview_evaluate(request):
    try:
        data = json.loads(request.body)
        role = data.get('role', '')
        experience = data.get('experience', 0)
        jd = data.get('jd', '')
        history = data.get('history', [])
        prompt = (
            "Evaluate the interview answers and return strict JSON with keys: "
            "communication, behavior, technical, problem_solving, role_fit, summary. "
            "Scores should be 0-100 integers."
        )
        context = {"role": role, "experience": experience, "job_description": jd, "history": history}
        body = {"contents": [{"role": "user", "parts": [{"text": prompt + "\n" + json.dumps(context)}]}]}
        api_key = os.environ.get('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        r = requests.post(url, params={"key": api_key}, json=body, timeout=60)
        j = {}
        try:
            out = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            j = json.loads(out)
        except Exception:
            j = {"communication": 70, "behavior": 70, "technical": 70, "problem_solving": 70, "role_fit": 70, "summary": "Baseline evaluation."}
        comm = int(j.get("communication", 0))
        beh = int(j.get("behavior", 0))
        tech = int(j.get("technical", 0))
        prob = int(j.get("problem_solving", 0))
        fit = int(j.get("role_fit", 0))
        final_score = round(comm*0.15 + beh*0.30 + tech*0.30 + prob*0.15 + fit*0.10, 2)
        j["final_score"] = final_score
        return HttpResponse(json.dumps(j), content_type="application/json")
    except Exception:
        return HttpResponse(json.dumps({"communication": 0, "behavior": 0, "technical": 0, "problem_solving": 0, "role_fit": 0, "final_score": 0, "summary": ""}), content_type="application/json")

@csrf_exempt
@require_http_methods(["GET"])
def ai_interview_ping(request):
    return HttpResponse(json.dumps({"ok": True}), content_type="application/json")

@csrf_exempt
@require_http_methods(["POST"])
def maya_chat(request):
    try:
        data = json.loads(request.body)
        user_text = data.get('message', '').strip()
        if not user_text:
            return HttpResponse(json.dumps({"reply": "Please type your question."}), content_type="application/json")
        api_key = os.environ.get('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))
        system_prompt = (
            "You are Maya, a curious girl. Speak simply like explaining to a 12-year-old, "
            "with short, clear explanations and small examples. Be friendly and concise. "
            "If the question is about code or flows in Careerlytics, reference common pages like UserHome, Campus Drives, Readiness Tests, Placement Drives, or Admin Dashboard and describe them simply."
        )
        if not api_key:
            return HttpResponse(json.dumps({"reply": "Please configure Gemini API to chat with Maya."}), content_type="application/json")
        client = genai.Client(api_key=api_key)
        txt = ""
        try:
            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[{"role":"user","parts":[{"text": user_text}]}],
                system_instruction={"role":"system","parts":[{"text": system_prompt}]},
                generation_config={"temperature":0.7,"topP":0.95}
            )
            txt = getattr(resp, "output_text", "") or getattr(resp, "text", "")
            if not txt:
                cands = getattr(resp, "candidates", None)
                if cands:
                    parts = cands[0].get("content", {}).get("parts", [])
                    if parts and parts[0].get("text"):
                        txt = parts[0]["text"]
        except Exception:
            try:
                resp = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=[{"role":"user","parts":[{"text": user_text}]}],
                    system_instruction={"role":"system","parts":[{"text": system_prompt}]},
                    generation_config={"temperature":0.7,"topP":0.95}
                )
                txt = getattr(resp, "output_text", "") or getattr(resp, "text", "")
                if not txt:
                    cands = getattr(resp, "candidates", None)
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        if parts and parts[0].get("text"):
                            txt = parts[0]["text"]
            except Exception:
                txt = ""
        if not txt or not txt.strip():
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                body = {
                    "systemInstruction": {"role":"system","parts":[{"text": system_prompt}]},
                    "contents": [{"role":"user","parts":[{"text": user_text}]}],
                    "generationConfig": {"temperature":0.7,"topP":0.95}
                }
                r = requests.post(url, params={"key": api_key}, json=body, timeout=25)
                j = r.json()
                txt = j.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
            except Exception:
                txt = ""
        if not txt or not txt.strip():
            txt = "Here’s a quick, simple take: " + (user_text[:180] if user_text else "Ask something specific, and I’ll explain it clearly.")
        return HttpResponse(json.dumps({"reply": txt}), content_type="application/json")
    except Exception:
        return HttpResponse(json.dumps({"reply": "Let's think about this together!"}), content_type="application/json")
def reset_password(request):
    if request.method == 'POST':
        step = request.POST.get('step')
        
        if step == '1':
            userid = request.POST.get('userid', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Find user by User ID or Student ID, AND matching Email
            user = UserRegistration.objects.filter(
                (Q(userid=userid) | Q(student_id=userid)) & Q(email=email)
            ).first()
            
            if user:
                # User found, move to step 2
                return render(request, 'resetpassword.html', {'step': 2, 'user_pk': user.pk})
            else:
                messages.error(request, "User not found with provided ID and Email.")
                return render(request, 'resetpassword.html', {'step': 1})
                
        elif step == '2':
            user_pk = request.POST.get('user_pk')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'resetpassword.html', {'step': 2, 'user_pk': user_pk})
            
            try:
                user = UserRegistration.objects.get(pk=user_pk)
                
                # Update UserRegistration password
                user.password = new_password
                user.save()
                
                # Update subtype model password to keep in sync
                if user.user_type == 'student':
                    student = Student.objects.filter(userid=user.userid).first()
                    if student:
                        student.password = new_password
                        student.save()
                elif user.user_type == 'non_student':
                    non_student = NonStudent.objects.filter(userid=user.userid).first()
                    if non_student:
                        non_student.password = new_password
                        non_student.save()
                        
                messages.success(request, "Password reset successfully! Please login with your new password.")
                return redirect('users:user_login')
            except UserRegistration.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('users:reset_password')
                
    # GET request
    return render(request, 'resetpassword.html', {'step': 1})

def my_test_results(request):
    """View to display student's readiness test results"""
    if 'userid' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')
    
    userid = request.session['userid']
    user = get_object_or_404(UserRegistration, userid=userid)
    
    # Get the latest result
    result = ReadinessTestResult.objects.filter(student=user).order_by('-completed_at').first()
    
    if not result:
        messages.info(request, "You haven't taken any readiness tests yet.")
        return redirect('users:campus_drives')
    
    # Calculate percentage offset for the SVG radial progress (circumference is 552.92)
    # stroke-dashoffset = circumference - (percentage / 100) * circumference
    # We use a negative offset because the stroke-dashoffset subtraction in template
    percentage_val = result.percentage
    circumference = 552.92
    result.percentage_offset = -(percentage_val / 100) * circumference
    
    return render(request, 'users/readyresult.html', {'result': result, 'user': user})

def load_readiness_test_questions():
    """Load questions from JSON files in radinesstest directory"""
    import json
    import os
    
    from django.conf import settings
    
    questions = {
        'aptitude': [],
        'reasoning': [],
        'english': [],
        'core': []
    }
    
    base_path = os.path.join(settings.BASE_DIR, 'radinesstest', 'questions')
    
    # Load each category
    for category in questions.keys():
        file_path = os.path.join(base_path, f'{category}.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions[category] = data.get('questions', [])
            except Exception as e:
                print(f"Error loading {category} questions: {e}")
                questions[category] = []
    
    return questions

def readiness_test_view(request):
    """Main readiness test view for students"""
    if 'userid' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('users:user_login')
    
    userid = request.session['userid']
    user = get_object_or_404(UserRegistration, userid=userid)
    
    # Verify user is a student
    if user.user_type != 'student':
        messages.warning(request, "Readiness test is only available for students.")
        return redirect('users:UserHome')
    
    # Check if test is enabled
    current_test = ReadinessTest.objects.first()
    if not current_test or current_test.status != 'enabled':
        messages.warning(request, "The Readiness Test is currently deactivated by the administrator. Please check back later.")
        return redirect('users:campus_drives')
    
    # Check if student already took the test
    existing_result = ReadinessTestResult.objects.filter(student=user).first()
    if existing_result:
        # Redirect to results page with a message
        messages.info(request, "You have already completed the Readiness Test. You can view your results below.")
        return redirect('users:my_test_results')
    
    # Redirect to dynamic test interface
    return redirect('users:take_readiness_test', test_id=current_test.id)

# Remove the old duplicate submit_readiness_test(request) function as it's redundant
# with submit_readiness_test(request, test_id) used by the dynamic interface.




 


