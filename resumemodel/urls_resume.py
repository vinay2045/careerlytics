from django.urls import path
from . import views_resume

app_name = 'users'

urlpatterns = [
    # Resume-related URLs
    path('my-resumes/', views_resume.my_resumes, name='my_resumes'),
    path('download-resume/<int:resume_id>/', views_resume.download_resume, name='download_resume'),
    path('delete-resume/<int:resume_id>/', views_resume.delete_resume, name='delete_resume'),
    path('analyze-resume-api/', views_resume.analyze_resume_api, name='analyze_resume_api'),
]
