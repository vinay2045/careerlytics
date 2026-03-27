from django.urls import path
from . import views

app_name = 'resumeanalysis'

urlpatterns = [
    # Resume upload and analysis
    path('upload/', views.upload_resume, name='upload_resume'),
    path('delete/<uuid:analysis_id>/', views.delete_resume, name='delete_resume'),
    
    # Test quiz functionality
    path('test-quiz/', views.test_quiz, name='test_quiz'),
    
    # Test management
    path('test/start/', views.start_test, name='start_test'),
    path('test/start/<int:role_id>/', views.start_test_with_role, name='start_test_with_role'),
    path('submit-test/', views.submit_test, name='submit_test'),
    
    # Quiz management (legacy)
    path('quiz/<uuid:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('quiz/<uuid:quiz_id>/submit/', views.submit_answer, name='submit_answer'),
    path('quiz/<uuid:quiz_id>/complete/', views.complete_quiz, name='complete_quiz'),
    path('quiz/<uuid:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
