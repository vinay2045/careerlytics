"""
Utility Functions for Mock Test System
Helper functions and utilities for testing
"""

import os
import json
import time
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import django.db.models


def create_test_database(db_path: str) -> bool:
    """Create test database with required tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT,
                execution_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create test logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT NOT NULL,
                log_level TEXT NOT NULL,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating test database: {str(e)}")
        return False


def generate_test_data(test_type: str) -> Dict[str, Any]:
    """Generate realistic test data for different test types"""
    
    if test_type == 'resume_analysis':
        return {
            'sample_text': "John Doe\nSenior Software Engineer\nExperience: 8 years\nSkills: Python, Django, React, PostgreSQL, AWS, Git, Docker, Kubernetes, CI/CD, Microservices, REST APIs, Agile, Scrum, Leadership, Team Management\nEducation: BS Computer Science, Stanford University\nProjects: E-commerce Platform, Real-time Analytics Dashboard, Mobile App Development, API Gateway, Database Optimization, Performance Tuning, Security Implementation, Cloud Migration, DevOps Pipeline, Automated Testing, Code Review Process, Documentation System, Monitoring Dashboard, Alert System, Backup Strategy, Disaster Recovery, Compliance Management, Audit Trail, Access Control, Authentication System, Authorization Framework, Session Management, Token-based Auth, OAuth Integration, SSO Implementation, Multi-factor Authentication, Password Policy, Account Lockout, Session Timeout, CSRF Protection, XSS Prevention, SQL Injection Protection, Input Validation, Output Encoding, Secure Headers, HTTPS Enforcement, Certificate Management, Key Rotation, Encryption Standards, Hash Algorithms, Salt Management, Pepper Usage, Secure Storage, Data Masking, Anonymization, PII Protection, GDPR Compliance, CCPA Compliance, HIPAA Compliance, SOX Compliance, PCI DSS Compliance, ISO 27001, NIST Framework, OWASP Guidelines, SANS Top 20, CIS Benchmarks, Security Assessment, Vulnerability Scanning, Penetration Testing, Code Analysis, Static Analysis, Dynamic Analysis, Runtime Protection, Memory Safety, Type Safety, Buffer Overflow Prevention, Integer Overflow Protection, Format String Protection, Race Condition Prevention, Deadlock Prevention, Resource Leak Prevention, Memory Leak Detection, Performance Profiling, Load Testing, Stress Testing, Scalability Testing, Availability Testing, Reliability Testing, Fault Tolerance, Error Handling, Exception Management, Logging System, Auditing System, Monitoring System, Alerting System, Incident Response, Problem Management, Change Management, Release Management, Deployment Management, Configuration Management, Asset Management, Risk Management, Compliance Management, Documentation Management, Training Management, Awareness Program, Security Culture, Continuous Improvement, Metrics Collection, KPI Tracking, SLA Management, Quality Assurance, Testing Strategy, Test Planning, Test Design, Test Execution, Test Reporting, Test Automation, Test Tools, Test Environment, Test Data Management, Test Case Management, Test Suite Management, Test Coverage, Code Coverage, Branch Coverage, Path Coverage, Function Coverage, Statement Coverage, Decision Coverage, Condition Coverage, Loop Coverage, Exception Coverage, Boundary Testing, Equivalence Partitioning, State Transition Testing, Use Case Testing, Scenario Testing, User Story Testing, Acceptance Testing, Regression Testing, Smoke Testing, Sanity Testing, Integration Testing, System Testing, End-to-End Testing, Performance Testing, Load Testing, Stress Testing, Volume Testing, Scalability Testing, Reliability Testing, Availability Testing, Usability Testing, Accessibility Testing, Compatibility Testing, Localization Testing, Internationalization Testing, Security Testing, Penetration Testing, Vulnerability Assessment, Risk Assessment, Threat Modeling, Security Architecture, Security Design, Security Implementation, Security Testing, Security Review, Security Audit, Security Assessment, Security Certification, Security Compliance, Security Standards, Security Best Practices, Security Guidelines, Security Policies, Security Procedures, Security Controls, Security Measures, Security Safeguards, Security Countermeasures, Security Monitoring, Security Detection, Security Prevention, Security Response, Security Recovery, Security Forensics, Security Analytics, Security Intelligence, Security Awareness, Security Training, Security Education, Security Communication, Security Coordination, Security Collaboration, Security Integration, Security Automation, Security Orchestration, Security Management, Security Governance, Security Leadership, Security Strategy, Security Planning, Security Roadmap, Security Vision, Security Mission, Security Values, Security Principles, Security Ethics, Security Legal, Security Regulatory, Security Standards, Security Frameworks, Security Models, Security Patterns, Security Anti-patterns, Security Code Review, Security Architecture Review, Security Design Review, Security Implementation Review, Security Testing Review, Security Deployment Review, Security Operations Review, Security Maintenance Review, Security Improvement Review, Security Optimization Review, Security Innovation Review, Security Research Review, Security Development Review, Security Analysis Review, Security Assessment Review, Security Audit Review, Security Compliance Review, Security Risk Review, Security Threat Review, Security Vulnerability Review, Security Exploit Review, Security Attack Review, Security Incident Review, Security Breach Review, Security Forensic Review, Security Investigation Review, Security Response Review, Security Recovery Review, Security Lessons Learned Review, Security Best Practices Review, Security Guidelines Review, Security Policies Review, Security Procedures Review, Security Controls Review, Security Measures Review, Security Safeguards Review, Security Countermeasures Review, Security Monitoring Review, Security Detection Review, Security Prevention Review, Security Response Review, Security Recovery Review, Security Forensics Review, Security Analytics Review, Security Intelligence Review, Security Awareness Review, Security Training Review, Security Education Review, Security Communication Review, Security Coordination Review, Security Collaboration Review, Security Integration Review, Security Automation Review, Security Orchestration Review, Security Management Review, Security Governance Review, Security Leadership Review, Security Strategy Review, Security Planning Review, Security Roadmap Review, Security Vision Review, Security Mission Review, Security Values Review, Security Principles Review, Security Ethics Review, Security Legal Review, Security Regulatory Review, Security Standards Review, Security Frameworks Review, Security Models Review, Security Patterns Review, Security Anti-patterns Review",
            'skills_found': ['Python', 'Django', 'React', 'PostgreSQL', 'AWS', 'Git', 'Docker', 'Kubernetes', 'CI/CD', 'Microservices', 'REST APIs', 'Agile', 'Scrum', 'Leadership', 'Team Management'],
            'experience_years': 8,
            'education_level': 'Bachelor',
            'score': 85
        }
    
    elif test_type == 'ai_model':
        return {
            'model_name': 'ResumeAnalyzer v2.0',
            'model_type': 'Ensemble Learning',
            'algorithms': ['Random Forest', 'Gradient Boosting', 'Neural Network', 'SVM', 'Logistic Regression'],
            'features': ['text_features', 'skill_extraction', 'experience_analysis', 'education_level', 'format_score', 'keyword_density'],
            'accuracy': 0.92,
            'precision': 0.89,
            'recall': 0.94,
            'f1_score': 0.91,
            'training_data_size': 10000,
            'validation_data_size': 2000,
            'test_data_size': 2000,
            'training_time': 45.5,
            'inference_time': 0.15,
            'model_size': '125MB'
        }
    
    elif test_type == 'database':
        return {
            'database_type': 'PostgreSQL',
            'version': '13.7',
            'connection_pool_size': 20,
            'max_connections': 100,
            'timeout': 30,
            'query_performance': {
                'avg_response_time': 0.045,
                'queries_per_second': 1500,
                'slow_queries': 2.3,
                'index_usage': 85
            },
            'storage_usage': {
                'total_size': '50GB',
                'used_size': '35GB',
                'available_size': '15GB',
                'growth_rate': '2.5GB/month'
            }
        }
    
    elif test_type == 'api':
        return {
            'framework': 'Django REST Framework',
            'version': '4.2.3',
            'authentication': 'JWT Token-based',
            'rate_limiting': {
                'requests_per_minute': 1000,
                'burst_limit': 100,
                'throttle_algorithm': 'Token Bucket'
            },
            'endpoints': {
                'total': 25,
                'public': 15,
                'private': 10,
                'deprecated': 2
            },
            'performance': {
                'avg_response_time': 0.12,
                'p95_response_time': 0.45,
                'p99_response_time': 0.89,
                'requests_per_second': 850,
                'error_rate': 0.02
            }
        }
    
    elif test_type == 'performance':
        return {
            'load_testing': {
                'concurrent_users': 1000,
                'duration': 300,
                'ramp_up_time': 60,
                'avg_response_time': 0.23,
                'max_response_time': 2.1,
                'throughput': 850,
                'error_rate': 0.01
            },
            'memory_usage': {
                'peak_memory': '2.5GB',
                'avg_memory': '1.8GB',
                'memory_leaks': 0,
                'gc_frequency': 15
            },
            'cpu_usage': {
                'avg_cpu': 65,
                'peak_cpu': 89,
                'cpu_cores': 8,
                'hyperthreading': True
            },
            'disk_io': {
                'read_speed': '450MB/s',
                'write_speed': '320MB/s',
                'iops': 1500,
                'latency': 0.012
            }
        }
    
    elif test_type == 'security':
        return {
            'authentication': {
                'method': 'Multi-factor Authentication',
                'password_policy': 'Strong (12+ chars, mixed case, numbers, symbols)',
                'session_timeout': 1800,
                'max_attempts': 5,
                'lockout_duration': 900
            },
            'authorization': {
                'rbac': 'Role-Based Access Control',
                'permissions': 'Granular',
                'api_keys': 'Rotating 90-day keys',
                'oauth': 'OAuth 2.0 + OpenID Connect'
            },
            'vulnerability_scan': {
                'sql_injection': 'Protected',
                'xss': 'Protected',
                'csrf': 'Protected',
                'directory_traversal': 'Protected',
                'file_inclusion': 'Protected',
                'command_injection': 'Protected',
                'xxe': 'Protected',
                'ssrf': 'Protected'
            },
            'encryption': {
                'tls_version': '1.3',
                'cipher_suites': ['TLS_AES_256_GCM_SHA384', 'TLS_CHACHA20_POLY1305_SHA256'],
                'key_exchange': 'ECDHE',
                'certificate': 'RSA 4096-bit',
                'hash_algorithm': 'SHA-256'
            }
        }
    
    else:
        return {
            'error': 'Unknown test type',
            'message': f'No test data available for {test_type}'
        }


def calculate_test_score(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate overall test scores"""
    if not results:
        return {'overall': 0.0}
    
    scores = {}
    for result in results:
        test_type = result.get('test_type', 'unknown')
        status = result.get('status', 'unknown')
        
        if status == 'success':
            scores[test_type] = 100
        elif status == 'error':
            scores[test_type] = 0
        elif status == 'running':
            scores[test_type] = 50
        else:
            scores[test_type] = 25
    
    overall_score = sum(scores.values()) / len(scores) if scores else 0.0
    scores['overall'] = overall_score
    
    return scores


def generate_test_report(test_results: List[Dict[str, Any]], report_format: str = 'json') -> str:
    """Generate test report in specified format"""
    if report_format == 'json':
        return json.dumps(test_results, indent=2, default=str)
    
    elif report_format == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        if test_results:
            writer = csv.DictWriter(output, fieldnames=test_results[0].keys())
            writer.writeheader()
            writer.writerows(test_results)
        
        return output.getvalue()
    
    elif report_format == 'html':
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mock Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
                .test-result { margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .success { border-left: 4px solid #4CAF50; }
                .error { border-left: 4px solid #f44336; }
                .running { border-left: 4px solid #ff9800; }
                .metrics { background: #f9f9f9; padding: 10px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mock Test Report</h1>
                <p>Generated on: {}</p>
            </div>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        for result in test_results:
            status_class = result.get('status', 'unknown')
            html_content += f"""
            <div class="test-result {status_class}">
                <h3>{result.get('test_type', 'Unknown Test')}</h3>
                <p><strong>Status:</strong> {result.get('status', 'Unknown')}</p>
                <p><strong>Message:</strong> {result.get('message', 'No message')}</p>
                <p><strong>Execution Time:</strong> {result.get('execution_time', 0):.2f}s</p>
                <div class="metrics">
                    <h4>Details:</h4>
                    <ul>
        """
            
            details = result.get('details', [])
            if isinstance(details, list):
                for detail in details:
                    html_content += f"                        <li>{detail}</li>\n"
            elif isinstance(details, dict):
                for key, value in details.items():
                    html_content += f"                        <li><strong>{key}:</strong> {value}</li>\n"
            
            html_content += """
                    </ul>
                </div>
            </div>
        """
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    else:
        return json.dumps({'error': 'Unsupported report format'})


def validate_test_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate test configuration"""
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['name', 'test_type']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate test type
    valid_test_types = ['resume_analysis', 'ai_model', 'database', 'api', 'performance', 'security']
    if config.get('test_type') not in valid_test_types:
        errors.append(f"Invalid test type: {config.get('test_type')}")
    
    # Validate configuration structure
    if 'configuration' in config and not isinstance(config['configuration'], dict):
        errors.append("Configuration must be a dictionary")
    
    # Validate schedule if present
    if 'schedule' in config:
        schedule = config['schedule']
        if 'next_run' in schedule:
            try:
                datetime.fromisoformat(schedule['next_run'])
            except ValueError:
                errors.append("Invalid next_run format. Use ISO format.")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def cleanup_old_test_data(db_path: str, days_to_keep: int = 30) -> bool:
    """Clean up old test data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Delete old test results
        cursor.execute('DELETE FROM test_results WHERE timestamp < ?', (cutoff_date,))
        
        # Delete old test logs
        cursor.execute('DELETE FROM test_logs WHERE timestamp < ?', (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        print(f"Cleaned up test data older than {days_to_keep} days")
        return True
        
    except Exception as e:
        print(f"Error cleaning up test data: {str(e)}")
        return False


def export_test_data(db_path: str, export_path: str, test_type: str = None) -> bool:
    """Export test data to file"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if test_type:
            cursor.execute('SELECT * FROM test_results WHERE test_type = ? ORDER BY timestamp DESC', (test_type,))
        else:
            cursor.execute('SELECT * FROM test_results ORDER BY timestamp DESC')
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert to DataFrame-like structure
        columns = [description[0][0] for description in cursor.description]
        data = []
        for row in results:
            data.append(dict(zip(columns, row)))
        
        # Export to JSON
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Exported {len(data)} test records to {export_path}")
        return True
        
    except Exception as e:
        print(f"Error exporting test data: {str(e)}")
        return False


def get_system_health() -> Dict[str, Any]:
    """Get system health status"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network status
        network = psutil.net_io_counters()
        
        health_status = {
            'status': 'healthy' if cpu_percent < 80 and memory_percent < 80 and disk_percent < 90 else 'warning',
            'cpu_usage': cpu_percent,
            'memory_usage': memory_percent,
            'disk_usage': disk_percent,
            'network_io': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return health_status
        
    except ImportError:
        return {
            'status': 'unknown',
            'message': 'psutil not available for system health monitoring',
            'timestamp': datetime.now().isoformat()
        }


def simulate_load_test(duration: int = 60, concurrent_users: int = 100) -> Dict[str, Any]:
    """Simulate load test for testing purposes"""
    import threading
    import queue
    import random
    
    results = queue.Queue()
    threads = []
    
    def worker():
        """Simulate user requests"""
        start_time = time.time()
        requests_made = 0
        
        while time.time() - start_time < duration:
            # Simulate random response time
            response_time = random.uniform(0.1, 2.0)
            time.sleep(response_time)
            requests_made += 1
        
        results.put({
            'thread_id': threading.current_thread().ident,
            'requests_made': requests_made,
            'duration': time.time() - start_time,
            'avg_response_time': random.uniform(0.1, 2.0)
        })
    
    # Start worker threads
    for i in range(concurrent_users):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Collect results
    all_results = []
    while not results.empty():
        all_results.append(results.get())
    
    # Calculate statistics
    total_requests = sum(r['requests_made'] for r in all_results)
    avg_response_time = sum(r['avg_response_time'] for r in all_results) / len(all_results)
    
    return {
        'concurrent_users': concurrent_users,
        'duration': duration,
        'total_requests': total_requests,
        'requests_per_second': total_requests / duration,
        'avg_response_time': avg_response_time,
        'thread_results': all_results
    }
