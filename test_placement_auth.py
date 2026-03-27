import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from Careerlytics.models import PlacementCell
from users.models import AdminRegistration

def test_placement_cell_registration_and_login():
    client = Client()
    
    # Generate unique test data
    test_id = f"TEST_{uuid.uuid4().hex[:6].upper()}"
    test_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    test_password = "testpassword123"
    test_institution = "SCCE"
    
    print(f"--- Testing Registration with {test_email} ---")
    
    # 1. Test Registration
    reg_url = reverse('placement_cell_register')
    test_institution = f"Test Institution {uuid.uuid4().hex[:6]}"

    reg_data = {
        'username': test_id,
        'email': test_email,
        'institution_name': test_institution,
        'password': test_password,
        'confirm_password': test_password,
        'terms': 'on'
    }
    
    response = client.post(reg_url, reg_data, follow=True)
    
    # Check if registration was successful
    is_success = PlacementCell.objects.filter(email=test_email).exists()
    
    if is_success:
        print("SUCCESS: Registration successful and PlacementCell record created.")
        
        # Check if AdminRegistration was also created
        if AdminRegistration.objects.filter(username=test_email).exists():
            print("SUCCESS: AdminRegistration compatibility record created.")
        else:
            print("FAILED: AdminRegistration compatibility record NOT created.")
            return False
            
        # Check if session variables are set
        if client.session.get('admin_username') == test_email:
            print("SUCCESS: Session variables set correctly after registration.")
        else:
            print(f"FAILED: Session variables NOT set correctly. Got {client.session.get('admin_username')}")
            return False
    else:
        print(f"FAILED: Registration failed. Status code: {response.status_code}")
        # Print messages from session
        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        if messages:
            for msg in messages:
                print(f"Message: {msg}")
        elif response.context and 'messages' in response.context:
            for msg in response.context['messages']:
                print(f"Message: {msg}")
        return False

    # 2. Test Login
    print(f"\n--- Testing Login with {test_id} ---")
    client.logout() # Clear session
    
    login_url = reverse('placement_cell_login')
    login_data = {
        'username': test_id,
        'password': test_password
    }
    
    response = client.post(login_url, login_data, follow=True)
    
    if response.status_code == 200 and response.resolver_match.url_name == 'AdminHome':
        print("SUCCESS: Login successful using Placement Cell ID.")
        
        # Check if session variables are set after login
        if client.session.get('admin_username') == test_email:
            print("SUCCESS: Session variables set correctly after login.")
        else:
            print(f"FAILED: Session variables NOT set correctly after login. Got {client.session.get('admin_username')}")
            return False
    else:
        print(f"FAILED: Login failed. Status code: {response.status_code}")
        if response.resolver_match:
             print(f"Redirected to: {response.resolver_match.url_name}")
        return False

    print("\n--- Testing Login with Email ---")
    client.logout()
    
    login_data = {
        'username': test_email,
        'password': test_password
    }
    
    response = client.post(login_url, login_data, follow=True)
    
    if response.status_code == 200 and response.resolver_match.url_name == 'AdminHome':
        print("SUCCESS: Login successful using Email.")
    else:
        print(f"FAILED: Login failed using Email.")
        return False

    print("\nALL TESTS PASSED!")
    return True

if __name__ == "__main__":
    try:
        test_placement_cell_registration_and_login()
    except Exception as e:
        print(f"An error occurred during testing: {e}")
        import traceback
        traceback.print_exc()
