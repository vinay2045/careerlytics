from django.urls import path, include
from . import views

app_name = 'personalizedplan'

urlpatterns = [
    path('test-system/', include('personalizedplan.testsystem.urls')),
    path('dashboard/', views.personalized_plan_dashboard, name='dashboard'),
    path('api/stats/', views.api_dashboard_stats, name='api_stats'),
    path('start/', views.start_personalized_plan, name='start'),
    path('create-from-assessment/', views.create_plan_from_assessment, name='create_from_assessment'),
    path('plan/<uuid:plan_id>/', views.plan_detail, name='plan_detail'),
    path('complete-task/<uuid:task_id>/', views.complete_daily_task, name='complete_task'),
    path('weekly-test/<uuid:week_id>/', views.take_weekly_test, name='weekly_test'),
    path('resume-impact/', views.resume_impact_dashboard, name='resume_impact'),
    path('reset/', views.reset_plan, name='reset_plan'),
    path('delete/', views.delete_plan, name='delete_plan'),
]
