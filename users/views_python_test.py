"""
Django Views for Python Mock Test
Handles Python programming test with 50 questions and dynamic options
"""

import json
import random
import os
import re
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings


def serve_python_questions(request):
    """Serve Python questions text file"""
    try:
        questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'pythonquestions.txt')
        with open(questions_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain')
    except Exception as e:
        return HttpResponse(f'Error loading file: {str(e)}', status=500)


def python_test(request):
    """Main Python test page"""
    return render(request, 'users/python_test.html')


def python_test_dashboard(request):
    """Python test selection and instructions page"""
    return render(request, 'users/python_test_dashboard.html')


def load_python_questions(request):
    """Load Python questions from text file"""
    try:
        # Path to Python questions file
        questions_file = os.path.join(settings.BASE_DIR, 'mocktestdata', 'pythonquestions.txt')
        
        with open(questions_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        questions = parse_python_questions(content)
        
        # Shuffle and limit to 50 questions
        random.shuffle(questions)
        limited_questions = questions[:50]
        
        return JsonResponse({
            'status': 'success',
            'questions': limited_questions,
            'total_questions': len(limited_questions)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to load questions: {str(e)}'
        }, status=500)


def parse_python_questions(content):
    """Parse Python questions from text file format"""
    questions = []
    lines = content.split('\n')
    current_question = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('View Answer') or line.startswith('Explanation:'):
            continue
            
        # New question starts with number and dot
        if re.match(r'^\d+\.\s*', line):
            # Save previous question if exists
            if current_question and current_question['question'] and current_question['options']:
                questions.append(current_question)
            
            # Start new question
            question_text = re.sub(r'^\d+\.\s*', '', line)
            current_question = {
                'question': question_text,
                'options': [],
                'correct_answer': None,
                'explanation': ''
            }
            
        # Option lines start with a), b), c), d) or +, -, etc.
        elif re.match(r'^[a-dA-D]\)\s*', line) or re.match(r'^[+-]\s*', line):
            if current_question:
                # Clean option text
                option_text = re.sub(r'^[a-dA-D]\)\s*', '', line).strip()
                option_text = re.sub(r'^[+-]\s*', '', option_text).strip()
                current_question['options'].append(option_text)
                
        # Correct answer line
        elif line.lower().startswith('correct answer:') or line.lower().startswith('answer:'):
            if current_question:
                answer_text = re.sub(r'.*correct answer:\s*', '', line, flags=re.IGNORECASE)
                answer_text = re.sub(r'.*answer:\s*', '', answer_text, flags=re.IGNORECASE)
                answer_text = answer_text.strip().upper()
                
                # Convert letter to index (A=0, B=1, C=2, D=3)
                if answer_text == 'A':
                    current_question['correct_answer'] = 0
                elif answer_text == 'B':
                    current_question['correct_answer'] = 1
                elif answer_text == 'C':
                    current_question['correct_answer'] = 2
                elif answer_text == 'D':
                    current_question['correct_answer'] = 3
                elif answer_text.isdigit():
                    current_question['correct_answer'] = int(answer_text) - 1
    
    # Save last question
    if current_question and current_question['question'] and current_question['options']:
        questions.append(current_question)
    
    return questions


@csrf_exempt
@require_http_methods(["POST"])
def submit_python_test_auto(request):
    """Handle auto-submitted Python test when user exits"""
    try:
        data = json.loads(request.body)
        
        # Extract auto-submitted test data
        score = data.get('score', 0)
        correct_count = data.get('correctCount', 0)
        total_count = data.get('totalCount', 0)
        time_taken = data.get('timeTaken', 0)
        results = data.get('results', [])
        auto_submitted = data.get('autoSubmitted', False)
        submission_time = data.get('submissionTime')
        
        # Get user from session
        if 'username' not in request.session:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        
        user_id = request.session['username']
        
        # Store test results (you might want to save to database)
        test_result = {
            'user_id': user_id,
            'score': score,
            'correct_count': correct_count,
            'total_count': total_count,
            'time_taken': time_taken,
            'auto_submitted': auto_submitted,
            'submission_time': submission_time,
            'results': results,
            'test_type': 'python_auto_submit'
        }
        
        # Store in session for results page
        request.session['python_test_results'] = test_result
        
        return JsonResponse({'status': 'success', 'message': 'Test auto-submitted successfully'})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid data format'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def submit_python_test(request):
    """Submit Python test and calculate results"""
    try:
        data = json.loads(request.body)
        user_answers = data.get('answers', [])
        questions = data.get('questions', [])
        
        # Calculate results
        correct_count = 0
        total_questions = len(questions)
        results = []
        
        for i, question in enumerate(questions):
            user_answer = user_answers[i] if i < len(user_answers) else None
            correct_answer = question.get('correct_answer')
            is_correct = user_answer == correct_answer
            
            if is_correct:
                correct_count += 1
            
            results.append({
                'question_number': i + 1,
                'question': question['question'],
                'options': question['options'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
        
        # Calculate percentage
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Determine performance level
        if percentage >= 80:
            performance = "Excellent"
            message = "Outstanding performance! You have excellent Python knowledge."
        elif percentage >= 70:
            performance = "Good"
            message = "Good job! You have solid Python programming skills."
        elif percentage >= 60:
            performance = "Average"
            message = "Fair performance. Consider reviewing Python fundamentals."
        else:
            performance = "Needs Improvement"
            message = "Keep practicing! Focus on Python basics and programming concepts."
        
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
            'message': f'Failed to submit test: {str(e)}'
        }, status=500)


def python_test_results(request):
    """Display Python test results page"""
    # Check for auto-submitted test results in session
    auto_results = request.session.get('python_test_results')
    
    # Check for manually submitted test results in sessionStorage (passed via template)
    context = {}
    if auto_results:
        context = {
            'score': auto_results['score'],
            'correct_count': auto_results['correct_count'],
            'total_count': auto_results['total_count'],
            'time_taken': auto_results['time_taken'],
            'auto_submitted': auto_results['auto_submitted'],
            'submission_time': auto_results['submission_time'],
            'results': auto_results['results']
        }
        # Clear the auto-submitted results from session
        del request.session['python_test_results']
    
    return render(request, 'users/python_test_results.html', context)
