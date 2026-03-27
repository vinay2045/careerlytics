from django.urls import path
from . import views
from . import views_resume
from . import views_python_test
from . import views_mock_test

app_name = 'users'

urlpatterns = [
    # Original user URLs
    path('user_login/', views.UserLogin, name='user_login'),  # Direct access for /user_login/
    path('reset-password/', views.reset_password, name='reset_password'),
    path('UserRegisterAction/', views.UserRegisterAction, name='UserRegisterAction'),
    path('UserLoginCheck/', views.UserLoginCheck, name='UserLoginCheck'),
    path('UserLogout/', views.UserLogout, name='UserLogout'),
    path('UserHome/', views.UserHome, name='UserHome'),
    path('UserProfile/', views.user_profile, name='UserProfile'),
    path('EditUserProfile/', views.edit_user_profile, name='EditUserProfile'),
    path('UserDocuments/', views.user_documents, name='UserDocuments'),
    path('UserViewDocs/<int:doc_id>/', views.user_view_document, name='UserViewDocs'),
    path('UserSearchDocuments/', views.UserCanViewDocusActions, name='UserSearchDocuments'),
    
    path('UserViewDocument/<int:doc_id>/', views.user_view_document, name='UserViewDocument'),
    path('UserCanViewDocusActions/', views.UserCanViewDocusActions, name='UserCanViewDocusActions'),
    
    # Resume-related URLs
    path('my-resumes/', views_resume.my_resumes, name='my_resumes'),
    path('download-resume/<int:resume_id>/', views_resume.download_resume, name='download_resume_int'),
    path('download-resume/<uuid:resume_id>/', views_resume.download_resume, name='download_resume'),
    path('delete-resume/<int:resume_id>/', views_resume.delete_resume, name='delete_resume_int'),
    
    # Campus Drives & Readiness Tests URLs (Student-Only)
    path('campus-drives/', views.campus_drives, name='campus_drives'),
    path('campus-drives/apply/<int:drive_id>/', views.apply_drive, name='apply_drive'),
    path('campus-drives/take-test/<int:test_id>/', views.take_readiness_test, name='take_readiness_test'),
    path('campus-drives/submit-test/<int:test_id>/', views.submit_readiness_test, name='submit_readiness_test'),
    path('campus-drives/my-applications/', views.my_drive_applications, name='my_drive_applications'),
    path('campus-drives/my-results/', views.my_test_results, name='my_test_results'),
    
    # Readiness Test URLs
    path('readiness-test/', views.readiness_test_view, name='readiness_test'),
    # Note: submit_readiness_test is handled by campus-drives/submit-test/<int:test_id>/
    
    path('delete-resume/<uuid:resume_id>/', views_resume.delete_resume, name='delete_resume'),
    path('analyze-resume-api/', views_resume.analyze_resume_api, name='analyze_resume_api'),
    
    # Python test URLs
    path('python-test-dashboard/', views_python_test.python_test_dashboard, name='python_test_dashboard'),
    path('load-python-questions/', views_python_test.load_python_questions, name='load_python_questions'),
    path('python-test/', views_python_test.python_test, name='python_test'),
    path('submit-python-test/', views_python_test.submit_python_test, name='submit_python_test'),
    path('python-test-results/', views_python_test.python_test_results, name='python_test_results'),
    
    # Core Assessment URLs
    path('core-assessment-selection/', views_mock_test.core_assessment_selection, name='core_assessment_selection'),
    path('core-assessment/<str:assessment_type>/', views_mock_test.core_assessment_detail, name='core_assessment_detail'),
    path('start-core-assessment/<str:assessment_type>/<int:test_index>/', views_mock_test.start_core_assessment, name='start_core_assessment'),
    path('submit-core-assessment/', views_mock_test.submit_core_assessment, name='submit_core_assessment'),
    path('core-results/', views_mock_test.core_assessment_results, name='core_results'),
    
    path('ai-interviewer/', views.ai_interviewer, name='ai_interviewer'),
    path('ai-interviewer-api/generate-question/', views.ai_interview_generate_question, name='ai_interview_generate_question'),
    path('ai-interviewer-api/tts/', views.ai_interview_tts, name='ai_interview_tts'),
    path('ai-interviewer-api/evaluate/', views.ai_interview_evaluate, name='ai_interview_evaluate'),
    path('ai-interviewer-api/ping/', views.ai_interview_ping, name='ai_interview_ping'),
    path('maya-chat/', views.maya_chat, name='maya_chat'),
]
