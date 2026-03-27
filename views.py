from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
import json

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
                return render(request, 'login.html')
            
            if user_type == 'user' and user.is_staff:
                messages.error(request, 'Admin users cannot login as regular users.')
                return render(request, 'login.html')
            
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
                return redirect('admin_dashboard')  # You'll need to create this URL
            else:
                messages.success(request, 'Welcome back to Careerlytics!')
                return redirect('users:UserHome')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'login.html')

def user_login_view(request):
    """
    Legacy user login view - redirects to unified login
    """
    return redirect('unified_login')

def admin_login_view(request):
    """
    Legacy admin login view - redirects to unified login
    """
    return redirect('unified_login')

@require_http_methods(["POST"])
@csrf_protect
def logout_view(request):
    """
    Logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('unified_login')

def admin_dashboard_view(request):
    """
    Admin dashboard view
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('unified_login')
    
    context = {
        'user': request.user,
        'page_title': 'Admin Dashboard'
    }
    return render(request, 'admin_dashboard.html', context)

@require_http_methods(["POST"])
@csrf_protect
def api_login(request):
    """
    API endpoint for login (for AJAX requests)
    """
    try:
        data = json.loads(request.body)
        user_type = data.get('user_type', 'user')
        email = data.get('email')
        password = data.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check user type
            if user_type == 'admin' and not user.is_staff:
                return HttpResponse(
                    json.dumps({'success': False, 'error': 'Admin privileges required'}),
                    content_type='application/json',
                    status=403
                )
            
            if user_type == 'user' and user.is_staff:
                return HttpResponse(
                    json.dumps({'success': False, 'error': 'Cannot login as regular user'}),
                    content_type='application/json',
                    status=403
                )
            
            login(request, user)
            
            return HttpResponse(
                json.dumps({
                    'success': True,
                    'redirect_url': '/admin/dashboard/' if user_type == 'admin' else '/UserHome/UserHome/'
                }),
                content_type='application/json'
            )
        else:
            return HttpResponse(
                json.dumps({'success': False, 'error': 'Invalid credentials'}),
                content_type='application/json',
                status=401
            )
    except Exception as e:
        return HttpResponse(
            json.dumps({'success': False, 'error': 'Server error'}),
            content_type='application/json',
            status=500
        )

def user_register_view(request):
    """
    User registration view
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Careerlytics.')
            return redirect('users:UserHome')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form, 'user_type': 'user'})

def admin_register_view(request):
    """
    Admin registration view (restricted)
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            messages.success(request, 'Admin registration successful! Welcome to Careerlytics Admin.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Admin registration failed. Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form, 'user_type': 'admin'})
