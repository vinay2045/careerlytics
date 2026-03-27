from django.urls import path
from . import views

app_name = 'testsystem'

urlpatterns = [
    path('start-weekly/<uuid:week_id>/', views.start_weekly_test, name='start_weekly'),
    path('start-initial/<str:category>/', views.start_initial_assessment, name='start_initial'),
    path('interface/', views.exam_interface, name='exam_interface'),
    path('api/questions/', views.get_test_data, name='get_questions'),
    path('submit/', views.submit_test, name='submit_test'),
    path('results/', views.exam_results, name='exam_results'),
]
