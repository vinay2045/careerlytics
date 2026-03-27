"""
Comprehensive Mock Test System Views
Handles role-based and language-based mock tests with multi-step selection flow
"""

import json
import random
import os
import re
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from resumeanalysis.models import Role, MockTest, Language, TestAttempt, MockTestXP
from users.models import UserRegistration
from users.utils import get_user_registration

# Test configuration data
ROLE_TESTS = {
    'frontend': [
        {
            'name': 'HTML & CSS Basics',
            'file': 'frontend_html_css.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Beginner',
            'description': 'Test your knowledge of HTML5 and CSS3 fundamentals'
        },
        {
            'name': 'JavaScript Core',
            'file': 'frontend_js_core.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Intermediate',
            'description': 'Core JavaScript concepts, ES6+, and DOM manipulation'
        },
        {
            'name': 'React Framework',
            'file': 'frontend_react.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Advanced',
            'description': 'Advanced React patterns, hooks, and state management'
        }
    ],
    'backend': [
        {
            'name': 'Python & Django',
            'file': 'backend_python_django.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Intermediate',
            'description': 'Python programming and Django web framework concepts'
        },
        {
            'name': 'Database Design',
            'file': 'backend_db_design.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Advanced',
            'description': 'SQL, normalization, and database architecture'
        },
        {
            'name': 'API Development',
            'file': 'backend_api_dev.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Intermediate',
            'description': 'RESTful APIs, authentication, and backend architecture'
        }
    ],
    'fullstack': [
        {
            'name': 'Web Architecture',
            'file': 'fullstack_web_arch.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Advanced',
            'description': 'End-to-end web application architecture and deployment'
        },
        {
            'name': 'System Design',
            'file': 'fullstack_system_design.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Expert',
            'description': 'Scalable system design and microservices patterns'
        }
    ],
    'devops': [
        {
            'name': 'Docker & Kubernetes',
            'file': 'devops_docker_k8s.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Advanced',
            'description': 'Containerization and orchestration concepts'
        },
        {
            'name': 'CI/CD Pipelines',
            'file': 'devops_cicd.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Intermediate',
            'description': 'Continuous Integration and Deployment workflows'
        }
    ],
    'datascience': [
        {
            'name': 'Python for Data Science',
            'file': 'ds_python.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Intermediate',
            'description': 'Pandas, NumPy, and data manipulation'
        },
        {
            'name': 'Machine Learning Basics',
            'file': 'ds_ml_basics.txt',
            'questions': 30,
            'time': 30,
            'difficulty': 'Advanced',
            'description': 'Supervised and unsupervised learning algorithms'
        }
    ]
}

LANGUAGE_TESTS = {
    'python': [
        {
            'name': 'Mock Test 1',
            'file': 'python_fundamentals.json',
            'description': 'Python syntax, data types, and core concepts',
            'difficulty': 'Beginner',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'Mock Test 2',
            'file': 'python_advanced.txt',
            'description': 'Advanced Python features, decorators, and metaprogramming',
            'difficulty': 'Advanced',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'Mock Test 3',
            'file': 'python_web.txt',
            'description': 'Flask, Django, and web frameworks',
            'difficulty': 'Intermediate',
            'time': 30,
            'questions': 30
        }
    ],
    'java': [
        {
            'name': 'Java Core Programming',
            'file': 'java_core.json',
            'description': 'Java fundamentals, OOP, and core libraries',
            'difficulty': 'Intermediate',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'Java Spring Framework',
            'file': 'java_spring.txt',
            'description': 'Spring Boot, dependency injection, and enterprise Java',
            'difficulty': 'Advanced',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'Java Concurrency',
            'file': 'java_concurrency.txt',
            'description': 'Multithreading, concurrency, and performance',
            'difficulty': 'Advanced',
            'time': 30,
            'questions': 30
        }
    ],
    'javascript': [
        {
            'name': 'JavaScript ES6+',
            'file': 'javascript_es6.json',
            'description': 'Modern JavaScript features, ES6+, and async programming',
            'difficulty': 'Intermediate',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'Node.js & Express',
            'file': 'javascript_nodejs.txt',
            'description': 'Server-side JavaScript and Express framework',
            'difficulty': 'Intermediate',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'React & Frontend',
            'file': 'javascript_react.txt',
            'description': 'React, hooks, and modern frontend development',
            'difficulty': 'Advanced',
            'time': 30,
            'questions': 30
        }
    ],
    'cpp': [
        {
            'name': 'C++ STL',
            'file': 'cpp_stl.json',
            'description': 'Standard Template Library, containers, and algorithms',
            'difficulty': 'Intermediate',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'C++ Advanced',
            'file': 'cpp_advanced.txt',
            'description': 'Advanced C++, templates, and performance optimization',
            'difficulty': 'Advanced',
            'time': 30,
            'questions': 30
        },
        {
            'name': 'C++ System Programming',
            'file': 'cpp_system.txt',
            'description': 'System programming, memory management, and low-level concepts',
            'difficulty': 'Advanced',
            'time': 30,
            'questions': 30
        }
    ]
}

def get_user_progress(request):
    """Helper function to get user progress for context"""
    progress = {
        'current_level': 1,
        'total_xp': 0,
        'xp_progress': 0,
        'xp_threshold': 1000,
        'progress_percentage': 0,
        'next_level': 2,
        'xp_needed': 1000
    }
    
    userid = None
    if 'username' in request.session:
        userid = request.session['username']
    elif 'userid' in request.session:
        userid = request.session['userid']
    elif request.user.is_authenticated:
        userid = request.user.username
        
    if userid:
        try:
            # Use UserRegistration to get the correct userid if needed
            user_reg = UserRegistration.objects.filter(userid=userid).first()
            if user_reg:
                xp_obj, created = MockTestXP.objects.get_or_create(user_id=user_reg.userid)
                progress['total_xp'] = xp_obj.total_xp
                progress['current_level'] = xp_obj.current_level
                progress['next_level'] = xp_obj.current_level + 1
                progress['xp_progress'] = xp_obj.total_xp % progress['xp_threshold']
                progress['progress_percentage'] = (progress['xp_progress'] / progress['xp_threshold']) * 100
                progress['xp_needed'] = progress['xp_threshold'] - progress['xp_progress']
        except Exception as e:
            print(f"Error fetching MockTestXP in get_user_progress: {e}")
            
    return progress

def mock_test_index(request):
    """Main mock test selection page"""
    context = {}
    
    # Add progress context
    context.update(get_user_progress(request))
    
    if 'username' in request.session:
        try:
            user = UserRegistration.objects.get(userid=request.session['username'])
            context['user'] = user
        except UserRegistration.DoesNotExist:
            pass
    return render(request, 'mock_test/index.html', context)

def role_selection(request):
    """Role selection page"""
    roles_qs = Role.objects.filter(is_active=True).order_by('id')
    roles = []
    
    for r in roles_qs:
        roles.append({
            'name': r.name,
            'key': r.key,
            'description': r.description,
            'icon': r.icon,
            'color': r.color,
            'test_count': r.tests.count()
        })
    
    context = {'roles': roles}
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
            
    return render(request, 'mock_test/roles/index.html', context)

def role_test_list(request, role):
    """Role-specific test list page"""
    # Check if role exists in DB
    role_obj = Role.objects.filter(key=role).first()
    if not role_obj:
        return render(request, 'mock_test/404.html')
    
    # Get tests for this role
    tests = MockTest.objects.filter(role=role_obj).order_by('id')
    
    context = {
        'role': role_obj,
        'tests': tests
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
    
    return render(request, 'mock_test/roles/detail.html', context)

def language_selection(request):
    """Language selection page"""
    languages_qs = Language.objects.filter(is_active=True).order_by('id')
    languages = []
    
    for l in languages_qs:
        languages.append({
            'name': l.name,
            'key': l.key,
            'description': l.description,
            'icon': l.icon,
            'color': l.color,
            'test_count': l.tests.count()
        })
            
    context = {'languages': languages}
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
            
    return render(request, 'mock_test/languages/index.html', context)

def language_test_list(request, language):
    """Language-specific test list page"""
    # Check if language exists in DB
    lang_obj = Language.objects.filter(key=language).first()
    if not lang_obj:
        return render(request, 'mock_test/404.html')
    
    # Get tests for this language
    tests = MockTest.objects.filter(language=lang_obj).order_by('id')
    
    context = {
        'language': lang_obj,
        'tests': tests
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
    
    return render(request, 'mock_test/languages/detail.html', context)

def test_variations(request, test_type, category, test_index):
    """Display variations (Mock Test 1, 2) for a selected test topic"""
    if test_type == 'role':
        role = Role.objects.filter(key=category).first()
        if not role:
            return render(request, 'mock_test/404.html')
        tests_qs = MockTest.objects.filter(role=role).order_by('id')
    elif test_type == 'language':
        lang = Language.objects.filter(key=category).first()
        if not lang:
            return render(request, 'mock_test/404.html')
        tests_qs = MockTest.objects.filter(language=lang).order_by('id')
    elif test_type == 'softskill':
        # Hardcoded soft skills test info for variations
        test_obj = type('Test', (), {
            'id': 0,
            'name': 'Communication & Leadership',
            'questions_count': 50,
            'time_limit': 45,
            'difficulty': 'Intermediate',
            'description': 'Master the essential interpersonal skills for professional success.'
        })
        tests_qs = [test_obj] # Mock queryset behavior
    elif test_type == 'core':
        assessment_details = {
            'aptitude': {
                'name': 'Aptitude Modules',
                'description': 'Select a module to evaluate your quantitative aptitude, logical reasoning, and problem-solving skills.',
                'icon': 'psychology',
                'color': 'blue',
                'skills': ['Quantitative Aptitude', 'Logical Reasoning', 'Problem Solving', 'Data Interpretation']
            },
            'reasoning': {
                'name': 'Logical Reasoning',
                'description': 'Master critical thinking and logical deduction patterns common in recruitment tests.',
                'icon': 'account_tree',
                'color': 'purple',
                'skills': ['Deductive Reasoning', 'Pattern Recognition', 'Syllogisms', 'Analytical Thinking']
            },
            'verbal': {
                'name': 'Verbal Ability',
                'description': 'Enhance your grammar, vocabulary, and reading comprehension for effective communication.',
                'icon': 'translate',
                'color': 'emerald',
                'skills': ['Grammar', 'Vocabulary', 'Reading Comprehension', 'Sentence Correction']
            }
        }
        
        detail = assessment_details.get(category)
        if not detail:
            return render(request, 'mock_test/404.html')
            
        test_obj = type('Test', (), {
            'id': f"core_{category}_{test_index}",
            'name': f"{detail['name']} - Module {int(test_index) + 1}",
            'questions_count': 30,
            'time_limit': 30,
            'difficulty': 'Intermediate',
            'description': detail['description']
        })
        tests_qs = [test_obj]
    else:
        return render(request, 'mock_test/404.html')

    try:
        test_index = int(test_index)
        if test_type in ['softskill', 'core']:
            test_obj = tests_qs[0]
        elif test_index < 0 or test_index >= tests_qs.count():
            return render(request, 'mock_test/404.html')
        else:
            test_obj = tests_qs[test_index]
    except (ValueError, IndexError):
        return render(request, 'mock_test/404.html')

    # Get user attempts for THIS specific test
    highest_score = 0
    attempts_count = 0
    latest_attempt_id = None

    user_id = None
    if request.user.is_authenticated:
        user_id = request.user.username
    elif 'userid' in request.session:
        user_id = request.session['userid']
    elif 'username' in request.session:
        user_id = request.session['username']

    if user_id:
        try:
            user = UserRegistration.objects.get(userid=user_id)
            
            # Get completion status for THIS specific test
            if test_type == 'core':
                # For core assessments, check based on category and module_index
                mod1_completed = TestAttempt.objects.filter(
                    user=user, 
                    test_type='core', 
                    category=category, 
                    module_index=0, 
                    status='completed'
                ).exists()
                
                mod2_completed = TestAttempt.objects.filter(
                    user=user, 
                    test_type='core', 
                    category=category, 
                    module_index=1, 
                    status='completed'
                ).exists()
                
                mod2_unlocked = mod1_completed
                attempts_count = (1 if mod1_completed else 0) + (1 if mod2_completed else 0)
                
                print(f"DEBUG: Variations view (CORE) - User: {user_id}, Category: {category}, Mod1: {mod1_completed}, Mod2: {mod2_completed}")
            else:
                # Important: role_id in TestAttempt stores MockTest.id
                attempts = TestAttempt.objects.filter(user=user, role_id=test_obj.id if test_obj else 0, status='completed')
                attempts_count = attempts.count()
                
                if attempts.exists():
                    latest_attempt = attempts.order_by('-completed_at').first()
                    highest_score = attempts.order_by('-total_score').first().total_score
                    latest_attempt_id = latest_attempt.id
                
                mod1_completed = attempts_count >= 1
                mod2_completed = attempts_count >= 2
                mod2_unlocked = attempts_count >= 1
                
                print(f"DEBUG: Variations view - User: {user_id}, Test: {test_obj.id if test_obj else 'N/A'}, Attempts found: {attempts_count}")
        except Exception as e:
            print(f"DEBUG: Error fetching attempts in variations: {e}")
            mod1_completed = False
            mod2_completed = False
            mod2_unlocked = False
    else:
        print("DEBUG: No user_id found in session or request for variations view")
        mod1_completed = False
        mod2_completed = False
        mod2_unlocked = False

    context = {
        'test': test_obj,
        'test_type': test_type,
        'category': category,
        'test_index': test_index,
        'latest_attempt_id': latest_attempt_id,
        'total_xp_reward': test_obj.questions_count * 25 if test_obj else 750,
        'variations': [
            {
                'name': f'Module 1' if test_type == 'core' else 'Mock Test 1', 
                'description': f'Foundation level assessment of {test_obj.name if test_obj else category.title()}.',
                'xp_reward': 500,
                'available': True,
                'completed': mod1_completed,
                'required_level': 1,
                'test_index': 0 if test_type == 'core' else test_index
            },
            {
                'name': f'Module 2' if test_type == 'core' else 'Mock Test 2', 
                'description': f'Intermediate scenarios testing deeper understanding.',
                'xp_reward': 750,
                'available': mod2_unlocked,
                'completed': mod2_completed,
                'required_level': 1,
                'test_index': 1 if test_type == 'core' else test_index
            }
        ]
    }
    
    # Only add 3rd variation for non-core tests
    if test_type != 'core':
        context['variations'].append({
            'name': 'Mock Test 3', 
            'description': 'Advanced professional level assessment.',
            'xp_reward': 1000,
            'available': attempts_count >= 2,
            'completed': attempts_count >= 3,
            'required_level': 1
        })
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
    return render(request, 'mock_test/variations.html', context)

def start_exam(request, test_type, category, test_index):
    """Universal exam starter"""
    try:
        # Validate test type and category
        if test_type == 'role':
            role = Role.objects.filter(key=category).first()
            if not role:
                return JsonResponse({'status': 'error', 'message': 'Invalid role'}, status=400)
            
            tests_qs = MockTest.objects.filter(role=role).order_by('id')
            try:
                test_index = int(test_index)
                if test_index < 0 or test_index >= tests_qs.count():
                    return JsonResponse({'status': 'error', 'message': 'Invalid test index'}, status=400)
                test_obj = tests_qs[test_index]
                
                test_info = {
                    'name': test_obj.name,
                    'file': test_obj.file_name,
                    'questions': test_obj.questions_count,
                    'time': test_obj.time_limit,
                    'difficulty': test_obj.difficulty,
                    'description': test_obj.description
                }
            except (ValueError, IndexError):
                 return JsonResponse({'status': 'error', 'message': 'Invalid test index'}, status=400)
        
        elif test_type == 'softskill':
            # Hardcoded soft skills test info for now
            test_info = {
                'name': 'Communication & Leadership',
                'file': 'jamai/jamai_1.json',
                'questions': 50,
                'time': 45,
                'difficulty': 'Intermediate',
                'description': 'Master the essential interpersonal skills for professional success.'
            }
            test_index = 0

        elif test_type == 'language':
            lang = Language.objects.filter(key=category).first()
            if not lang:
                return JsonResponse({'status': 'error', 'message': 'Invalid language'}, status=400)
            
            tests_qs = MockTest.objects.filter(language=lang).order_by('id')
            try:
                test_index = int(test_index)
                if test_index < 0 or test_index >= tests_qs.count():
                    return JsonResponse({'status': 'error', 'message': 'Invalid test index'}, status=400)
                test_obj = tests_qs[test_index]
                
                test_info = {
                    'name': test_obj.name,
                    'file': test_obj.file_name,
                    'questions': test_obj.questions_count,
                    'time': test_obj.time_limit,
                    'difficulty': test_obj.difficulty,
                    'description': test_obj.description
                }
            except (ValueError, IndexError):
                return JsonResponse({'status': 'error', 'message': 'Invalid test index'}, status=400)
        elif test_type == 'core':
            # Handle core assessment modules
            assessment_files = {
                'aptitude': ['aptitude_1.json', 'aptitude_2.json'],
                'reasoning': ['reasoning_1.json', 'reasoning_2.json'],
                'verbal': ['verbal_1.json', 'verbal_2.json']
            }
            
            files = assessment_files.get(category)
            if not files:
                return JsonResponse({'status': 'error', 'message': 'Invalid core category'}, status=400)
                
            try:
                test_index = int(test_index)
                if test_index < 0 or test_index >= len(files):
                    return JsonResponse({'status': 'error', 'message': 'Invalid core test index'}, status=400)
                    
                filename = files[test_index]
                test_info = {
                    'name': f"{category.title()} Module {test_index + 1}",
                    'file': filename,
                    'questions': 30,
                    'time': 30,
                    'difficulty': 'Intermediate',
                    'description': f'Assessment for {category.title()} - Module {test_index + 1}'
                }
            except (ValueError, IndexError):
                return JsonResponse({'status': 'error', 'message': 'Invalid test index'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid test type'}, status=400)
        
        # Load questions
        if test_type == 'softskill':
             questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'questions', 
                                     'jamai', test_info['file'])
        elif test_type == 'core':
            questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'questions', 
                                     'Core Assessment Areas', test_info['file'])
        else:
            questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'questions', 
                                     test_type + 's', category, test_info['file'])
        
        if not os.path.exists(questions_file):
            # Create sample questions if file doesn't exist
            questions = generate_sample_questions(test_info['questions'])
        else:
            with open(questions_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if questions_file.endswith('.json'):
                try:
                    questions_json = json.loads(content)
                    questions = []
                    for q in questions_json:
                        questions.append({
                            'question': q.get('question_text', ''),
                            'options': q.get('options', []),
                            'correct': q.get('correct_answer', 0)
                        })
                except json.JSONDecodeError:
                     questions = generate_sample_questions(test_info['questions'])
            else:
                questions = parse_questions(content)
        
        # Shuffle and limit questions
        random.shuffle(questions)
        limited_questions = questions[:test_info['questions']]
        
        # Store test info in session
        request.session['current_test'] = {
            'type': test_type,
            'category': category,
            'test_index': test_index,
            'info': test_info,
            'questions': limited_questions,
            'start_time': None
        }
        
        # Log session test data
        print(f"DEBUG: start_exam - Session initialized for {test_type} / {category} / Module {test_index}")
        
        # Clear any existing attempt ID to ensure a fresh attempt is created for the new test
        if 'current_attempt_id' in request.session:
            del request.session['current_attempt_id']
        
        # Ensure session is saved
        request.session.modified = True
        
        return JsonResponse({
            'status': 'success',
            'test_info': test_info,
            'questions': limited_questions,
            'total_questions': len(limited_questions)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to start exam: {str(e)}'
        }, status=500)

def generate_sample_questions(count):
    """Generate sample questions for testing"""
    sample_questions = [
        "What is the primary purpose of this technology?",
        "Which of the following best describes this concept?",
        "How would you implement this feature?",
        "What are the benefits of this approach?",
        "Which design pattern is most appropriate here?"
    ]
    
    questions = []
    for i in range(count):
        q = sample_questions[i % len(sample_questions)]
        questions.append({
            'question': f"{i+1}. {q}",
            'options': [
                "Option A: Correct answer",
                "Option B: Incorrect answer", 
                "Option C: Incorrect answer",
                "Option D: Incorrect answer"
            ],
            'correct': 0
        })
    
    return questions

def parse_questions(content):
    """Parse questions from text file"""
    questions = []
    lines = content.split('\n')
    current_question = None
    
    for line in lines:
        line = line.strip()
        
        if not line or line.startswith('View Answer') or line.startswith('Explanation:'):
            continue
            
        if re.match(r'^\d+\.\s*', line):
            if current_question and current_question['question'] and current_question['options']:
                questions.append(current_question)
            
            question_text = re.sub(r'^\d+\.\s*', '', line)
            current_question = {
                'question': question_text,
                'options': [],
                'correct': None
            }
            
        elif re.match(r'^[a-dA-D]\)\s*', line) or re.match(r'^[+-]\s*', line):
            if current_question:
                option_text = re.sub(r'^[a-dA-D]\)\s*', '', line).strip()
                option_text = re.sub(r'^[+-]\s*', '', option_text).strip()
                current_question['options'].append(option_text)
                
        elif line.lower().startswith('correct answer:') or line.lower().startswith('answer:'):
            if current_question:
                answer_text = re.sub(r'.*correct answer:\s*', '', line, flags=re.IGNORECASE)
                answer_text = re.sub(r'.*answer:\s*', '', answer_text, flags=re.IGNORECASE)
                answer_text = answer_text.strip().upper()
                
                if answer_text == 'A':
                    current_question['correct'] = 0
                elif answer_text == 'B':
                    current_question['correct'] = 1
                elif answer_text == 'C':
                    current_question['correct'] = 2
                elif answer_text == 'D':
                    current_question['correct'] = 3
                elif answer_text.isdigit():
                    current_question['correct'] = int(answer_text) - 1
    
    if current_question and current_question['question'] and current_question['options']:
        questions.append(current_question)
    
    return questions

@csrf_exempt
@require_http_methods(["POST"])
def save_exam_progress(request):
    """Save exam progress in real-time"""
    try:
        data = json.loads(request.body)
        question_index = data.get('question_index')
        selected_answer = data.get('selected_answer')
        
        user_id = request.session.get('username') or request.session.get('userid')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)
            
        user = UserRegistration.objects.get(userid=user_id)
        current_test = request.session.get('current_test')
        
        if not current_test:
            return JsonResponse({'status': 'error', 'message': 'No active test found'}, status=400)
            
        # Get or create TestAttempt for this session
        attempt_id = request.session.get('current_attempt_id')
        attempt = None
        
        if attempt_id:
            attempt = TestAttempt.objects.filter(id=attempt_id, user=user).first()
            
        if not attempt:
            # Need to find the test_obj first
            test_type = current_test.get('type')
            category = current_test.get('category')
            test_index = current_test.get('test_index')
            
            test_obj = None
            if test_type == 'role':
                role = Role.objects.filter(key=category).first()
                if role:
                    tests_qs = MockTest.objects.filter(role=role).order_by('id')
                    if 0 <= test_index < tests_qs.count():
                        test_obj = tests_qs[test_index]
            elif test_type == 'language':
                lang = Language.objects.filter(key=category).first()
                if lang:
                    tests_qs = MockTest.objects.filter(language=lang).order_by('id')
                    if 0 <= test_index < tests_qs.count():
                        test_obj = tests_qs[test_index]
            elif test_type == 'softskill':
                # Handle softskills differently since it might not be in MockTest model yet
                # We can still create an attempt with role_id=0 or similar
                pass

            total_questions = len(current_test.get('questions', []))
            time_limit = current_test.get('info', {}).get('time', 30)
            
            attempt = TestAttempt.objects.create(
                user=user,
                role_id=test_obj.id if test_obj else 0,
                total_questions=total_questions,
                time_limit=time_limit,
                status='in_progress',
                total_score=0,
                questions_answered=0,
                questions_correct=0,
                xp_earned=0
            )
            request.session['current_attempt_id'] = str(attempt.id)
            request.session.modified = True

        # Save the answer
        questions = current_test.get('questions', [])
        if 0 <= question_index < len(questions):
            question = questions[question_index]
            
            from resumeanalysis.models import TestAnswer
            correct_answer = question.get('correct')
            is_correct = selected_answer == correct_answer
            
            # Update or create answer
            TestAnswer.objects.update_or_create(
                test_attempt=attempt,
                question_id=f"q_{question_index + 1}",
                defaults={
                    'question_category': current_test.get('type'),
                    'question_text': question['question'],
                    'question_options': question['options'],
                    'correct_answer': correct_answer if correct_answer is not None else -1,
                    'selected_answer': selected_answer if selected_answer is not None else -1,
                    'is_correct': is_correct
                }
            )
            
            # Update attempt progress
            answered_count = TestAnswer.objects.filter(test_attempt=attempt).count()
            correct_count = TestAnswer.objects.filter(test_attempt=attempt, is_correct=True).count()
            
            attempt.questions_answered = answered_count
            attempt.questions_correct = correct_count
            # Update score as percentage of progress so far
            if total_questions := len(questions):
                attempt.total_score = int((correct_count / total_questions) * 100)
            attempt.save()
            
            return JsonResponse({'status': 'success', 'attempt_id': str(attempt.id)})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid question index'}, status=400)
            
    except Exception as e:
        import traceback
        print(f"DEBUG: save_exam_progress error: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submit_exam(request):
    """Universal exam submission"""
    try:
        # Try to parse JSON from body first
        try:
            data = json.loads(request.body)
            user_answers_raw = data.get('answers', data.get('user_answers', []))
            questions = data.get('questions', [])
            time_taken = data.get('time_taken', 0)
            test_type = data.get('test_type')
            category = data.get('category')
            test_index = data.get('test_index')
        except (json.JSONDecodeError, AttributeError):
            # Fallback to POST parameters
            user_answers_raw = request.POST.get('user_answers', '[]')
            if isinstance(user_answers_raw, str):
                try:
                    user_answers_raw = json.loads(user_answers_raw)
                except:
                    user_answers_raw = []
            
            questions = request.POST.get('questions', '[]')
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                except:
                    questions = []
            
            time_taken = request.POST.get('time_taken', 0)
            test_type = request.POST.get('test_type')
            category = request.POST.get('category')
            test_index = request.POST.get('test_index')

        # If questions are not provided in request, try to get them from session
        if not questions:
            current_test = request.session.get('current_test')
            if current_test:
                questions = current_test.get('questions', [])
                test_type = test_type or current_test.get('type')
                category = category or current_test.get('category')
                test_index = test_index or current_test.get('test_index')
        
        if not questions:
            return JsonResponse({'status': 'error', 'message': 'No questions provided for evaluation'}, status=400)
        
        # Standardize user_answers to a list or dict
        # If it's a dict like {"0": 1, "1": 0}, convert to list or handle appropriately
        user_answers = []
        if isinstance(user_answers_raw, dict):
            # Convert dict indices to list
            max_idx = -1
            for k in user_answers_raw.keys():
                try:
                    max_idx = max(max_idx, int(k))
                except ValueError: pass
            
            user_answers = [None] * (max_idx + 1)
            for k, v in user_answers_raw.items():
                try:
                    user_answers[int(k)] = v
                except ValueError: pass
        else:
            user_answers = user_answers_raw

        # Calculate results
        correct_count = 0
        total_questions = len(questions)
        results = []
        
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
                
            user_answer = user_answers[i] if i < len(user_answers) else None
            
            # Handle different question formats
            correct_answer = question.get('correct')
            if correct_answer is None:
                correct_answer = question.get('correct_answer')
            if correct_answer is None:
                correct_answer = question.get('answer')
                
            is_correct = False
            if user_answer is not None and correct_answer is not None:
                is_correct = str(user_answer) == str(correct_answer)
            
            if is_correct:
                correct_count += 1
            
            question_text = question.get('question', question.get('question_text', 'Unknown Question'))
            
            results.append({
                'question_number': i + 1,
                'question': question_text,
                'options': question.get('options', []),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
        
        # Calculate percentage
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Determine performance level
        if percentage >= 90:
            performance = "Excellent"
            message = "Outstanding performance! You have mastered this topic."
        elif percentage >= 80:
            performance = "Good"
            message = "Good job! You have solid understanding of this topic."
        elif percentage >= 70:
            performance = "Average"
            message = "Fair performance. Consider reviewing some concepts."
        elif percentage >= 60:
            performance = "Below Average"
            message = "Keep practicing! Focus on the fundamentals."
        else:
            performance = "Needs Improvement"
            message = "Additional study recommended. Review the basics thoroughly."
        
        # Store results in session
        request.session['test_results'] = {
            'total_questions': total_questions,
            'correct_answers': correct_count,
            'wrong_answers': total_questions - correct_count,
            'percentage': round(percentage, 2),
            'performance_level': performance,
            'message': message,
            'detailed_results': results
        }
        
        # Save to database if user is logged in
        user_id = request.session.get('username') or request.session.get('userid')
        if user_id:
            try:
                user = UserRegistration.objects.get(userid=user_id)
                current_test = request.session.get('current_test')
                
                if current_test:
                    test_type = current_test.get('type')
                    category = current_test.get('category')
                    test_index = current_test.get('test_index')
                    
                    print(f"DEBUG: submit_exam - Processing test: {test_type}, category: {category}, index: {test_index}")
                    
                    test_obj = None
                    if test_type == 'role':
                        role = Role.objects.filter(key=category).first()
                        if role:
                            tests_qs = MockTest.objects.filter(role=role).order_by('id')
                            if 0 <= test_index < tests_qs.count():
                                test_obj = tests_qs[test_index]
                    elif test_type == 'language':
                        lang = Language.objects.filter(key=category).first()
                        if lang:
                            tests_qs = MockTest.objects.filter(language=lang).order_by('id')
                            if 0 <= test_index < tests_qs.count():
                                test_obj = tests_qs[test_index]
                    elif test_type == 'core':
                        # For core assessments, we don't have a MockTest object
                        # We use the category and module index directly
                        test_obj = None
                    
                    # Calculate XP earned (Base 500 XP for perfect score)
                    xp_earned = int((percentage / 100) * 500)
                    
                    # Check for existing attempt from real-time progress saving
                    attempt_id = request.session.get('current_attempt_id')
                    attempt = None
                    if attempt_id:
                        attempt = TestAttempt.objects.filter(id=attempt_id, user=user).first()
                    
                    if attempt:
                        # Update existing attempt
                        attempt.status = 'completed'
                        attempt.completed_at = timezone.now()
                        attempt.total_score = int(percentage)
                        attempt.questions_answered = len(user_answers)
                        attempt.questions_correct = correct_count
                        attempt.xp_earned = xp_earned
                        # For core tests, update these fields if they were missing
                        if test_type == 'core':
                            attempt.test_type = 'core'
                            attempt.category = category
                            attempt.module_index = test_index
                        attempt.save()
                    else:
                        # Create new attempt if not found
                        attempt = TestAttempt.objects.create(
                            user=user,
                            role_id=test_obj.id if test_obj else 0,
                            test_type=test_type,
                            category=category if test_type == 'core' else None,
                            module_index=test_index if test_type == 'core' else None,
                            total_questions=total_questions,
                            time_limit=test_obj.time_limit if test_obj else 30,
                            status='completed',
                            completed_at=timezone.now(),
                            total_score=int(percentage),
                            questions_answered=len(user_answers),
                            questions_correct=correct_count,
                            xp_earned=xp_earned
                        )
                    
                    print(f"DEBUG: submit_exam - Attempt {attempt.id} marked as completed")

                    # Save individual answers
                    from resumeanalysis.models import TestAnswer
                    for i, res in enumerate(results):
                        TestAnswer.objects.update_or_create(
                            test_attempt=attempt,
                            question_id=f"q_{i+1}",
                            defaults={
                                'question_category': test_type,
                                'question_text': res['question'],
                                'question_options': res['options'],
                                'correct_answer': res['correct_answer'] if res['correct_answer'] is not None else -1,
                                'selected_answer': res['user_answer'] if res['user_answer'] is not None else -1,
                                'is_correct': res['is_correct']
                            }
                        )
                    
                    # Clear attempt from session after successful submission
                    if 'current_attempt_id' in request.session:
                        del request.session['current_attempt_id']
                    
                    # Update MockTestXP
                    try:
                        xp_obj, created = MockTestXP.objects.get_or_create(user_id=user.userid)
                        xp_obj.update_progress(xp_earned)
                    except Exception as e:
                        print(f"Error updating MockTestXP: {e}")

                    # Force session update to reflect latest attempt
                    request.session.modified = True
                
                # Check for personalized plan assessment
                elif request.session.get('personalized_plan_data'):
                    # Save attempt for personalized plan assessment
                    attempt = TestAttempt.objects.create(
                        user=user,
                        role_id=0, # Conventional ID for personalized assessment
                        total_questions=total_questions,
                        time_limit=30, # Default time limit
                        status='completed',
                        completed_at=timezone.now(),
                        total_score=int(percentage),
                        questions_answered=len(user_answers),
                        questions_correct=correct_count,
                        xp_earned=int((percentage / 100) * 500)
                    )

                    # Save individual answers
                    from resumeanalysis.models import TestAnswer
                    for i, res in enumerate(results):
                        TestAnswer.objects.create(
                            test_attempt=attempt,
                            question_id=f"q_{i+1}",
                            question_category='personalized_assessment',
                            question_text=res['question'],
                            question_options=res['options'],
                            correct_answer=res['correct_answer'] if res['correct_answer'] is not None else -1,
                            selected_answer=res['user_answer'] if res['user_answer'] is not None else -1,
                            is_correct=res['is_correct']
                        )
            except Exception as e:
                print(f"Error saving test attempt: {e}")
        
        return JsonResponse({
            'status': 'success',
            'results': {
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'wrong_answers': total_questions - correct_count,
                'percentage': round(percentage, 2),
                'performance_level': performance,
                'message': message,
                'detailed_results': results
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to submit exam: {str(e)}'
        }, status=500)

def softskills_selection(request):
    """Jamai selection page"""
    context = {
        'jamai': [
            {
                'name': 'Soft Skills Fundamentals',
                'key': 'jamai',
                'description': 'Comprehensive assessment of communication, leadership, and emotional intelligence.',
                'icon': 'diversity_3',
                'color': 'purple',
                'test_count': 1
            }
        ]
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
            
    return render(request, 'mock_test/jamai/index.html', context)

def softskills_test_list(request):
    """Jamai test list page"""
    context = {
        'category_name': 'Jamai',
        'tests': [
            {
                'id': 0,
                'name': 'Communication & Leadership',
                'file_name': 'jamai/jamai_1.json',
                'questions_count': 50,
                'time_limit': 45,
                'difficulty': 'Intermediate',
                'description': 'Master the essential interpersonal skills for professional success.'
            }
        ]
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
    
    return render(request, 'mock_test/jamai/detail.html', context)

def exam_results(request):
    """Universal exam results page"""
    # Check if a specific attempt ID is provided
    attempt_id = request.GET.get('attempt_id')
    results = None

    user = get_user_registration(request)
    if attempt_id and user:
        try:
            attempt = TestAttempt.objects.filter(user=user, id=attempt_id, status='completed').first()
            if attempt:
                # Load detailed results from TestAnswer
                from resumeanalysis.models import TestAnswer
                answers = TestAnswer.objects.filter(test_attempt=attempt).order_by('id')
                detailed_results = []
                for i, ans in enumerate(answers):
                    detailed_results.append({
                        'question_number': i + 1,
                        'question': ans.question_text,
                        'options': ans.question_options,
                        'user_answer': ans.selected_answer if ans.selected_answer != -1 else None,
                        'correct_answer': ans.correct_answer if ans.correct_answer != -1 else None,
                        'is_correct': ans.is_correct
                    })

                results = {
                    'total_questions': attempt.total_questions,
                    'correct_answers': attempt.questions_correct,
                    'wrong_answers': attempt.total_questions - attempt.questions_correct,
                    'percentage': attempt.total_score,
                    'performance_level': "Review Result",
                    'message': f"Result from {attempt.completed_at.strftime('%Y-%m-%d %H:%M')}",
                    'detailed_results': detailed_results
                }
        except Exception as e:
            print(f"Error fetching specific attempt: {e}")

    if not results:
        results = request.session.get('test_results')
    
    # If no results in session, try to get the latest attempt from DB
    if not results:
        user = get_user_registration(request)
        if user:
            try:
                latest_attempt = TestAttempt.objects.filter(user=user, status='completed').order_by('-completed_at').first()
                if latest_attempt:
                    # Load detailed results from TestAnswer
                    from resumeanalysis.models import TestAnswer
                    answers = TestAnswer.objects.filter(test_attempt=latest_attempt).order_by('id')
                    detailed_results = []
                    for i, ans in enumerate(answers):
                        detailed_results.append({
                            'question_number': i + 1,
                            'question': ans.question_text,
                            'options': ans.question_options,
                            'user_answer': ans.selected_answer if ans.selected_answer != -1 else None,
                            'correct_answer': ans.correct_answer if ans.correct_answer != -1 else None,
                            'is_correct': ans.is_correct
                        })

                    results = {
                        'total_questions': latest_attempt.total_questions,
                        'correct_answers': latest_attempt.questions_correct,
                        'wrong_answers': latest_attempt.total_questions - latest_attempt.questions_correct,
                        'percentage': latest_attempt.total_score,
                        'performance_level': "Historical Result",
                        'message': f"Showing your result from {latest_attempt.completed_at.strftime('%Y-%m-%d %H:%M')}",
                        'detailed_results': detailed_results
                    }
            except Exception as e:
                print(f"Error fetching historical result: {e}")

    if not results:
        return render(request, 'mock_test/404.html')
    
    # Check if this test was part of personalized plan assessment
    personalized_plan_data = request.session.get('personalized_plan_data')
    is_assessment = bool(personalized_plan_data)
    
    # Calculate performance color for UI
    percentage = results.get('percentage', 0)
    performance_color = 'gray'
    if percentage >= 90:
        performance_color = 'green'
    elif percentage >= 75:
        performance_color = 'blue'
    elif percentage >= 60:
        performance_color = 'yellow'
    elif percentage >= 45:
        performance_color = 'orange'
    else:
        performance_color = 'red'
    
    context = {
        'results': results,
        'performance_color': performance_color,
        'is_personalized_assessment': is_assessment,
        'personalized_plan_data': personalized_plan_data
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
    
    return render(request, 'mock_test/exam/results.html', context)

def exam_interface(request):
    """Universal exam interface"""
    return render(request, 'mock_test/exam/index.html')

def serve_question_file(request, test_type, category, filename):
    """Serve question files for development"""
    try:
        questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'questions', 
                                     test_type + 's', category, filename)
        
        if not os.path.exists(questions_file):
            return HttpResponse('Question file not found', status=404)
        
        with open(questions_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HttpResponse(content, content_type='application/json')
    except Exception as e:
        return HttpResponse(f'Error serving file: {str(e)}', status=500)

# Core Assessment Views
def core_assessment_selection(request):
    """Display core assessment selection page with dynamic data"""
    # Define core assessment areas with their information
    core_assessments = [
        {
            'name': 'Aptitude Modules',
            'key': 'aptitude',
            'description': 'Comprehensive modules covering quantitative aptitude, logical reasoning, and problem-solving skills.',
            'icon': 'psychology',
            'test_count': 2,
            'time_limit': 30,
            'difficulty': 'Intermediate',
            'color': 'blue'
        },
        {
            'name': 'Reasoning Test', 
            'key': 'reasoning',
            'description': 'Evaluate your analytical reasoning, critical thinking, and logical deduction abilities.',
            'icon': 'lightbulb',
            'test_count': 3,
            'time_limit': 25,
            'difficulty': 'Advanced',
            'color': 'purple'
        },
        {
            'name': 'Grammar Test',
            'key': 'grammar',
            'description': 'Assess your English language proficiency, grammar rules, and communication skills.',
            'icon': 'spellcheck',
            'test_count': 3,
            'time_limit': 20,
            'difficulty': 'Beginner',
            'color': 'green'
        }
    ]
    
    context = {'core_assessments': core_assessments}
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
            
    return render(request, 'mock_test/Core Assessment Areas/index.html', context)

def core_assessment_detail(request, assessment_type):
    """Display core assessment detail page with test variations"""
    # Define assessment details
    assessment_details = {
        'aptitude': {
            'name': 'Aptitude Modules',
            'description': 'Select a module to evaluate your quantitative aptitude, logical reasoning, and problem-solving skills.',
            'icon': 'psychology',
            'color': 'blue',
            'skills': ['Quantitative Aptitude', 'Logical Reasoning', 'Problem Solving', 'Data Interpretation', 'Numerical Ability'],
            'tests': [
                {
                    'name': 'Aptitude Module 1',
                    'description': 'Foundation level assessment covering basic quantitative and reasoning concepts.',
                    'questions_count': 20,
                    'time_limit': 30,
                    'difficulty': 'Beginner',
                    'test_index': 1
                },
                {
                    'name': 'Aptitude Module 2', 
                    'description': 'Intermediate level with complex problem-solving and data interpretation.',
                    'questions_count': 25,
                    'time_limit': 30,
                    'difficulty': 'Intermediate',
                    'test_index': 2
                }
            ]
        },
        'reasoning': {
            'name': 'Reasoning Test',
            'description': 'Evaluate your analytical reasoning, critical thinking, and logical deduction abilities.',
            'icon': 'lightbulb',
            'color': 'purple',
            'skills': ['Logical Deduction', 'Analytical Reasoning', 'Critical Thinking', 'Pattern Recognition', 'Verbal Reasoning'],
            'tests': [
                {
                    'name': 'Reasoning Module 1',
                    'description': 'Foundation level assessment of basic logical and analytical reasoning.',
                    'questions_count': 20,
                    'time_limit': 25,
                    'difficulty': 'Beginner',
                    'test_index': 1
                },
                {
                    'name': 'Reasoning Module 2',
                    'description': 'Intermediate level with complex logical patterns and deductions.',
                    'questions_count': 25,
                    'time_limit': 25,
                    'difficulty': 'Intermediate',
                    'test_index': 2
                }
            ]
        },
        'grammar': {
            'name': 'Grammar Test',
            'description': 'Assess your English language proficiency, grammar rules, and communication skills.',
            'icon': 'spellcheck',
            'color': 'green',
            'skills': ['Grammar Rules', 'Vocabulary', 'Sentence Structure', 'Reading Comprehension', 'Communication Skills'],
            'tests': [
                {
                    'name': 'Grammar Module 1',
                    'description': 'Foundation level assessment of basic English grammar and vocabulary.',
                    'questions_count': 20,
                    'time_limit': 20,
                    'difficulty': 'Beginner',
                    'test_index': 1
                },
                {
                    'name': 'Grammar Module 2',
                    'description': 'Intermediate level with complex grammar rules and sentence structures.',
                    'questions_count': 25,
                    'time_limit': 20,
                    'difficulty': 'Intermediate',
                    'test_index': 2
                }
            ]
        }
    }
    
    # Get assessment details or return 404 if not found
    assessment = assessment_details.get(assessment_type)
    if not assessment:
        return render(request, 'mock_test/404.html')
    
    context = {
        'assessment_type': assessment_type,
        'assessment': assessment,
        'tests': assessment['tests']
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context for sidebar/header
    user = get_user_registration(request)
    if user:
        context['user'] = user
            
    return render(request, 'mock_test/Core Assessment Areas/detail.html', context)

def start_core_assessment(request, assessment_type, test_index):
    """Start a core assessment test with module selection"""
    try:
        if 'userid' not in request.session and not request.user.is_authenticated:
            messages.error(request, "Please log in first.")
            return redirect('users:user_login')
        
        # Map assessment types to their respective files
        assessment_files = {
            'aptitude': 'Core Assessment Areas/aptitude_1.json',
            'reasoning': 'Core Assessment Areas/reasoning_1.json',
            'grammar': 'Core Assessment Areas/grammar_1.json'
        }
        
        if assessment_type not in assessment_files:
            messages.error(request, "Invalid assessment type.")
            return redirect('users:core_assessment_selection')
        
        # Load questions from the appropriate file
        questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'questions', assessment_files[assessment_type])
        
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
        except FileNotFoundError:
            messages.error(request, f"Questions file not found for {assessment_type}.")
            return redirect('users:core_assessment_selection')
        except json.JSONDecodeError:
            messages.error(request, f"Invalid JSON format in {assessment_type} questions file.")
            return redirect('users:core_assessment_selection')
        
        # Select questions based on module (test_index)
        # We'll use the test_index to seed the random number generator for consistency
        # Module 1 (test_index=1) will always get the same 20 questions
        # Module 2 (test_index=2) will always get the same 20 questions (different from Module 1)
        
        q_count = 20 if test_index == 1 else 25
        
        # Use a deterministic seed for consistency
        random.seed(f"{assessment_type}_{test_index}")
        if len(all_questions) > q_count:
            selected_questions = random.sample(all_questions, q_count)
        else:
            selected_questions = all_questions
            
        # Standardize question format for the exam interface
        standardized_questions = []
        for q in selected_questions:
            standardized_questions.append({
                'question': q.get('question_text', q.get('question', '')),
                'options': q.get('options', []),
                'correct': q.get('correct_answer', q.get('correct', 0))
            })
        selected_questions = standardized_questions
            
        # Reset seed for other parts of the app
        random.seed()
        
        # Store questions in session for the exam interface
        request.session['exam_questions'] = selected_questions
        request.session['exam_start_time'] = timezone.now().isoformat()
        
        # Determine time limit
        time_limit = 30
        if assessment_type == 'reasoning':
            time_limit = 25
        elif assessment_type == 'grammar':
            time_limit = 20
            
        # Prepare context for standard exam interface
        context = {
            'test_name': f"{assessment_type.title()} Module {test_index}",
            'test_type': 'core',
            'category': assessment_type,
            'test_index': test_index,
            'total_questions': len(selected_questions),
            'time_limit': time_limit,
            'is_core': True,
            'questions_json': json.dumps(selected_questions)
        }
        
        # Add progress context
        context.update(get_user_progress(request))
        
        # Add user context
        user = get_user_registration(request)
        if user:
            context['user'] = user

        return render(request, 'mock_test/exam/index.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('users:core_assessment_selection')

@csrf_exempt
@require_http_methods(["POST"])
def submit_core_assessment(request):
    """Handle core assessment submission and persist results"""
    try:
        if 'userid' not in request.session:
            return JsonResponse({'status': 'error', 'message': 'Session expired. Please log in again.'}, status=401)
            
        data = json.loads(request.body)
        assessment_type = data.get('assessment_type')
        user_answers = data.get('answers', [])
        time_taken = data.get('time_taken', 0)
        
        # In a real scenario, we'd fetch questions from session or DB to verify answers
        # For now, we trust the client-side calculation but we'll save it to DB
        
        correct_count = 0
        total_questions = len(user_answers)
        
        for ans in user_answers:
            if ans.get('is_correct'):
                correct_count += 1
        
        score = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Save to database
        user = get_user_registration(request)
        if not user:
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
        
        # Calculate XP earned
        xp_earned = int((score / 100) * 500)
        
        attempt = TestAttempt.objects.create(
            user=user,
            total_questions=total_questions,
            time_limit=get_time_limit(assessment_type),
            time_taken=time_taken,
            status='completed',
            completed_at=timezone.now(),
            total_score=score,
            questions_answered=total_questions,
            questions_correct=correct_count,
            xp_earned=xp_earned,
            # We use role_id to store a reference to the assessment type if needed
            # For core assessments, we might need a better way to distinguish them
            # but let's use a convention for now
        )
        
        # Update XP
        try:
            xp_obj, created = MockTestXP.objects.get_or_create(user_id=user.userid)
            xp_obj.update_progress(xp_earned)
        except Exception as e:
            print(f"Error updating MockTestXP: {e}")
        
        return JsonResponse({
            'status': 'success',
            'attempt_id': attempt.id,
            'xp_earned': xp_earned
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_time_limit(assessment_type):
    """Get time limit for each assessment type"""
    time_limits = {
        'aptitude': 30,  # 30 minutes
        'reasoning': 25,  # 25 minutes  
        'grammar': 20,    # 20 minutes
    }
    return time_limits.get(assessment_type, 30)

def core_assessment_results(request):
    """Display core assessment results from localStorage"""
    assessment_type = request.GET.get('assessment_type', 'aptitude')
    
    context = {
        'assessment_type': assessment_type,
        'assessment_title': assessment_type.title(),
    }
    
    # Add progress context
    context.update(get_user_progress(request))
    
    # Add user context
    user = get_user_registration(request)
    if user:
        context['user'] = user
            
    return render(request, 'mock_test/core_results.html', context)
