#!/usr/bin/env python3
"""
Mock Test Backend for AI Resume Analyzer
Comprehensive testing and debugging tools
"""

import os
import sys
import json
import time
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import django
from django.conf import settings
from django.db import connection

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'matrix.settings')
django.setup()

class MockTestBackend:
    """Comprehensive Mock Test Backend for AI Resume Analyzer"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.db_path = os.path.join(os.path.dirname(__file__), 'mock_test.db')
        self.init_database()
    
    def init_database(self):
        """Initialize mock test database"""
        try:
            conn = sqlite3.connect(self.db_path)
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
            self.log_info('Database', 'Mock test database initialized successfully')
            
        except Exception as e:
            self.log_error('Database', f'Failed to initialize database: {str(e)}')
    
    def log_info(self, test_type: str, message: str):
        """Log info message"""
        self._log(test_type, 'INFO', message)
    
    def log_error(self, test_type: str, message: str):
        """Log error message"""
        self._log(test_type, 'ERROR', message)
    
    def log_warning(self, test_type: str, message: str):
        """Log warning message"""
        self._log(test_type, 'WARNING', message)
    
    def _log(self, test_type: str, level: str, message: str):
        """Internal logging method"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_logs (test_type, log_level, message)
                VALUES (?, ?, ?)
            ''', (test_type, level, message))
            
            conn.commit()
            conn.close()
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {test_type}: {message}")
            
        except Exception as e:
            print(f"Logging error: {str(e)}")
    
    def test_resume_analysis(self) -> Dict[str, Any]:
        """Test resume analysis functionality"""
        self.start_time = time.time()
        self.log_info('Resume Analysis', 'Starting resume analysis test')
        
        try:
            # Test text parsing
            test_text = "John Doe\nSoftware Engineer\nExperience: 5 years\nSkills: Python, JavaScript, SQL"
            parsed_text = self._parse_resume_text(test_text)
            
            # Test skill extraction
            skills = self._extract_skills(parsed_text)
            
            # Test score calculation
            score = self._calculate_resume_score(skills)
            
            # Test database storage
            storage_success = self._test_database_storage(test_text, score)
            
            execution_time = time.time() - self.start_time
            
            result = {
                'status': 'success' if all([parsed_text, skills, score, storage_success]) else 'error',
                'message': 'Resume analysis test completed successfully' if storage_success else 'Database storage failed',
                'details': [
                    f'Text parsing: {"✓" if parsed_text else "✗"}',
                    f'Skill extraction: {"✓" if skills else "✗"}',
                    f'Score calculation: {"✓" if score > 0 else "✗"}',
                    f'Database storage: {"✓" if storage_success else "✗"}'
                ],
                'execution_time': round(execution_time, 2),
                'parsed_data': {
                    'text': parsed_text,
                    'skills': skills,
                    'score': score
                }
            }
            
            self.save_test_result('resume_analysis', result)
            self.log_info('Resume Analysis', f'Test completed in {execution_time:.2f} seconds')
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'Resume analysis test failed: {str(e)}',
                'details': ['Error in test execution'],
                'execution_time': time.time() - self.start_time
            }
            
            self.save_test_result('resume_analysis', error_result)
            self.log_error('Resume Analysis', f'Test failed: {str(e)}')
            
            return error_result
    
    def test_ai_model(self) -> Dict[str, Any]:
        """Test AI model functionality"""
        self.start_time = time.time()
        self.log_info('AI Model', 'Starting AI model test')
        
        try:
            # Test model loading
            model_loaded = self._test_model_loading()
            
            # Test prediction accuracy
            accuracy = self._test_prediction_accuracy()
            
            # Test response time
            response_time = self._test_response_time()
            
            # Test error handling
            error_handling = self._test_error_handling()
            
            execution_time = time.time() - self.start_time
            
            result = {
                'status': 'success' if all([model_loaded, accuracy > 0.8, response_time < 2.0, error_handling]) else 'error',
                'message': 'AI model test completed successfully',
                'details': [
                    f'Model loading: {"✓" if model_loaded else "✗"}',
                    f'Prediction accuracy: {"✓" if accuracy > 0.8 else "✗"} ({accuracy:.2f})',
                    f'Response time: {"✓" if response_time < 2.0 else "✗"} ({response_time:.2f}s)',
                    f'Error handling: {"✓" if error_handling else "✗"}'
                ],
                'execution_time': round(execution_time, 2),
                'metrics': {
                    'accuracy': accuracy,
                    'response_time': response_time,
                    'model_loaded': model_loaded
                }
            }
            
            self.save_test_result('ai_model', result)
            self.log_info('AI Model', f'Test completed in {execution_time:.2f} seconds')
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'AI model test failed: {str(e)}',
                'details': ['Error in test execution'],
                'execution_time': time.time() - self.start_time
            }
            
            self.save_test_result('ai_model', error_result)
            self.log_error('AI Model', f'Test failed: {str(e)}')
            
            return error_result
    
    def test_database(self) -> Dict[str, Any]:
        """Test database connectivity and CRUD operations"""
        self.start_time = time.time()
        self.log_info('Database', 'Starting database test')
        
        try:
            # Test connection
            connection_success = self._test_database_connection()
            
            # Test CRUD operations
            crud_success = self._test_crud_operations()
            
            # Test data integrity
            integrity_success = self._test_data_integrity()
            
            # Test performance
            performance_score = self._test_database_performance()
            
            execution_time = time.time() - self.start_time
            
            result = {
                'status': 'success' if all([connection_success, crud_success, integrity_success]) else 'error',
                'message': 'Database test completed successfully',
                'details': [
                    f'Connection: {"✓" if connection_success else "✗"}',
                    f'CRUD operations: {"✓" if crud_success else "✗"}',
                    f'Data integrity: {"✓" if integrity_success else "✗"}',
                    f'Performance: {"✓" if performance_score > 0.8 else "✗"} ({performance_score:.2f})'
                ],
                'execution_time': round(execution_time, 2),
                'metrics': {
                    'connection': connection_success,
                    'crud': crud_success,
                    'integrity': integrity_success,
                    'performance': performance_score
                }
            }
            
            self.save_test_result('database', result)
            self.log_info('Database', f'Test completed in {execution_time:.2f} seconds')
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'Database test failed: {str(e)}',
                'details': ['Error in test execution'],
                'execution_time': time.time() - self.start_time
            }
            
            self.save_test_result('database', error_result)
            self.log_error('Database', f'Test failed: {str(e)}')
            
            return error_result
    
    def test_api(self) -> Dict[str, Any]:
        """Test API endpoints and responses"""
        self.start_time = time.time()
        self.log_info('API', 'Starting API test')
        
        try:
            # Test GET requests
            get_success = self._test_get_requests()
            
            # Test POST requests
            post_success = self._test_post_requests()
            
            # Test authentication
            auth_success = self._test_authentication()
            
            # Test error handling
            error_handling = self._test_api_error_handling()
            
            execution_time = time.time() - self.start_time
            
            result = {
                'status': 'success' if all([get_success, post_success, auth_success, error_handling]) else 'error',
                'message': 'API test completed successfully',
                'details': [
                    f'GET requests: {"✓" if get_success else "✗"}',
                    f'POST requests: {"✓" if post_success else "✗"}',
                    f'Authentication: {"✓" if auth_success else "✗"}',
                    f'Error handling: {"✓" if error_handling else "✗"}'
                ],
                'execution_time': round(execution_time, 2),
                'metrics': {
                    'get': get_success,
                    'post': post_success,
                    'auth': auth_success,
                    'error_handling': error_handling
                }
            }
            
            self.save_test_result('api', result)
            self.log_info('API', f'Test completed in {execution_time:.2f} seconds')
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'API test failed: {str(e)}',
                'details': ['Error in test execution'],
                'execution_time': time.time() - self.start_time
            }
            
            self.save_test_result('api', error_result)
            self.log_error('API', f'Test failed: {str(e)}')
            
            return error_result
    
    def test_performance(self) -> Dict[str, Any]:
        """Test system performance and load testing"""
        self.start_time = time.time()
        self.log_info('Performance', 'Starting performance test')
        
        try:
            # Test load testing
            load_test_success = self._test_load_testing()
            
            # Test response time
            response_time_score = self._test_response_time_performance()
            
            # Test memory usage
            memory_usage_score = self._test_memory_usage()
            
            # Test CPU usage
            cpu_usage_score = self._test_cpu_usage()
            
            execution_time = time.time() - self.start_time
            
            overall_score = (load_test_success + response_time_score + memory_usage_score + cpu_usage_score) / 4
            
            result = {
                'status': 'success' if overall_score > 0.7 else 'error',
                'message': 'Performance test completed successfully',
                'details': [
                    f'Load testing: {"✓" if load_test_success else "✗"}',
                    f'Response time: {"✓" if response_time_score > 0.7 else "✗"}',
                    f'Memory usage: {"✓" if memory_usage_score > 0.7 else "✗"}',
                    f'CPU usage: {"✓" if cpu_usage_score > 0.7 else "✗"}'
                ],
                'execution_time': round(execution_time, 2),
                'metrics': {
                    'load_test': load_test_success,
                    'response_time': response_time_score,
                    'memory_usage': memory_usage_score,
                    'cpu_usage': cpu_usage_score,
                    'overall_score': overall_score
                }
            }
            
            self.save_test_result('performance', result)
            self.log_info('Performance', f'Test completed in {execution_time:.2f} seconds')
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'Performance test failed: {str(e)}',
                'details': ['Error in test execution'],
                'execution_time': time.time() - self.start_time
            }
            
            self.save_test_result('performance', error_result)
            self.log_error('Performance', f'Test failed: {str(e)}')
            
            return error_result
    
    def test_security(self) -> Dict[str, Any]:
        """Test security vulnerabilities and authentication"""
        self.start_time = time.time()
        self.log_info('Security', 'Starting security test')
        
        try:
            # Test authentication
            auth_success = self._test_security_authentication()
            
            # Test authorization
            authz_success = self._test_security_authorization()
            
            # Test SQL injection protection
            sql_injection_success = self._test_sql_injection_protection()
            
            # Test XSS protection
            xss_protection_success = self._test_xss_protection()
            
            execution_time = time.time() - self.start_time
            
            result = {
                'status': 'success' if all([auth_success, authz_success, sql_injection_success, xss_protection_success]) else 'error',
                'message': 'Security test completed successfully',
                'details': [
                    f'Authentication: {"✓" if auth_success else "✗"}',
                    f'Authorization: {"✓" if authz_success else "✗"}',
                    f'SQL injection: {"✓" if sql_injection_success else "✗"}',
                    f'XSS protection: {"✓" if xss_protection_success else "✗"}'
                ],
                'execution_time': round(execution_time, 2),
                'metrics': {
                    'authentication': auth_success,
                    'authorization': authz_success,
                    'sql_injection': sql_injection_success,
                    'xss_protection': xss_protection_success
                }
            }
            
            self.save_test_result('security', result)
            self.log_info('Security', f'Test completed in {execution_time:.2f} seconds')
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': f'Security test failed: {str(e)}',
                'details': ['Error in test execution'],
                'execution_time': time.time() - self.start_time
            }
            
            self.save_test_result('security', error_result)
            self.log_error('Security', f'Test failed: {str(e)}')
            
            return error_result
    
    # Helper methods for testing
    def _parse_resume_text(self, text: str) -> str:
        """Mock resume text parsing"""
        return text.strip() if text else ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Mock skill extraction"""
        skills = ['Python', 'JavaScript', 'SQL', 'Django', 'React', 'Node.js']
        found_skills = [skill for skill in skills if skill.lower() in text.lower()]
        return found_skills
    
    def _calculate_resume_score(self, skills: List[str]) -> float:
        """Mock resume score calculation"""
        base_score = 50
        skill_bonus = len(skills) * 5
        return min(100, base_score + skill_bonus)
    
    def _test_database_storage(self, text: str, score: float) -> bool:
        """Mock database storage test"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_results (test_type, status, message, details, execution_time)
                VALUES (?, ?, ?, ?, ?)
            ''', ('storage_test', 'success', 'Mock storage test', 0.1))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def _test_model_loading(self) -> bool:
        """Mock model loading test"""
        time.sleep(0.1)  # Simulate loading time
        return random.choice([True, True, True])  # 90% success rate
    
    def _test_prediction_accuracy(self) -> float:
        """Mock prediction accuracy test"""
        return random.uniform(0.75, 0.95)  # 75-95% accuracy
    
    def _test_response_time(self) -> float:
        """Mock response time test"""
        return random.uniform(0.5, 1.8)  # 0.5-1.8 seconds
    
    def _test_error_handling(self) -> bool:
        """Mock error handling test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_database_connection(self) -> bool:
        """Mock database connection test"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except Exception:
            return False
    
    def _test_crud_operations(self) -> bool:
        """Mock CRUD operations test"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create
            cursor.execute('CREATE TABLE IF NOT EXISTS test_crud (id INTEGER PRIMARY KEY, data TEXT)')
            
            # Read
            cursor.execute('SELECT COUNT(*) FROM test_crud')
            
            # Update
            cursor.execute('UPDATE test_crud SET data = ? WHERE id = 1', ('test_data',))
            
            # Delete
            cursor.execute('DELETE FROM test_crud WHERE id = 1')
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def _test_data_integrity(self) -> bool:
        """Mock data integrity test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_database_performance(self) -> float:
        """Mock database performance test"""
        return random.uniform(0.7, 0.95)  # 70-95% performance score
    
    def _test_get_requests(self) -> bool:
        """Mock GET request test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_post_requests(self) -> bool:
        """Mock POST request test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_authentication(self) -> bool:
        """Mock authentication test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_api_error_handling(self) -> bool:
        """Mock API error handling test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_load_testing(self) -> bool:
        """Mock load testing"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_response_time_performance(self) -> float:
        """Mock response time performance test"""
        return random.uniform(0.6, 0.95)  # 60-95% performance score
    
    def _test_memory_usage(self) -> float:
        """Mock memory usage test"""
        return random.uniform(0.65, 0.9)  # 65-90% performance score
    
    def _test_cpu_usage(self) -> float:
        """Mock CPU usage test"""
        return random.uniform(0.7, 0.9)  # 70-90% performance score
    
    def _test_security_authentication(self) -> bool:
        """Mock security authentication test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_security_authorization(self) -> bool:
        """Mock security authorization test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_sql_injection_protection(self) -> bool:
        """Mock SQL injection protection test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def _test_xss_protection(self) -> bool:
        """Mock XSS protection test"""
        return random.choice([True, True, True, False])  # 75% success rate
    
    def save_test_result(self, test_type: str, result: Dict[str, Any]):
        """Save test result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_results (test_type, status, message, details, execution_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                test_type,
                result['status'],
                result['message'],
                json.dumps(result['details']),
                result.get('execution_time', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_error('Database', f'Failed to save test result: {str(e)}')
    
    def get_test_results(self, test_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get test results from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if test_type:
                cursor.execute('''
                    SELECT * FROM test_results 
                    WHERE test_type = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (test_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM test_results 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                result['details'] = json.loads(result['details']) if result['details'] else []
                results.append(result)
            
            conn.close()
            return results
            
        except Exception as e:
            self.log_error('Database', f'Failed to get test results: {str(e)}')
            return []
    
    def clear_test_results(self, test_type: str = None):
        """Clear test results from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if test_type:
                cursor.execute('DELETE FROM test_results WHERE test_type = ?', (test_type,))
            else:
                cursor.execute('DELETE FROM test_results')
            
            conn.commit()
            conn.close()
            
            self.log_info('Database', f'Cleared test results for {test_type or "all tests"}')
            
        except Exception as e:
            self.log_error('Database', f'Failed to clear test results: {str(e)}')


def main():
    """Main function to run mock tests"""
    backend = MockTestBackend()
    
    print("🧪 Mock Test Backend Started")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ('Resume Analysis', backend.test_resume_analysis),
        ('AI Model', backend.test_ai_model),
        ('Database', backend.test_database),
        ('API', backend.test_api),
        ('Performance', backend.test_performance),
        ('Security', backend.test_security)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        result = test_func()
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Execution Time: {result['execution_time']:.2f}s")
        print("   Details:")
        for detail in result['details']:
            print(f"     • {detail}")
    
    print("\n" + "=" * 50)
    print("✅ All Mock Tests Completed!")
    print(f"📊 Results saved to: {backend.db_path}")
    
    return backend


if __name__ == "__main__":
    main()
