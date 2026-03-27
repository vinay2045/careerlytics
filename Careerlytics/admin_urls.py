from django.urls import path
from . import views

app_name = 'readiness_admin'

urlpatterns = [
    # Student Readiness Management
    path('student-classification/', views.student_classification, name='student_classification'),
]
