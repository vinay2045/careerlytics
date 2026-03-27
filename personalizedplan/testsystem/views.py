import json
import random
import os
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib import messages
from personalizedplan.models import WeeklyPlan, AssessmentResult, WeakTopicDiagnosis, UserXP, XPReward, PersonalizedPlan, DailyTask, AssessmentSession
from resumeanalysis.models import TestAttempt
from users.models import UserRegistration
from personalizedplan.views import session_login_required

def get_questions_file_path(topic):
    """Helper to find the most relevant question file based on topic"""
    base_dir = os.path.join(str(settings.BASE_DIR), 'mocktestdata', 'questions')
    topic_lower = topic.lower()
    
    # Mapping of common topics to file paths
    mapping = {
        'python': ('languages', 'python', 'python_fundamentals.json'),
        'java': ('languages', 'java', 'java_core.json'),
        'javascript': ('languages', 'javascript', 'javascript_es6.json'),
        'cpp': ('languages', 'cpp', 'cpp_stl.json'),
        'frontend': ('roles', 'frontend', 'frontend_html_css.json'),
        'html': ('roles', 'frontend', 'frontend_html_css.json'),
        'css': ('roles', 'frontend', 'frontend_html_css.json'),
        'react': ('roles', 'frontend', 'frontend_html_css.json'), # React specifically fallback to frontend
        'backend': ('roles', 'backend', 'backend_django.json'),
        'django': ('roles', 'backend', 'backend_django.json'),
        'node': ('roles', 'backend', 'backend_nodejs.json'),
        'sql': ('roles', 'backend', 'backend_django.json'), # SQL fallback
        'datascience': ('roles', 'datascience', 'datascience_python.json'),
        'data science': ('roles', 'datascience', 'datascience_python.json'),
        'devops': ('roles', 'devops', 'devops_docker.json'),
        'fullstack': ('roles', 'backend', 'backend_django.json'), # Fullstack fallback to backend
    }
    
    # Priority check for exact matches first
    if topic_lower in mapping:
        return os.path.join(base_dir, *mapping[topic_lower])
    
    # Try direct mapping with partial match
    for key, path_tuple in mapping.items():
        if key in topic_lower:
            return os.path.join(base_dir, *path_tuple)
            
    # Fallback: Search for file with matching name
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if topic_lower in file.lower():
                return os.path.join(root, file)
                
    # Default fallback
    return os.path.join(base_dir, 'languages', 'python', 'python_fundamentals.json')

def parse_questions(content, file_ext='.json'):
    """Parse questions from file content"""
    if file_ext == '.json':
        try:
            data = json.loads(content)
            # Handle different JSON structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'questions' in data:
                return data['questions']
            else:
                return []
        except json.JSONDecodeError:
            return []
    else:
        # Text file parsing (legacy format support)
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
                    
                    if answer_text == 'A': current_question['correct'] = 0
                    elif answer_text == 'B': current_question['correct'] = 1
                    elif answer_text == 'C': current_question['correct'] = 2
                    elif answer_text == 'D': current_question['correct'] = 3
                    elif answer_text.isdigit(): current_question['correct'] = int(answer_text) - 1
        
        if current_question and current_question['question'] and current_question['options']:
            questions.append(current_question)
        
        return questions

@session_login_required
def start_initial_assessment(request, category):
    """Initialize an initial assessment session for personalized plan"""
    # Get personalized plan data from session
    plan_data = request.session.get('personalized_plan_data')
    if not plan_data:
        messages.error(request, "Please start from the personalized plan selection.")
        return redirect('personalizedplan:start')
    
    # Find and update assessment session
    try:
        assessment_session = AssessmentSession.objects.get(
            user__userid=request.session['userid'],
            session_key=plan_data['session_key'],
            status='started'
        )
        assessment_session.status = 'in_progress'
        assessment_session.save()
    except AssessmentSession.DoesNotExist:
        messages.error(request, "Invalid assessment session. Please start again.")
        return redirect('personalizedplan:start')
        
    # Find appropriate question file
    file_path = get_questions_file_path(category)
    
    if not os.path.exists(file_path):
        messages.error(request, "Assessment content not found.")
        return redirect('personalizedplan:start')
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            _, ext = os.path.splitext(file_path)
            questions = parse_questions(content, ext)
            
        # Select 30 random questions or all if less than 30
        if not questions:
            raise ValueError("No questions found in the selected file.")
            
        selected_questions = questions if len(questions) <= 30 else random.sample(questions, 30)
        
        # Store in session
        request.session['current_test_questions'] = selected_questions
        request.session['current_test_context'] = {
            'type': 'initial_assessment',
            'id': 'initial',
            'title': f"Initial Assessment - {category}",
            'week_number': 0,
            'plan_id': None,
            'category': category,
            'session_key': plan_data['session_key']
        }
        
        return redirect('personalizedplan:testsystem:exam_interface')
        
    except Exception as e:
        messages.error(request, f"Error starting assessment: {str(e)}")
        return redirect('personalizedplan:start')

@session_login_required
def start_weekly_test(request, week_id):
    """Initialize a weekly test session"""
    week_plan = get_object_or_404(WeeklyPlan, id=week_id)
    
    # Check if user is authorized for this plan
    if week_plan.personalized_plan.user.userid != request.session['userid']:
        messages.error(request, "Unauthorized access to this test.")
        return redirect('personalizedplan:dashboard')
        
    # Find appropriate question file
    file_path = get_questions_file_path(week_plan.skill_focus)
    
    if not os.path.exists(file_path):
        messages.error(request, "Test content not found.")
        return redirect('personalizedplan:plan_detail', plan_id=week_plan.personalized_plan.id)
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            _, ext = os.path.splitext(file_path)
            questions = parse_questions(content, ext)
            
        # Select 30 random questions or all if less than 30
        if not questions:
            raise ValueError("No questions found in the selected file.")

        selected_questions = questions if len(questions) <= 30 else random.sample(questions, 30)
        
        # Store in session
        request.session['current_test_questions'] = selected_questions
        request.session['current_test_context'] = {
            'type': 'weekly',
            'id': str(week_id),
            'title': f"Week {week_plan.week_number} - {week_plan.skill_focus}",
            'week_number': week_plan.week_number,
            'plan_id': str(week_plan.personalized_plan.id)
        }
        
        return redirect('personalizedplan:testsystem:exam_interface')
        
    except Exception as e:
        messages.error(request, f"Error starting test: {str(e)}")
        return redirect('personalizedplan:plan_detail', plan_id=week_plan.personalized_plan.id)

@session_login_required
def exam_interface(request):
    """Render the exam interface"""
    test_context = request.session.get('current_test_context')
    questions = request.session.get('current_test_questions')
    
    if not test_context or not questions:
        messages.error(request, "No active test found. Please start an assessment from the beginning.")
        return redirect('personalizedplan:start')
        
    return render(request, 'personalizedplan/testsystem/exam_interface.html', {
        'test_context': test_context,
        'questions_json': json.dumps(questions)
    })

@csrf_exempt
@require_http_methods(["POST"])
def submit_test(request):
    """Handle test submission"""
    try:
        data = json.loads(request.body)
        user_answers = data.get('answers', [])
        questions = request.session.get('current_test_questions', [])
        test_context = request.session.get('current_test_context')
        
        if not questions or not test_context:
            return JsonResponse({'status': 'error', 'message': 'Session expired'}, status=400)
            
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
                'question': question.get('question_text', question.get('question', '')),
                'is_correct': is_correct,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'tags': question.get('tags', [])
            })
            
        # Calculate score
        score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Determine pass/fail (70% threshold)
        passed = score_percentage >= 70
        message = "Test Passed!" if passed else "Test Failed. Keep practicing!"
        
        # Save results to session for the results page
        request.session['exam_results'] = {
            'type': test_context.get('type', 'weekly'),
            'total_questions': total_questions,
            'correct_answers': correct_count,
            'wrong_answers': total_questions - correct_count,
            'score_percentage': score_percentage,
            'topic': test_context.get('title', 'Weekly Test'),
            'passed': passed,
            'message': message,
            'results_detail': results,
            'is_revised': False,  # Default
        }
        
        # Save to database
        try:
            # Get UserRegistration correctly from session userid
            from users.models import UserRegistration
            user_reg = get_object_or_404(UserRegistration, userid=request.session.get('userid'))
            
            if test_context.get('type') == 'initial_assessment':
                # Create TestAttempt for initial assessment (Existing logic)
                test_attempt = TestAttempt.objects.create(
                    user=user_reg,
                    total_questions=total_questions,
                    time_limit=30, 
                    status='completed',
                    completed_at=timezone.now(),
                    total_score=int(score_percentage),
                    questions_answered=total_questions,
                    questions_correct=correct_count,
                    general_score=int(score_percentage),
                    tech_score=int(score_percentage),
                    role_score=int(score_percentage)
                )
                
                # Update assessment session
                session_key = test_context.get('session_key')
                if session_key:
                    try:
                        assessment_session = AssessmentSession.objects.get(
                            user=user_reg,
                            session_key=session_key,
                            status='in_progress'
                        )
                        assessment_session.status = 'completed'
                        assessment_session.completed_at = timezone.now()
                        assessment_session.save()
                    except AssessmentSession.DoesNotExist:
                        pass
                
                return JsonResponse({'status': 'success', 'redirect_url': '/personalized-plan/create-from-assessment/'})

            # For Weekly Tests - Save results and then recommend
            # 1. Get WeeklyPlan
            week_plan = get_object_or_404(WeeklyPlan, id=test_context['id'])
            
            # 2. Create or update AssessmentResult (THIS SAVES THE DATA)
            assessment, created = AssessmentResult.objects.get_or_create(
                user=user_reg,
                personalized_plan=week_plan.personalized_plan,
                test_type='weekly',
                defaults={
                    'score': score_percentage,
                    'total_questions': total_questions,
                    'created_at': timezone.now()
                }
            )
            
            if not created:
                assessment.score = score_percentage
                assessment.total_questions = total_questions
                assessment.created_at = timezone.now()
                assessment.save()
            
            user = week_plan.personalized_plan.user
            
            if passed:
                # Success Logic (Existing)
                week_plan.status = 'completed'
                week_plan.save()
                
                xp_amount = 300 + (correct_count * 10)
                user_xp, _ = UserXP.objects.get_or_create(user=user)
                user_xp.total_xp += xp_amount
                user_xp.save()
                
                XPReward.objects.create(
                    user_xp=user_xp,
                    reward_type='weekly_test',
                    xp_amount=xp_amount,
                    reason=f"Passed {test_context.get('title', 'Weekly Test')}"
                )
            else:
                # 3. RECOMMENDATION LOGIC (Only after data is saved)
                # Mark week as failed
                week_plan.status = 'failed'
                week_plan.save()
                
                # Add extra days for practice
                extra_days = 2 if score_percentage > 50 else 4
                week_plan.extra_days_added += extra_days
                
                # Create WeakTopicDiagnosis
                # Extract failed topics from tags
                failed_tags = []
                for res in results:
                    if not res['is_correct'] and res.get('tags'):
                        failed_tags.extend(res['tags'])
                
                # Count and sort most frequent failed tags
                from collections import Counter
                tag_counts = Counter(failed_tags)
                top_failed_topics = [tag for tag, count in tag_counts.most_common(3)]
                
                weak_details = {
                    'focus_area': test_context.get('title', 'Weekly Test'),
                    'score': f"{score_percentage:.1f}%",
                    'threshold': "70%",
                    'suggestion': f"Focus on these key areas: {', '.join(top_failed_topics) if top_failed_topics else 'General Review'}.",
                    'missed_concepts': [q['question'][:50] + "..." for q in results if not q['is_correct']][:5],
                    'top_topics': top_failed_topics
                }
                
                diagnosis = WeakTopicDiagnosis.objects.create(
                    assessment_result=assessment,
                    weak_topics=weak_details,
                    severity_level='medium' if score_percentage > 50 else 'high'
                )
                
                # Generate Remedial Daily Tasks
                last_task = DailyTask.objects.filter(weekly_plan=week_plan).order_by('-day_number').first()
                start_day = last_task.day_number + 1 if last_task else 8
                
                revised_tasks = []
                for i in range(extra_days):
                    # Use specific topics for task names if available
                    if top_failed_topics:
                        current_topic = top_failed_topics[i % len(top_failed_topics)]
                        task_topic = f"Revised Plan Day {i+1}: {current_topic.replace('-', ' ').title()} Mastery"
                        task_desc = f"REVISED STUDY PLAN: Deep dive into {current_topic.replace('-', ' ')}. This area showed weakness in your last test. Review documentation and practice coding examples."
                    else:
                        missed_qs = [q['question'] for q in results if not q['is_correct']]
                        focus_q = missed_qs[i % len(missed_qs)] if missed_qs else "General Review"
                        task_topic = f"Revised Plan Day {i+1}: {test_context.get('title', 'Weekly Test')} Focus"
                        task_desc = f"REVISED STUDY PLAN: Deep dive into concepts you missed. Focus on: {focus_q[:120]}..."
                    
                    task = DailyTask.objects.create(
                        weekly_plan=week_plan,
                        day_number=start_day + i,
                        topic=task_topic,
                        description=task_desc,
                        status='unlocked' if i == 0 else 'locked',
                        xp_reward=25
                    )
                    revised_tasks.append(task.topic)
                
                # Keep status as failed to show warning
                week_plan.status = 'failed'
                week_plan.save()
                
                # Update session for results page feedback
                request.session['exam_results'].update({
                    'is_revised': True,
                    'extra_days': extra_days,
                    'revised_tasks': revised_tasks,
                    'diagnosis': weak_details
                })
                request.session.modified = True
                
                # Effort XP
                xp_amount = correct_count * 5
                if xp_amount > 0:
                    user_xp, _ = UserXP.objects.get_or_create(user=user)
                    user_xp.total_xp += xp_amount
                    user_xp.save()
                    
                    XPReward.objects.create(
                        user_xp=user_xp,
                        reward_type='weekly_test',
                        xp_amount=xp_amount,
                        reason=f"Attempted {test_context.get('title', 'Weekly Test')}"
                    )
            
        except Exception as e:
            print(f"Error saving results: {e}")
            # Continue anyway to show results to user
            
        return JsonResponse({'status': 'success', 'redirect_url': '/personalized-plan/test-system/results/'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@session_login_required
def get_test_data(request):
    """API to get current test questions for the frontend"""
    questions = request.session.get('current_test_questions')
    context = request.session.get('current_test_context')
    
    if not questions or not context:
        return JsonResponse({'error': 'No active test found'}, status=404)
        
    return JsonResponse({
        'questions': questions,
        'context': context
    })

@session_login_required
def exam_results(request):
    """Render the results page"""
    results = request.session.get('exam_results')
    if not results:
        return redirect('personalizedplan:dashboard')
        
    return render(request, 'personalizedplan/testsystem/results.html', {
        'results': results
    })
