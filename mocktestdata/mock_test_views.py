"""
Django Views for Mock Test System
API endpoints for running and managing mock tests
"""

import json
import time
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from .mock_test_models import MockTestResult, MockTestLog, MockTestConfiguration, MockTestSchedule, MockTestReport
from .mock_test_backend import MockTestBackend


def mock_test_dashboard(request):
    """Mock test dashboard view"""
    # Get recent test results
    recent_results = MockTestResult.objects.order_by('-created_at')[:10]
    
    # Get test statistics
    test_stats = {}
    for test_type, _ in MockTestResult.TEST_TYPES:
        results = MockTestResult.objects.filter(test_type=test_type)
        test_stats[test_type] = {
            'total': results.count(),
            'successful': results.filter(status='success').count(),
            'failed': results.filter(status='error').count(),
            'last_run': results.first().created_at if results.exists() else None
        }
    
    context = {
        'recent_results': recent_results,
        'test_stats': test_stats,
        'page_title': 'Mock Test Dashboard'
    }
    
    return render(request, 'mock_test_dashboard.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def run_test(request, test_type):
    """Run a specific mock test"""
    if test_type not in [t[0] for t in MockTestResult.TEST_TYPES]:
        return JsonResponse({
            'status': 'error',
            'message': f'Invalid test type: {test_type}'
        }, status=400)
    
    # Initialize backend
    backend = MockTestBackend()
    
    # Update test status to running
    test_result, created = MockTestResult.objects.get_or_create(
        test_type=test_type,
        defaults={
            'status': 'running',
            'message': f'{test_type.replace("_", " ").title()} test is running...',
            'execution_time': 0
        }
    )
    
    if not created:
        test_result.status = 'running'
        test_result.message = f'{test_type.replace("_", " ").title()} test is running...'
        test_result.execution_time = 0
        test_result.save()
    
    try:
        # Run the appropriate test
        if test_type == 'resume_analysis':
            result = backend.test_resume_analysis()
        elif test_type == 'ai_model':
            result = backend.test_ai_model()
        elif test_type == 'database':
            result = backend.test_database()
        elif test_type == 'api':
            result = backend.test_api()
        elif test_type == 'performance':
            result = backend.test_performance()
        elif test_type == 'security':
            result = backend.test_security()
        else:
            result = {
                'status': 'error',
                'message': f'Unknown test type: {test_type}',
                'details': ['Test type not implemented'],
                'execution_time': 0
            }
        
        # Update test result
        test_result.status = result['status']
        test_result.message = result['message']
        test_result.details = result.get('details', [])
        test_result.execution_time = result.get('execution_time', 0)
        test_result.metrics = result.get('metrics', {})
        test_result.save()
        
        return JsonResponse(result)
        
    except Exception as e:
        # Update test result with error
        test_result.status = 'error'
        test_result.message = f'Test failed: {str(e)}'
        test_result.details = ['Error in test execution']
        test_result.execution_time = time.time() - time.time()
        test_result.save()
        
        return JsonResponse({
            'status': 'error',
            'message': f'Test execution failed: {str(e)}',
            'details': ['Error in test execution']
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_test_results(request):
    """Get test results"""
    test_type = request.GET.get('test_type')
    limit = int(request.GET.get('limit', 50))
    
    # Filter results
    if test_type:
        results = MockTestResult.objects.filter(test_type=test_type)
    else:
        results = MockTestResult.objects.all()
    
    # Apply limit and order
    results = results.order_by('-created_at')[:limit]
    
    # Convert to list of dictionaries
    results_data = []
    for result in results:
        results_data.append({
            'id': result.id,
            'test_type': result.test_type,
            'status': result.status,
            'message': result.message,
            'details': result.get_details_list(),
            'execution_time': result.execution_time,
            'metrics': result.metrics,
            'created_at': result.created_at.isoformat(),
            'updated_at': result.updated_at.isoformat()
        })
    
    return JsonResponse({
        'status': 'success',
        'results': results_data,
        'count': len(results_data)
    })


@csrf_exempt
@require_http_methods(["POST"])
def clear_test_results(request):
    """Clear test results"""
    try:
        data = json.loads(request.body)
        test_type = data.get('test_type')
        
        if test_type:
            MockTestResult.objects.filter(test_type=test_type).delete()
            message = f'Cleared results for {test_type}'
        else:
            MockTestResult.objects.all().delete()
            message = 'Cleared all test results'
        
        return JsonResponse({
            'status': 'success',
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to clear results: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_test_logs(request):
    """Get test logs"""
    test_type = request.GET.get('test_type')
    log_level = request.GET.get('log_level', 'INFO')
    limit = int(request.GET.get('limit', 100))
    
    # Filter logs
    if test_type:
        logs = MockTestLog.objects.filter(test_type=test_type)
    else:
        logs = MockTestLog.objects.all()
    
    if log_level != 'ALL':
        logs = logs.filter(log_level=log_level)
    
    # Apply limit and order
    logs = logs.order_by('-created_at')[:limit]
    
    # Convert to list of dictionaries
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'test_type': log.test_type,
            'log_level': log.log_level,
            'message': log.message,
            'created_at': log.created_at.isoformat()
        })
    
    return JsonResponse({
        'status': 'success',
        'logs': logs_data,
        'count': len(logs_data)
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def test_configuration(request):
    """Manage test configurations"""
    if request.method == 'GET':
        # Get all configurations
        configs = MockTestConfiguration.objects.filter(is_active=True)
        
        configs_data = []
        for config in configs:
            configs_data.append({
                'id': config.id,
                'name': config.name,
                'description': config.description,
                'configuration': config.configuration,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'configurations': configs_data
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create or update configuration
            config, created = MockTestConfiguration.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data.get('description', ''),
                    'configuration': data.get('configuration', {}),
                    'is_active': data.get('is_active', True)
                }
            )
            
            if not created:
                config.description = data.get('description', config.description)
                config.configuration = data.get('configuration', config.configuration)
                config.is_active = data.get('is_active', config.is_active)
                config.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Configuration saved successfully',
                'config_id': config.id
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to save configuration: {str(e)}'
            }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_test_statistics(request):
    """Get comprehensive test statistics"""
    # Get overall statistics
    total_tests = MockTestResult.objects.count()
    successful_tests = MockTestResult.objects.filter(status='success').count()
    failed_tests = MockTestResult.objects.filter(status='error').count()
    running_tests = MockTestResult.objects.filter(status='running').count()
    
    # Get statistics by test type
    type_stats = {}
    for test_type, _ in MockTestResult.TEST_TYPES:
        results = MockTestResult.objects.filter(test_type=test_type)
        type_stats[test_type] = {
            'total': results.count(),
            'successful': results.filter(status='success').count(),
            'failed': results.filter(status='error').count(),
            'success_rate': (results.filter(status='success').count() / results.count() * 100) if results.count() > 0 else 0,
            'avg_execution_time': results.aggregate(models.Avg('execution_time'))['execution_time__avg'] or 0
        }
    
    # Get recent activity
    recent_results = MockTestResult.objects.order_by('-created_at')[:10]
    recent_activity = []
    for result in recent_results:
        recent_activity.append({
            'test_type': result.test_type,
            'status': result.status,
            'execution_time': result.execution_time,
            'created_at': result.created_at.isoformat()
        })
    
    statistics = {
        'overall': {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'running_tests': running_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
        },
        'by_type': type_stats,
        'recent_activity': recent_activity
    }
    
    return JsonResponse({
        'status': 'success',
        'statistics': statistics
    })


@csrf_exempt
@require_http_methods(["POST"])
def generate_report(request):
    """Generate test report"""
    try:
        data = json.loads(request.body)
        report_type = data.get('report_type', 'summary')
        test_types = data.get('test_types', [])
        
        # Get test results
        if test_types:
            results = MockTestResult.objects.filter(test_type__in=test_types)
        else:
            results = MockTestResult.objects.all()
        
        # Generate report content
        if report_type == 'summary':
            report_content = generate_summary_report(results)
        elif report_type == 'detailed':
            report_content = generate_detailed_report(results)
        elif report_type == 'comparison':
            report_content = generate_comparison_report(results)
        else:
            report_content = 'Invalid report type'
        
        # Save report
        report = MockTestReport.objects.create(
            name=f"Mock Test Report - {report_type.title()}",
            report_type=report_type,
            content=report_content
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Report generated successfully',
            'report_id': report.id,
            'report_content': report_content
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to generate report: {str(e)}'
        }, status=500)


def generate_summary_report(results):
    """Generate summary report content"""
    total_tests = results.count()
    successful_tests = results.filter(status='success').count()
    failed_tests = results.filter(status='error').count()
    
    content = f"""
# Mock Test Summary Report

Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Total Tests: {total_tests}
- Successful Tests: {successful_tests}
- Failed Tests: {failed_tests}
- Success Rate: {(successful_tests / total_tests * 100):.1f}%

## Test Results by Type
"""
    
    for test_type, _ in MockTestResult.TEST_TYPES:
        type_results = results.filter(test_type=test_type)
        if type_results.exists():
            content += f"""
### {test_type.replace('_', ' ').title()}
- Total: {type_results.count()}
- Successful: {type_results.filter(status='success').count()}
- Failed: {type_results.filter(status='error').count()}
- Success Rate: {(type_results.filter(status='success').count() / type_results.count() * 100):.1f}%
"""
    
    return content


def generate_detailed_report(results):
    """Generate detailed report content"""
    content = f"""
# Detailed Mock Test Report

Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

## Detailed Results
"""
    
    for result in results.order_by('-created_at'):
        content += f"""
### {result.test_type.replace('_', ' ').title()} - {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- Status: {result.status}
- Message: {result.message}
- Execution Time: {result.execution_time:.2f}s
- Details:
{chr(10).join(f"  - {detail}" for detail in result.get_details_list())}
"""
    
    return content


def generate_comparison_report(results):
    """Generate comparison report content"""
    content = f"""
# Comparison Mock Test Report

Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Comparison
"""
    
    # Group by test type and calculate averages
    for test_type, _ in MockTestResult.TEST_TYPES:
        type_results = results.filter(test_type=test_type)
        if type_results.exists():
            avg_time = type_results.aggregate(models.Avg('execution_time'))['execution_time__avg'] or 0
            success_rate = (type_results.filter(status='success').count() / type_results.count() * 100) if type_results.count() > 0 else 0
            
            content += f"""
### {test_type.replace('_', ' ').title()}
- Average Execution Time: {avg_time:.2f}s
- Success Rate: {success_rate:.1f}%
- Total Runs: {type_results.count()}
"""
    
    return content


@csrf_exempt
@require_http_methods(["POST"])
def schedule_test(request):
    """Schedule automated test runs"""
    try:
        data = json.loads(request.body)
        
        # Create schedule
        schedule = MockTestSchedule.objects.create(
            test_type=data['test_type'],
            schedule_type=data.get('schedule_type', 'once'),
            next_run=data.get('next_run'),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Test scheduled successfully',
            'schedule_id': schedule.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to schedule test: {str(e)}'
        }, status=500)


def mock_test_status(request):
    """Get current status of all tests"""
    # Get latest result for each test type
    status_data = {}
    for test_type, _ in MockTestResult.TEST_TYPES:
        latest_result = MockTestResult.objects.filter(test_type=test_type).order_by('-created_at').first()
        status_data[test_type] = {
            'status': latest_result.status if latest_result else 'never_run',
            'last_run': latest_result.created_at.isoformat() if latest_result else None,
            'message': latest_result.message if latest_result else 'No previous runs'
        }
    
    return JsonResponse({
        'status': 'success',
        'test_status': status_data
    })
