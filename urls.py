from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from users import views_resume

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home page - Redirect to login
    path('', views.unified_login_view, name='home'),
    
    # Unified login system
    path('login/', views.unified_login_view, name='unified_login'),
    path('user/login/', views.user_login_view, name='user_login'),
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard pages
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # API endpoints
    path('api/login/', views.api_login, name='api_login'),
    
    # Registration pages
    path('register/', views.register_view, name='register'),
    path('user/register/', views.user_register_view, name='user_register'),
    path('admin/register/', views.admin_register_view, name='admin_register'),
    
    # Include users app URLs with prefix
    path('UserHome/', include(('users.urls', 'users'))),
    
    # Direct resume upload URLs (without UserHome prefix)
    path('my-resumes/', views_resume.my_resumes, name='my_resumes'),
    path('download-resume/<uuid:resume_id>/', views_resume.download_resume, name='download_resume'),
    path('delete-resume/<uuid:resume_id>/', views_resume.delete_resume, name='delete_resume'),
    
    # Include Careerlytics app URLs with prefix
    path('Careerlytics/', include('Careerlytics.urls')),
    
    # Include personalizedplan app URLs with prefix
    path('personalizedplan/', include('personalizedplan.urls')),
    
    # Include resumeanalysis app URLs without prefix
    path('', include(('resumeanalysis.urls', 'resumeanalysis')))
    
    # Include other app URLs if needed
    # path('api/', include('api.urls')),
    
    # Serve mock test data files
    path('mocktestdata/pythonquestions.txt', views_python_test.serve_python_questions, name='serve_python_questions'),
]
