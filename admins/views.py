from django.shortcuts import render,HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os, secrets
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from users.models import Document, UserRegistration, AdminRegistration
import time
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
import datetime
from collections import deque
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from cachetools import TTLCache
from Careerlytics.models import PlacementActivity, PlacementCell

def AdminLogin(request): os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from django.core.mail import send_mail
from base64 import urlsafe_b64encode

ALLOWED_EXT = ['.pdf', '.doc', '.docx', '.txt']

# --- Admin dashboard runtime event stream (in-memory) ---
_DASHBOARD_START = timezone.now()
_EVENT_SEQ = 0
_EVENTS = deque(maxlen=200)


def _push_event(level: str, message: str):
    """Store a lightweight dashboard event for the live console (in-memory)."""
    global _EVENT_SEQ
    _EVENT_SEQ += 1
    _EVENTS.append({
        "id": _EVENT_SEQ,
        "ts": timezone.now().isoformat(timespec="seconds"),
        "level": level,  # REQUEST | PENDING | SUCCESS | DENIED
        "message": message,
    })



def AdminRegister(request):
    return render(request, 'AdminRegister.html')

def AdminRegisterAction(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        institution_name = request.POST.get('institution_name')
        mobile = request.POST.get('mobile', '')
        address = request.POST.get('address', '')

        if not username or not password or not email or not institution_name:
            messages.error(request, "All required fields must be filled.")
            return redirect('AdminRegister')

        # Check if username already exists
        if AdminRegistration.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('AdminRegister')

        # Check if email already exists
        if AdminRegistration.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('AdminRegister')

        # Create new placement cell account
        try:
            # Also create Django user for authentication
            from django.contrib.auth.models import User
            django_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True  # Mark as admin/staff
            )
            
            # Create custom registration record
            admin_reg = AdminRegistration.objects.create(
                username=username,
                password=password,
                email=email,
                institution_name=institution_name,
                mobile=mobile,
                address=address,
                status='Activated'
            )
            
            messages.success(request, "Placement Cell account created successfully! You can now login.")
            return redirect('placement_cell')
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect('AdminRegister')

    return render(request, 'AdminRegister.html')


def AdminLogin(request):
    return render(request, 'admins/AdminLogin.html')

def AdminLoginAction(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Try Django authentication first (primary method)
            from django.contrib.auth import authenticate, login
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Try custom AdminRegistration model as fallback
                admin = AdminRegistration.objects.get(username=username, password=password)
                request.session['admin_username'] = admin.username
                request.session['admin_email'] = admin.email
                request.session['admin_institution'] = admin.institution_name
                messages.success(request, f"Welcome {admin.username} from {admin.institution_name}!")
                _push_event("SUCCESS", f"Placement Cell logged in: {admin.username}")
                return redirect('AdminHome')
            
            # Django user found - check if staff
            if user.is_staff:
                # Get additional admin info from custom model
                try:
                    admin_info = AdminRegistration.objects.get(username=username)
                    request.session['admin_username'] = admin_info.username
                    request.session['admin_email'] = admin_info.email
                    request.session['admin_institution'] = admin_info.institution_name
                except AdminRegistration.DoesNotExist:
                    # Create admin info if doesn't exist
                    admin_info = AdminRegistration.objects.create(
                        username=username,
                        password=password,  # Store for fallback
                        email=user.email,
                        institution_name="Default Institution"
                    )
                    request.session['admin_username'] = admin_info.username
                    request.session['admin_email'] = admin_info.email
                    request.session['admin_institution'] = admin_info.institution_name
                
                # Login Django user
                login(request, user)
                messages.success(request, f"Welcome {user.username}!")
                _push_event("SUCCESS", f"Placement Cell logged in: {user.username}")
                return redirect('AdminHome')
            else:
                # Regular user trying to access Placement Cell login
                messages.error(request, "You don't have Placement Cell privileges.")
                _push_event("DENIED", f"Non-Placement Cell user attempted login: {user.username}")
                return redirect('unified_login')
                
        except AdminRegistration.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            return redirect('unified_login')
        except Exception as e:
            messages.error(request, f"Login failed: {str(e)}")
            return redirect('unified_login')

    return render(request, 'AdminLogin.html')


def AdminHome(request):
    # Check for Django authentication first
    if request.user.is_authenticated and request.user.is_staff:
        # Get additional admin info from custom model
        try:
            admin_info = AdminRegistration.objects.get(username=request.user.username)
            context = {
                'admin': request.user.username,
                'email': admin_info.email,
                'institution': admin_info.institution_name,
                'mobile': admin_info.mobile,
                'address': admin_info.address
            }
        except AdminRegistration.DoesNotExist:
            context = {
                'admin': request.user.username,
                'email': request.user.email,
                'institution': 'Default Institution',
                'mobile': '',
                'address': ''
            }
            
        # Add placement stats
        try:
            placement_cell = PlacementCell.objects.filter(user=request.user).first()
            if placement_cell:
                context['active_drives_count'] = PlacementActivity.objects.filter(
                    placement_cell=placement_cell,
                    activity_type='drive',
                    status__in=['upcoming', 'ongoing']
                ).count()
                context['readiness_tests_count'] = PlacementActivity.objects.filter(
                    placement_cell=placement_cell,
                    activity_type='readiness_test'
                ).count()
            else:
                context['active_drives_count'] = 0
                context['readiness_tests_count'] = 0
        except Exception as e:
            print(f"Error fetching stats: {e}")
            context['active_drives_count'] = 0
            context['readiness_tests_count'] = 0

        return render(request, 'admins/AdminHome.html', context)
    # Check for custom session authentication as fallback
    elif 'admin_username' in request.session:
        admin_info = AdminRegistration.objects.get(username=request.session['admin_username'])
        context = {
            'admin': request.session['admin_username'],
            'email': request.session.get('admin_email', admin_info.email),
            'institution': request.session.get('admin_institution', admin_info.institution_name),
            'mobile': admin_info.mobile,
            'address': admin_info.address
        }
        return render(request, 'admins/AdminHome.html', context)
    else:
        return redirect('unified_login')


def AdminLogout(request):
    # Handle Django authentication logout
    if request.user.is_authenticated:
        from django.contrib.auth import logout
        logout(request)
    
    # Handle custom session logout
    session_keys = ['admin_username', 'admin_email', 'admin_institution', 'admin']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    messages.success(request, "Placement Cell logged out successfully!")
    return redirect('index')




def is_allowed_filename(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXT











def send_emaill(sender_email, sender_password, recipient_email, subject, body, attachment_path=None):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    
    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(attachment_path)}'
        )
        message.attach(part)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())



# -------------------- Admin Dashboard APIs --------------------
def admin_dashboard_metrics(request):
    if 'admin_username' not in request.session:
        return JsonResponse({"error": "unauthorized"}, status=401)
    
    personnel_authorized = UserRegistration.objects.filter(status='Activated').count()
    
    uptime_hours = round((timezone.now() - _DASHBOARD_START).total_seconds() / 3600.0, 2)
    
    pending_users = UserRegistration.objects.filter(status='Not Activated').count()
    
    return JsonResponse({
        "personnel_authorized": personnel_authorized,
        "node_integrity": 99.9,
        "uptime_hours": uptime_hours,
        "pending_users": pending_users,
        "pending_key_requests": 0,  # No key requests to show
    })


def admin_dashboard_keyflow(request):
    if 'admin' not in request.session:
        return JsonResponse({"error": "unauthorized"}, status=401)
    
    days = 7
    today = timezone.localdate()
    start = today - datetime.timedelta(days=days - 1)
    
    # Simplified dashboard without DocumentKeyRequest references
    labels = []
    data = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        labels.append(d.strftime("%a"))
        data.append(0)  # No key requests to show
    
    return JsonResponse({"labels": labels, "data": data})




def user_view_document(request, doc_id):
    # This function has been removed as part of performance view cleanup
    return HttpResponse("Document viewing functionality has been removed.", status=404)

def send_emaill(sender_email, sender_password, recipient_email, subject, body, attachment_path=None):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    
    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(attachment_path)}'
        )
        message.attach(part)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
