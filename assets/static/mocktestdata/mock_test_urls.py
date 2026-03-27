"""
Django URL Configuration for Mock Test System
URL routing for mock test endpoints
"""

from django.urls import path
from . import mock_test_views

app_name = 'mock_test'

urlpatterns = [
    # Mock Test Dashboard
    path('', mock_test_views.mock_test_dashboard, name='mock_test_dashboard'),
    
    # Test Execution
    path('run/<str:test_type>/', mock_test_views.run_test, name='run_test'),
    
    # Test Results
    path('results/', mock_test_views.get_test_results, name='get_test_results'),
    path('results/<str:test_type>/', mock_test_views.get_test_results, name='get_test_results_by_type'),
    
    # Test Logs
    path('logs/', mock_test_views.get_test_logs, name='get_test_logs'),
    path('logs/<str:test_type>/', mock_test_views.get_test_logs, name='get_test_logs_by_type'),
    
    # Test Configuration
    path('config/', mock_test_views.test_configuration, name='test_configuration'),
    
    # Test Statistics
    path('stats/', mock_test_views.get_test_statistics, name='get_test_statistics'),
    
    # Report Generation
    path('report/', mock_test_views.generate_report, name='generate_report'),
    
    # Test Scheduling
    path('schedule/', mock_test_views.schedule_test, name='schedule_test'),
    
    # Test Status
    path('status/', mock_test_views.mock_test_status, name='mock_test_status'),
    
    # Clear Results
    path('clear/', mock_test_views.clear_test_results, name='clear_test_results'),
]
