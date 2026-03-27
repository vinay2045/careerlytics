"""OptimalKeyGeneration URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

# Import specific views for direct URL mapping
from resumeanalysis import views as resumeanalysis_views

from Careerlytics import views as mainview
from users import views as usr
from users import views_resume
from users import views_python_test
from users import views_mock_test
from admins import views as admins
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', mainview.index, name='index'),
    path('home', mainview.index, name='home'),
    
    # Unified login system
    path('login/', mainview.unified_login_view, name='unified_login'),
    path('user_login/', usr.UserLogin, name='user_login'),  # Direct mapping
    path('user_register/', mainview.UserRegister, name='user_register'),
    
    # ### Placement Cell App
    path('placement_cell/', mainview.placement_cell_view, name='placement_cell'),
    path('placement_cell/login/', mainview.placement_cell_login_action, name='placement_cell_login'),
    path('placement_cell/register/', mainview.placement_cell_register_action, name='placement_cell_register'),

    path('Logout/', mainview.Logout, name='Logout'),

    # Direct UserHome URL for backward compatibility
    path('UserHome/', usr.UserHome, name='UserHome_direct'),

    # ### User Based URLs - Include users app URLs with namespace
    path('', include('users.urls', namespace='users')),
    
    # Personalized Plan URLs
    path('personalized-plan/', include('personalizedplan.urls', namespace='personalizedplan')),
    
    # Resume Analysis URLs
    path('resumeanalysis/', include('resumeanalysis.urls', namespace='resumeanalysis')),
    
    # Simple resume upload URL
    path('upload/', resumeanalysis_views.upload_resume, name='upload'),

    # Google OAuth URLs
    path('auth/google/', usr.google_login_redirect, name='google_login'),
    path('auth/google/callback/', usr.google_callback, name='google_callback'),

    # ### Admin Based URLs
    path('AdminLoginAction/', admins.AdminLoginAction, name='AdminLoginAction'),
    path('AdminHome/', admins.AdminHome, name='AdminHome'),
    path('AdminLogout/', admins.AdminLogout, name='AdminLogout'), 
    
    # Student Classification Admin URLs
    path('readiness/', include('Careerlytics.admin_urls', namespace='readiness_admin')), 

    # ### Placement Drive Management URLs
    path('analysis/', mainview.admin_analysis, name='admin_analysis'),
    path('placement-drives/', mainview.admin_placement_drives, name='admin_placement_drives'),
    path('placement-drives/add/', mainview.admin_add_placement_drive, name='admin_add_placement_drive'),
    path('placement-drives/add-test/', mainview.admin_add_readiness_test, name='admin_add_readiness_test'),
    path('placement-drives/edit/<int:activity_id>/', mainview.admin_edit_activity, name='admin_edit_activity'),
    path('placement-drives/delete/<int:activity_id>/', mainview.admin_delete_activity, name='admin_delete_activity'),
    path('placement-drives/view/<int:activity_id>/', mainview.admin_view_activity, name='admin_view_activity'),
    path('placement-drives/applications/<int:drive_id>/', mainview.admin_drive_applications, name='admin_drive_applications'),
    path('placement-drives/opted-in/', mainview.admin_opted_in, name='admin_opted_in'),
    path('placement-drives/application-detail/<int:application_id>/', mainview.admin_application_detail, name='admin_application_detail'),
    path('placement-drives/update-status/<int:application_id>/', mainview.admin_update_application_status, name='admin_update_application_status'),
    path('placement-drives/outcome-registry/', mainview.outcome_registry, name='outcome_registry'),
    path('placement-drives/test-results/', mainview.admin_test_results, name='admin_test_results'),
    path('placement-drives/students/', mainview.admin_all_students, name='admin_all_students'),
    path('placement-drives/student/update/<int:student_id>/', mainview.admin_update_student, name='admin_update_student'),
    path('placement-drives/student/toggle/<int:student_id>/', mainview.admin_toggle_student_status, name='admin_toggle_student_status'),
    path('placement-drives/toggle-status/<int:activity_id>/', mainview.admin_toggle_activity_status, name='admin_toggle_activity_status'),
    path('placement-drives/test/update-thresholds/<int:activity_id>/', mainview.admin_update_readiness_thresholds, name='admin_update_readiness_thresholds'),
    path('placement-drives/test/reset/<int:test_id>/', mainview.admin_reset_readiness_test, name='admin_reset_readiness_test'),

    # ### Admin Dashboard APIs
    path('admin/dashboard/metrics/', admins.admin_dashboard_metrics, name='AdminDashboardMetrics'),
    path('admin/dashboard/keyflow/', admins.admin_dashboard_keyflow, name='AdminDashboardKeyflow'),

    path('UserViewDocument/<int:doc_id>/', admins.user_view_document, name='UserViewDocument'),

    # Resume upload URLs
    path('my-resumes/', views_resume.my_resumes, name='my_resumes'),
    path('delete-resume/<int:resume_id>/', views_resume.delete_resume, name='delete_resume'),

    # Mock test URLs
    path('mock-test/', views_mock_test.mock_test_index, name='mock_test'),
    path('mock_test.html', TemplateView.as_view(template_name='mock_test.html'), name='mock_test_legacy'),
    path('exam/', TemplateView.as_view(template_name='exam.html'), name='exam'),
    
    # Comprehensive mock test system URLs
    path('mock-test/roles/', views_mock_test.role_selection, name='role_selection'),
    path('mock-test/role/<str:role>/', views_mock_test.role_test_list, name='role_test_list'),
    path('mock-test/languages/', views_mock_test.language_selection, name='language_selection'),
    path('mock-test/language/<str:language>/', views_mock_test.language_test_list, name='language_test_list'),
    path('mock-test/exam/', views_mock_test.exam_interface, name='exam_interface'),
    path('mock-test/variations/<str:test_type>/<str:category>/<int:test_index>/', views_mock_test.test_variations, name='test_variations'),
    path('mock-test/start/<str:test_type>/<str:category>/<int:test_index>/', views_mock_test.start_exam, name='start_exam'),
    path('mock-test/submit/', views_mock_test.submit_exam, name='submit_exam'),
    path('mock-test/save-progress/', views_mock_test.save_exam_progress, name='save_exam_progress'),
    path('mock-test/results/', views_mock_test.exam_results, name='exam_results'),
    path('mock-test/jamai/', views_mock_test.softskills_selection, name='softskills_selection'),
    path('mock-test/jamai/list/', views_mock_test.softskills_test_list, name='softskills_test_list'),
    path('mock-test/questions/<str:test_type>/<str:category>/<str:filename>', views_mock_test.serve_question_file, name='serve_question_file'),
    
    # Serve mocktestdata directory
    path('mocktestdata/<path:path>', serve, kwargs={'document_root': 'mocktestdata'}, name='mocktestdata_file'),

    # Serve readiness test data directory
    path('radinesstest/<path:path>', serve, kwargs={'document_root': 'radinesstest'}, name='readinesstest_file'),

    # Jamai (Voice Recording) URLs
    path('softskills/', include('jamai.urls', namespace='softskills')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
