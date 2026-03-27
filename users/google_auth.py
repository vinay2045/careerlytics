from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import login
from django.contrib import messages
from urllib.parse import urlencode
import requests
import json
from .models import UserRegistration
import secrets
import io
import base64
import re
import os
from datetime import datetime

def google_login_redirect(request):
    """Redirect user to Google OAuth 2.0 consent screen"""
    # Google OAuth 2.0 configuration
    client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
    redirect_uri = settings.GOOGLE_OAUTH2_REDIRECT_URI
    
    # Build the authorization URL
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'include_granted_scopes': 'true',
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return redirect(auth_url)

def google_callback(request):
    """Handle Google OAuth 2.0 callback"""
    # Get authorization code from Google
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'Google authentication error: {error}')
        return redirect('user_login')
    
    if not code:
        messages.error(request, 'No authorization code received from Google')
        return redirect('user_login')
    
    try:
        # Exchange authorization code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        # Get user info from Google
        access_token = token_data['access_token']
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()
        
        # Check if user exists in database
        email = user_info['email']
        try:
            user = UserRegistration.objects.get(email=email)
            
            # User exists, log them in
            request.session['userid'] = user.userid
            request.session['email'] = user.email
            request.session['username'] = user.userid
            request.session['totp_secret'] = user.totp_secret
            
            messages.success(request, f'Welcome back {user.userid}!')
            return redirect('UserHome')
            
        except UserRegistration.DoesNotExist:
            # User doesn't exist, redirect to registration with Google data
            request.session['google_data'] = {
                'email': email,
                'name': user_info.get('name', ''),
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'picture': user_info.get('picture', ''),
            }
            
            messages.info(request, 'Please complete your registration to continue')
            return redirect('google_complete_registration')
            
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error communicating with Google: {str(e)}')
        return redirect('user_login')
    except Exception as e:
        messages.error(request, f'Error during Google authentication: {str(e)}')
        return redirect('user_login')

def google_complete_registration(request):
    """Show registration form pre-filled with Google data"""
    google_data = request.session.get('google_data')
    
    if not google_data:
        messages.error(request, 'Google session data not found')
        return redirect('user_register')
    
    if request.method == 'POST':
        try:
            # Get form data
            userid = request.POST.get('userid')
            password = request.POST.get('password')
            email = google_data['email']
            country_code = request.POST.get('country_code', '+91')  # Default to India if not selected
            mobile_number = request.POST.get('mobile')
            mobile = country_code + mobile_number if mobile_number else ''
            address = request.POST.get('address')
            dob = request.POST.get('dob')
            gender = request.POST.get('gender')
            pic = request.FILES.get('pic')
            
            # Validate required fields
            if not all([userid, password, mobile_number, address, dob, gender]):
                messages.error(request, "All fields are required!")
                return render(request, 'users/google_complete_registration.html', {'google_data': google_data})
            
            # Validate mobile number (should be exactly 10 digits)
            if len(mobile_number) != 10 or not mobile_number.isdigit():
                messages.error(request, "Mobile number must be exactly 10 digits!")
                return render(request, 'users/google_complete_registration.html', {'google_data': google_data})
            
            # Parse date of birth
            dob_parsed = datetime.strptime(dob, '%Y-%m-%d').date()
            
            # Create user
            new_user = UserRegistration(
                userid=userid,
                password=password,
                email=email,
                mobile=mobile,
                address=address,
                dob=dob_parsed,
                gender=gender,
                pic=pic,
                status='Activated'  # Auto-activate Google users
            )
            new_user.save()
            
            # Link to placement cell
            try:
                from .utils import link_student_to_placement_cell
                link_success, link_msg = link_student_to_placement_cell(new_user)
                if link_success:
                    print(f"Successfully linked {new_user.userid} to placement cell: {link_msg}")
                else:
                    print(f"Failed to link {new_user.userid} to placement cell: {link_msg}")
            except Exception as e:
                print(f"Error linking student to placement cell: {e}")
            
            # Log user in
            request.session['userid'] = new_user.userid
            request.session['email'] = new_user.email
            request.session['username'] = new_user.userid
            
            # Clear Google session data
            del request.session['google_data']
            
            messages.success(request, f'Account created successfully! Welcome {new_user.userid}!')
            return redirect('UserHome')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'users/google_complete_registration.html', {'google_data': google_data})
    
    return render(request, 'users/google_complete_registration.html', {'google_data': google_data})

def google_register_redirect(request):
    """Redirect to Google OAuth for registration"""
    return google_login_redirect(request)
