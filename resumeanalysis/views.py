import json
import time
import uuid
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict, Any

from typing import Any
import os

from users.models import UserRegistration
from .models import (
    ResumeAnalysis, RoleQuiz, QuizQuestion, QuizResponse, 
    RoleEligibility, RecommendedRole, TestAttempt, TestAnswer
)
from .forms import ResumeUploadForm, QuizStartForm, QuizAnswerForm, RoleSelectionForm
from .resume_analyzer import analyze_resume_text
from .quiz_generator import generate_role_quiz, calculate_quiz_scores
from .eligibility_calculator import calculate_role_eligibility

def extract_text_from_file(uploaded_file) -> str:
    """Extract text from uploaded resume file"""
    try:
        # For PDF files
        if uploaded_file.name.lower().endswith('.pdf'):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
            except ImportError:
                # Fallback if PyPDF2 not available
                return "PDF processing not available. Please install PyPDF2."
        
        # For DOCX files
        elif uploaded_file.name.lower().endswith('.docx'):
            try:
                import docx
                doc = docx.Document(uploaded_file)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                # Fallback if python-docx not available
                return "DOCX processing not available. Please install python-docx."
        
        # For DOC files (basic text extraction)
        elif uploaded_file.name.lower().endswith('.doc'):
            # Basic text extraction - may not work perfectly for all DOC files
            try:
                import antiword
                return antiword.run(uploaded_file.temporary_file_path())
            except ImportError:
                return "DOC processing requires antiword. Please convert to PDF or DOCX."
        
        else:
            return "Unsupported file format."
            
    except Exception as e:
        return f"Error processing file: {str(e)}"

def upload_resume(request):
    """Handle resume upload and analysis"""
    print("=== Upload Resume Request ===")  # Debug line
    print(f"Request method: {request.method}")  # Debug line
    print(f"User in session: {'username' in request.session}")  # Debug line
    
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        print("No user in session")  # Debug line
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
        print(f"Found user: {user.userid}")  # Debug line
    except UserRegistration.DoesNotExist:
        print("User not found in database")  # Debug line
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Check for recent resume uploads (7-day cooldown)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_analysis = ResumeAnalysis.objects.filter(
        user=user, 
        created_at__gte=seven_days_ago
    ).first()
    
    # Calculate cooldown info
    can_upload = not recent_analysis
    next_upload_date = None
    hours_remaining = 0
    
    if recent_analysis:
        next_upload_date = recent_analysis.created_at + timedelta(days=7)
        time_remaining = next_upload_date - timezone.now()
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        days_remaining = int(time_remaining.days)
        
        if days_remaining > 0:
            time_str = f"{days_remaining} day{'s' if days_remaining != 1 else ''}"
        else:
            time_str = f"{hours_remaining} hour{'s' if hours_remaining != 1 else ''}"
        
        messages.info(request, f"You must wait {time_str} or Delete existing resume to upload another resume. Next upload available: {next_upload_date.strftime('%B %d, %Y at %I:%M %p')}.")
    
    if request.method == 'POST':
        # Check cooldown before processing upload
        if not can_upload:
            messages.error(request, f"Resume upload is locked. Please wait {time_str} or Delete existing resume to upload again.")
            return render(request, 'resumeanalysis/upload_resume.html', {
                'form': ResumeUploadForm(),
                'user': user,
                'can_upload': False,
                'next_upload_date': next_upload_date,
                'hours_remaining': hours_remaining,
                'recent_analysis': recent_analysis
            })
        
        print("Processing POST request")  # Debug line
        form = ResumeUploadForm(request.POST, request.FILES)
        print(f"Form is valid: {form.is_valid()}")  # Debug line
        
        if form.is_valid():
            try:
                resume_file = request.FILES['resume_file']
                target_role = form.cleaned_data['target_role']
                print(f"Processing resume upload for role: {target_role}")  # Debug line
                print(f"Resume file name: {resume_file.name}")  # Debug line
                print(f"Resume file size: {resume_file.size}")  # Debug line
                
                # Analyze resume
                print("Starting resume analysis...")  # Debug line
                
                # Read file content with proper encoding handling
                try:
                    # Use helper function to extract text based on file type
                    file_content = extract_text_from_file(resume_file)
                    print(f"Text extraction successful, length: {len(file_content)}")
                    
                    # Reset file pointer for saving
                    resume_file.seek(0)
                except Exception as e:
                    print(f"Error extracting text: {e}")
                    # Fallback to simple decode if extraction fails
                    resume_file.seek(0)
                    file_content = resume_file.read().decode('utf-8', errors='ignore')
                    resume_file.seek(0)
                
                print(f"File content length: {len(file_content)} characters")  # Debug line
                analysis_result = analyze_resume_text(file_content, resume_file.name, target_role)
                print(f"Analysis completed: {analysis_result}")  # Debug line
                
                # Save resume analysis
                resume_analysis = ResumeAnalysis.objects.create(
                    user=user,
                    resume_file=resume_file,
                    original_filename=resume_file.name,
                    **analysis_result
                )
                print(f"Resume analysis saved with ID: {resume_analysis.id}")  # Debug line
                
                # Create quiz session
                try:
                    print(f"About to create quiz for user: {user.userid}, role: {target_role}")  # Debug line
                    quiz = RoleQuiz.objects.create(
                        user=user,
                        resume_analysis=resume_analysis,
                        target_role=target_role,
                        status='pending'
                    )
                    print(f"Successfully created quiz with ID: {quiz.id} for role: {target_role}")  # Debug line
                    print(f"Quiz ID type: {type(quiz.id)}")  # Debug line
                    print(f"Quiz object: {quiz}")  # Debug line
                    
                    # Verify quiz was saved
                    quiz_from_db = RoleQuiz.objects.get(id=quiz.id)
                    print(f"Quiz from DB: {quiz_from_db}, status: {quiz_from_db.status}")  # Debug line
                    
                except Exception as e:
                    print(f"Error creating quiz: {e}")  # Debug line
                    import traceback
                    traceback.print_exc()  # Debug line
                    messages.error(request, f"Error creating quiz: {str(e)}")
                    return render(request, 'resumeanalysis/upload_resume.html', {
                        'form': form, 'user': user
                    })
                
                messages.success(request, "Resume uploaded and analyzed successfully!")
                
                # Redirect directly to the quiz system
                redirect_url = reverse('resumeanalysis:start_quiz', kwargs={'quiz_id': quiz.id})
                print(f"Redirecting to: {redirect_url}")  # Debug line
                print(f"Quiz ID for redirect: {quiz.id}")  # Debug line
                print(f"Redirect URL type: {type(redirect_url)}")  # Debug line
                return redirect(redirect_url)
                
            except Exception as e:
                print(f"Error processing resume: {e}")  # Debug line
                import traceback
                traceback.print_exc()  # Debug line
                messages.error(request, f"Error processing resume: {str(e)}")
                return render(request, 'resumeanalysis/upload_resume.html', {
                    'form': form, 'user': user
                })
        else:
            print("Form validation failed")  # Debug line
            print(f"Form errors: {form.errors}")  # Debug line
    else:
        print("GET request - showing upload form")  # Debug line
        form = ResumeUploadForm()
    
    return render(request, 'resumeanalysis/upload_resume.html', {
        'form': form, 
        'user': user,
        'can_upload': can_upload,
        'next_upload_date': next_upload_date,
        'hours_remaining': hours_remaining,
        'recent_analysis': recent_analysis
    })

def test_quiz(request):
    """Test quiz functionality"""
    print("=== Test Quiz Request ===")  # Debug line
    
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
        print(f"Found user: {user.userid}")  # Debug line
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Create a simple test quiz
    try:
        quiz = RoleQuiz.objects.create(
            user=user,
            target_role='backend',
            status='pending'
        )
        print(f"Created test quiz with ID: {quiz.id}")  # Debug line
        
        # Redirect to quiz start
        redirect_url = reverse('resumeanalysis:start_quiz', kwargs={'quiz_id': quiz.id})
        print(f"Redirecting to: {redirect_url}")  # Debug line
        return redirect(redirect_url)
        
    except Exception as e:
        print(f"Error creating test quiz: {e}")  # Debug line
        messages.error(request, f"Error creating test quiz: {str(e)}")
        return redirect('upload')

def quiz_index(request):
    print("=== Quiz Index Request ===")  # Debug line
    print(f"User in session: {'username' in request.session or 'userid' in request.session}")  # Debug line
    
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
        print(f"Found user: {user.userid}")  # Debug line
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Check if user has any pending or in-progress quizzes
    pending_quizzes = RoleQuiz.objects.filter(
        user=user, 
        status__in=['pending', 'in_progress']
    ).order_by('-created_at')
    
    print(f"Found {pending_quizzes.count()} pending quizzes")  # Debug line
    
    if pending_quizzes.exists():
        # Redirect to the most recent quiz
        latest_quiz = pending_quizzes.first()
        print(f"Redirecting to existing quiz: {latest_quiz.id}")  # Debug line
        return redirect('resumeanalysis:start_quiz', quiz_id=latest_quiz.id)
    
    # No pending quizzes, redirect to upload page
    print("No pending quizzes found, redirecting to upload")  # Debug line
    messages.info(request, "Please upload your resume first to start the assessment.")
    return redirect('upload')

def start_quiz(request, quiz_id):
    """Start the quiz session"""
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Get quiz
    quiz = get_object_or_404(RoleQuiz, id=quiz_id, user=user)
    print(f"Quiz found with ID: {quiz.id}")  # Debug line
    print(f"Initial quiz status: {quiz.status}")  # Debug line
    
    if quiz.status == 'completed':
        messages.error(request, "This quiz has already been completed.")
        return redirect('resumeanalysis:quiz_results', quiz_id=quiz.id)
    
    # Generate quiz questions
    try:
        print(f"Attempting to generate quiz for role: {quiz.target_role}")  # Debug line
        quiz_data = generate_role_quiz(quiz.target_role)
        print(f"Generated quiz data for {quiz.target_role}: {len(quiz_data.get('questions', []))} questions")  # Debug line
        print(f"Quiz data keys: {list(quiz_data.keys())}")  # Debug line
        print(f"Quiz data type: {type(quiz_data)}")  # Debug line
        
        if not quiz_data:
            print("Quiz data is None or empty")  # Debug line
            messages.error(request, "Failed to generate quiz questions. Please try again.")
            return redirect('resumeanalysis:upload_resume')
            
        if 'questions' not in quiz_data:
            print("Quiz data missing 'questions' key")  # Debug line
            messages.error(request, "Failed to generate quiz questions. Please try again.")
            return redirect('resumeanalysis:upload_resume')
            
        if not quiz_data['questions']:
            print("Quiz data has empty 'questions' list")  # Debug line
            messages.error(request, "Failed to generate quiz questions. Please try again.")
            return redirect('resumeanalysis:upload_resume')
            
    except Exception as e:
        print(f"Error generating quiz: {e}")  # Debug line
        import traceback
        traceback.print_exc()  # Debug line
        
        # Create a fallback quiz with basic questions
        print("Creating fallback quiz...")  # Debug line
        quiz_data = {
            'questions': [
                {
                    'id': 'fallback_1',
                    'category': 'general',
                    'difficulty': 'easy',
                    'question_text': f'What is your experience with {quiz.target_role} development?',
                    'options': ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
                    'correct_answer': 1,
                    'explanation': 'This helps assess your current skill level.'
                },
                {
                    'id': 'fallback_2',
                    'category': 'general',
                    'difficulty': 'easy',
                    'question_text': 'How comfortable are you with problem-solving?',
                    'options': ['Not comfortable', 'Somewhat comfortable', 'Very comfortable', 'Expert level'],
                    'correct_answer': 2,
                    'explanation': 'Problem-solving is essential for development roles.'
                },
                {
                    'id': 'fallback_3',
                    'category': 'general',
                    'difficulty': 'easy',
                    'question_text': 'Do you prefer working independently or in teams?',
                    'options': ['Independently', 'Small teams', 'Large teams', 'Mixed approach'],
                    'correct_answer': 3,
                    'explanation': 'Team collaboration is important in most development roles.'
                }
            ],
            'quiz_info': {
                'title': f'{quiz.target_role.title()} Assessment',
                'description': 'Basic assessment for your selected role.',
                'total_questions': 3,
                'time_limit': 900,  # 15 minutes
                'difficulty': 'easy'
            }
        }
        print(f"Created fallback quiz with {len(quiz_data['questions'])} questions")  # Debug line
    
    # Store questions in session
    request.session[f'quiz_{quiz_id}_questions'] = quiz_data['questions']
    request.session[f'quiz_{quiz_id}_start_time'] = time.time()
    request.session.save()  # Ensure session is saved
    print(f"Stored {len(quiz_data['questions'])} questions in session")  # Debug line
    
    # Update quiz status
    quiz.status = 'in_progress'
    quiz.started_at = timezone.now()
    quiz.save()
    print(f"Updated quiz status to: {quiz.status}")  # Debug line
    
    # Create sanitized quiz data for frontend (exclude correct answers and explanations)
    import copy
    frontend_quiz_data = copy.deepcopy(quiz_data)
    for q in frontend_quiz_data.get('questions', []):
        if 'correct_answer' in q:
            del q['correct_answer']
        if 'explanation' in q:
            del q['explanation']
    
    return render(request, 'resumeanalysis/quiz.html', {
        'quiz': quiz,
        'quiz_data': frontend_quiz_data,
        'user': user
    })

def calculate_scores_from_session(responses: List[Dict[str, Any]], questions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate quiz scores using the questions from session
    
    Args:
        responses: List of user responses with question_id and selected_option
        questions: List of questions used in the quiz
        
    Returns:
        Dictionary with scores for each category and total
    """
    category_scores = {
        'general_ability': {'correct': 0, 'total': 0},
        'tech_fundamentals': {'correct': 0, 'total': 0},
        'role_specific': {'correct': 0, 'total': 0}
    }
    
    # Map categories to score categories
    category_mapping = {
        'general': 'general_ability',
        'tech_fundamentals': 'tech_fundamentals',
        'frontend': 'role_specific',
        'backend': 'role_specific',
        'devops': 'role_specific',
        'datascience': 'role_specific'
    }
    
    # Create a mapping of question_id to question for quick lookup
    question_map = {str(q['id']): q for q in questions}
    
    for response in responses:
        question_id = response.get('question_id')
        selected_option = response.get('selected_option')
        
        # Find the question from our questions list
        question = question_map.get(str(question_id))
        if not question:
            print(f"Warning: Question {question_id} not found in questions list")
            continue
        
        category = question['category']
        score_category = category_mapping.get(category, 'general_ability')
        
        # Update scores
        category_scores[score_category]['total'] += 1
        if selected_option == question['correct_answer']:
            category_scores[score_category]['correct'] += 1
    
    # Calculate percentages
    final_scores = {}
    for category, scores in category_scores.items():
        if scores['total'] > 0:
            final_scores[category] = int((scores['correct'] / scores['total']) * 100)
        else:
            final_scores[category] = 0
    
    # Calculate total score (weighted)
    weights = {
        'general_ability': 0.3,
        'tech_fundamentals': 0.3,
        'role_specific': 0.4
    }
    
    total_score = sum(
        final_scores[cat] * weight 
        for cat, weight in weights.items()
    )
    
    final_scores['total'] = int(total_score)
    
    return final_scores

@csrf_exempt
@require_POST
def submit_answer(request, quiz_id):
    """Submit quiz answer or complete quiz"""
    print(f"=== Submit Answer Request ===")  # Debug line
    print(f"Quiz ID: {quiz_id}")  # Debug line
    
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Get quiz
    quiz = get_object_or_404(RoleQuiz, id=quiz_id, user=user)
    print(f"Current quiz status: {quiz.status}")  # Debug line
    
    # If quiz is still pending, update it to in_progress (this might happen due to race conditions)
    if quiz.status == 'pending':
        print("Quiz was still pending, updating to in_progress")  # Debug line
        quiz.status = 'in_progress'
        quiz.started_at = timezone.now()
        quiz.save()
        print(f"Updated quiz status to: {quiz.status}")  # Debug line
    
    if quiz.status != 'in_progress':
        print(f"Quiz not in progress. Current status: {quiz.status}")  # Debug line
        
        # If quiz is already completed, redirect to results (handle double submission/race conditions)
        if quiz.status == 'completed':
            return JsonResponse({
                'status': 'success', 
                'message': 'Quiz already completed', 
                'redirect_url': reverse('resumeanalysis:quiz_results', kwargs={'quiz_id': quiz_id})
            })
            
        return JsonResponse({'status': 'error', 'message': f'Quiz not in progress. Current status: {quiz.status}'}, status=400)
    
    print("Quiz is in progress, proceeding with submission")  # Debug line
    
    try:
        # Handle FormData (from JavaScript fetch)
        if 'answers' in request.POST:
            # This is the final quiz submission
            answers_json = request.POST.get('answers')
            print(f"Received answers: {answers_json}")  # Debug line
            answers = json.loads(answers_json)
            questions = request.session.get(f'quiz_{quiz_id}_questions', [])
            print(f"Questions from session: {len(questions)}")  # Debug line
            
            # Clear existing responses
            QuizResponse.objects.filter(quiz=quiz).delete()
            
            # Save all answers
            for question_idx, selected_option in enumerate(answers):
                if selected_option is not None and question_idx < len(questions):
                    question = questions[question_idx]
                    QuizResponse.objects.create(
                        quiz=quiz,
                        session_question_id=question['id'],
                        user_answer=selected_option,
                        time_taken=0,
                        is_correct=(selected_option == question['correct_answer'])
                    )
            
            # Calculate scores and complete the quiz
            response_data = [
                {
                    'question_id': resp.session_question_id,
                    'selected_option': resp.user_answer
                }
                for resp in QuizResponse.objects.filter(quiz=quiz)
            ]
            
            print(f"Response data for scoring: {len(response_data)} responses")  # Debug line
            
            # Create a custom scoring function that uses the session questions
            scores = calculate_scores_from_session(response_data, questions)
            print(f"Calculated scores: {scores}")  # Debug line
            
            # Update quiz with scores
            quiz.general_ability_score = scores.get('general_ability', 0)
            quiz.tech_fundamentals_score = scores.get('tech_fundamentals', 0)
            quiz.role_specific_score = scores.get('role_specific', 0)
            quiz.total_score = scores.get('total', 0)
            quiz.status = 'completed'
            quiz.completed_at = timezone.now()
            quiz.save()
            
            # Calculate time taken
            start_time = request.session.get(f'quiz_{quiz_id}_start_time', time.time())
            quiz.time_taken = int(time.time() - start_time)
            quiz.save()
            
            # Calculate eligibility
            eligibility = calculate_role_eligibility(quiz.resume_analysis, quiz)
            
            # Save eligibility results
            with transaction.atomic():
                # Delete existing if any
                RoleEligibility.objects.filter(quiz=quiz).delete()
                
                role_eligibility = RoleEligibility.objects.create(
                    user=user,
                    quiz=quiz,
                    resume_analysis=quiz.resume_analysis,
                    role_name=eligibility['target_role'],
                    eligibility_score=eligibility['total_eligibility'],
                    is_eligible=eligibility['is_eligible'],
                    general_score=quiz.general_ability_score,
                    tech_score=quiz.tech_fundamentals_score,
                    role_score=quiz.role_specific_score,
                    resume_score=quiz.resume_analysis.ats_score,
                    recommended_roles=eligibility['recommended_roles'],
                    improvement_suggestions=eligibility['improvement_areas']
                )
                
                # Save recommended roles
                for rec in eligibility['recommended_roles']:
                    RecommendedRole.objects.create(
                        user=user,
                        eligibility=role_eligibility,
                        role_name=rec['role_name'],
                        match_percentage=rec['match_percentage'],
                        match_reasons=rec['match_reasons']
                    )
            
            # Always redirect to results page
            redirect_url = reverse('resumeanalysis:quiz_results', kwargs={'quiz_id': quiz.id})
            return JsonResponse({'status': 'success', 'message': 'Quiz submitted successfully', 'redirect_url': redirect_url})
        
        
        else:
            # Individual question submission
            question_id = request.POST.get('question_id')
            selected_option = request.POST.get('selected_option')
            time_taken = request.POST.get('time_taken', 0)
            
            # Get questions from session
            questions = request.session.get(f'quiz_{quiz_id}_questions', [])
            question = next((q for q in questions if q['id'] == question_id), None)
            
            if not question:
                return JsonResponse({'status': 'error', 'message': 'Question not found'}, status=404)
            
            # Check if already answered
            existing_response = QuizResponse.objects.filter(
                quiz=quiz, session_question_id=question_id
            ).first()
            
            if existing_response:
                # Update existing response
                existing_response.user_answer = int(selected_option)
                existing_response.time_taken = float(time_taken)
                existing_response.is_correct = (int(selected_option) == question['correct_answer'])
                existing_response.save()
            else:
                # Create new response
                QuizResponse.objects.create(
                    quiz=quiz,
                    session_question_id=question_id,
                    user_answer=int(selected_option),
                    time_taken=float(time_taken),
                    is_correct=(int(selected_option) == question['correct_answer'])
                )
            
            return JsonResponse({'status': 'success', 'message': 'Answer saved'})
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")  # Debug line
        return JsonResponse({'status': 'error', 'message': f'Invalid JSON in answers: {str(e)}'}, status=400)
    except Exception as e:
        print(f"General Error in submit_answer: {e}")  # Debug line
        import traceback
        traceback.print_exc()  # Debug line
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def complete_quiz(request, quiz_id):
    """Complete the quiz and calculate results"""
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Get quiz
    quiz = get_object_or_404(RoleQuiz, id=quiz_id, user=user)
    
    if quiz.status != 'in_progress':
        return redirect('resumeanalysis:quiz_results', quiz_id=quiz.id)
    
    # Get all responses
    responses = QuizResponse.objects.filter(quiz=quiz)
    
    # Calculate scores
    response_data = [
        {
            'question_id': resp.session_question_id,
            'selected_option': resp.user_answer
        }
        for resp in responses
    ]
    
    scores = calculate_quiz_scores(response_data, target_role=quiz.target_role)
    
    # Update quiz with scores
    quiz.general_ability_score = scores.get('general_ability', 0)
    quiz.tech_fundamentals_score = scores.get('tech_fundamentals', 0)
    quiz.role_specific_score = scores.get('role_specific', 0)
    quiz.total_score = scores.get('total', 0)
    quiz.status = 'completed'
    quiz.completed_at = timezone.now()
    
    # Calculate time taken
    start_time = request.session.get(f'quiz_{quiz_id}_start_time', time.time())
    quiz.time_taken = int(time.time() - start_time)
    quiz.save()
    
    # Calculate eligibility
    eligibility = calculate_role_eligibility(quiz.resume_analysis, quiz)
    
    # Save eligibility results
    with transaction.atomic():
        role_eligibility = RoleEligibility.objects.create(
            user=user,
            quiz=quiz,
            resume_analysis=quiz.resume_analysis,
            role_name=eligibility['target_role'],
            eligibility_score=eligibility['total_eligibility'],
            is_eligible=eligibility['is_eligible'],
            general_score=quiz.general_ability_score,
            tech_score=quiz.tech_fundamentals_score,
            role_score=quiz.role_specific_score,
            resume_score=quiz.resume_analysis.ats_score,
            recommended_roles=eligibility['recommended_roles'],
            improvement_suggestions=eligibility['improvement_areas']
        )
        
        # Save recommended roles
        for rec in eligibility['recommended_roles']:
            RecommendedRole.objects.create(
                user=user,
                eligibility=role_eligibility,
                role_name=rec['role_name'],
                match_percentage=rec['match_percentage'],
                match_reasons=rec['match_reasons']
            )
    
    # Clear quiz session data
    session_keys = [
        f'quiz_{quiz_id}_questions',
        f'quiz_{quiz_id}_start_time'
    ]
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    # Check if eligible or needs warning
    if eligibility['total_eligibility'] < 60:
        return redirect('resumeanalysis:quiz_results', quiz_id=quiz.id)
    else:
        return redirect('resumeanalysis:quiz_results', quiz_id=quiz.id)
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user = UserRegistration.objects.get(userid=request.session['username'])
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Get quiz and eligibility
    quiz = get_object_or_404(RoleQuiz, id=quiz_id, user=user)
    eligibility = calculate_role_eligibility(quiz.resume_analysis, quiz)
    
    if request.method == 'POST':
        form = RoleSelectionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == 'continue':
                # Continue to role-specific mock test
                return redirect(f'/mock-test/roles/{quiz.target_role}/')
            else:
                # Switch to general mock test
                return redirect('/mock-test/')
    else:
        form = RoleSelectionForm()
    
    return render(request, 'resumeanalysis/quiz_results.html', {
        'quiz': quiz,
        'eligibility': eligibility,
        'form': form,
        'user': user
    })

def quiz_results(request, quiz_id):
    """Display comprehensive quiz results"""
    print(f"=== Quiz Results Request ===")  # Debug line
    print(f"Quiz ID: {quiz_id}")  # Debug line
    print(f"Quiz ID type: {type(quiz_id)}")  # Debug line
    
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        print("User not in session")  # Debug line
        # For testing purposes, try to get the quiz owner
        try:
            quiz = RoleQuiz.objects.get(id=quiz_id)
            print(f"Found quiz without auth: {quiz.id}, owner: {quiz.user.userid}")  # Debug line
            # Set user to quiz owner for testing
            user = quiz.user
        except Exception as e:
            print(f"Error getting quiz without auth: {e}")  # Debug line
            return redirect('user_login')
    else:
        try:
            user_id = request.session.get('username') or request.session.get('userid')
            user = UserRegistration.objects.get(userid=user_id)
            print(f"Found user: {user.userid}")  # Debug line
        except UserRegistration.DoesNotExist:
            print("User not found in database")  # Debug line
            return redirect('user_login')
    
    # Get quiz and related data
    try:
        quiz = get_object_or_404(RoleQuiz, id=quiz_id, user=user)
        print(f"Found quiz: {quiz.id}")  # Debug line
        print(f"Quiz status: {quiz.status}")  # Debug line
        
        # Get actual quiz stats
        responses = QuizResponse.objects.filter(quiz=quiz)
        total_questions = responses.count()
        correct_count = responses.filter(is_correct=True).count()
        
        # Fix: If quiz is completed but scores are all zero, recalculate them from responses
        if quiz.status == 'completed' and total_questions > 0 and \
           quiz.general_ability_score == 0 and quiz.tech_fundamentals_score == 0 and quiz.role_specific_score == 0:
            response_data = [
                {'question_id': r.session_question_id, 'selected_option': r.user_answer}
                for r in responses
            ]
            scores = calculate_quiz_scores(response_data, target_role=quiz.target_role)
            
            quiz.general_ability_score = scores.get('general_ability', 0)
            quiz.tech_fundamentals_score = scores.get('tech_fundamentals', 0)
            quiz.role_specific_score = scores.get('role_specific', 0)
            quiz.total_score = scores.get('total', 0)
            quiz.save()
            
            # Also update existing eligibility record if it exists
            try:
                eligibility_rec = RoleEligibility.objects.get(quiz=quiz)
                resume_score = quiz.resume_analysis.ats_score if quiz.resume_analysis else 75
                eligibility_rec.eligibility_score = (resume_score * 0.4) + (quiz.total_score * 0.6)
                eligibility_rec.general_score = quiz.general_ability_score
                eligibility_rec.tech_score = quiz.tech_fundamentals_score
                eligibility_rec.role_score = quiz.role_specific_score
                eligibility_rec.save()
            except Exception:
                pass

        # Calculate weighted contributions
        weighted_general_contribution = quiz.general_ability_score * 0.3
        weighted_tech_contribution = quiz.tech_fundamentals_score * 0.3
        weighted_role_contribution = quiz.role_specific_score * 0.4
        
        # Calculate accuracy
        accuracy = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0

    except Exception as e:
        print(f"Error getting quiz: {e}")  # Debug line
        raise e
    
    try:
        eligibility = RoleEligibility.objects.get(quiz=quiz)
        recommended_roles = RecommendedRole.objects.filter(
            eligibility=eligibility
        ).order_by('-match_percentage')
        # Calculate warning level based on score
        score = eligibility.eligibility_score
        if score >= 75:
            warning_level = 'low'
        elif score >= 55:
            warning_level = 'medium'
        else:
            warning_level = 'high'

        # Use existing eligibility data
        eligibility_data = {
            'target_role': quiz.target_role,
            'eligibility_score': eligibility.eligibility_score,
            'recommended_roles': [role.role_name for role in recommended_roles],
            'improvement_areas': getattr(eligibility, 'improvement_suggestions', []),
            'warning_level': warning_level
        }
    except RoleEligibility.DoesNotExist:
        # Calculate if not exists
        if quiz.resume_analysis:
            eligibility_data = calculate_role_eligibility(quiz.resume_analysis, quiz)
            eligibility = None
            recommended_roles = eligibility_data.get('recommended_roles', [])
        else:
            # No resume analysis available, create basic results
            eligibility_data = {
                'target_role': quiz.target_role,
                'eligibility_score': 75.0,  # Default score
                'recommended_roles': [quiz.target_role],
                'improvement_areas': [],
                'warning_level': 'low'
            }
            eligibility = None
            recommended_roles = []
            total_questions = 30 # Fallback
            correct_count = 0
            accuracy = 0
    
    # Determine final score and risk level
    final_score = quiz.total_score
    risk_level = "Medium Risk - trainable"
    
    if eligibility:
        final_score = eligibility.eligibility_score
        if final_score >= 75:
            risk_level = "Low Risk - job ready"
        elif final_score >= 55:
            risk_level = "Medium Risk - trainable"
        else:
            risk_level = "High Risk - career mismatch"
    elif eligibility_data:
        final_score = eligibility_data.get('eligibility_score', quiz.total_score)
        risk_level = eligibility_data.get('warning_level', 'Medium Risk - trainable')
        if risk_level == 'low': risk_level = "Low Risk - job ready"
        elif risk_level == 'medium': risk_level = "Medium Risk - trainable"
        elif risk_level == 'high': risk_level = "High Risk - career mismatch"

    return render(request, 'resumeanalysis/result.html', {
        'quiz': quiz,
        'eligibility': eligibility,
        'recommended_roles': recommended_roles,
        'overall_score': final_score,
        'quiz_score': quiz.total_score,
        'risk_level': risk_level,
        'weighted_general_contribution': weighted_general_contribution,
        'weighted_tech_contribution': weighted_tech_contribution,
        'weighted_role_contribution': weighted_role_contribution,
        'test_attempt': {
            'questions_answered': total_questions,
            'questions_correct': correct_count,
            'accuracy_percentage': accuracy,
            'time_taken': quiz.time_taken,
            'stroke_dashoffset': 552.9 - (552.9 * final_score / 100),  # For circular progress based on final score
            'tech_score': quiz.tech_fundamentals_score,
            'role_score': quiz.role_specific_score,
            'general_score': quiz.general_ability_score
        }
    })

def delete_resume(request, analysis_id):
    """Delete a resume analysis to allow new upload"""
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    try:
        # Get the resume analysis
        analysis = ResumeAnalysis.objects.get(id=analysis_id, user=user)
        
        # Delete the analysis and associated files
        if analysis.resume_file:
            # Delete the file from storage
            if default_storage.exists(analysis.resume_file.name):
                default_storage.delete(analysis.resume_file.name)
        
        # Delete the analysis record
        analysis.delete()
        
        messages.success(request, "Resume deleted successfully. You can now upload a new resume.")
        return redirect('upload')
        
    except ResumeAnalysis.DoesNotExist:
        messages.error(request, "Resume not found.")
        return redirect('upload')
    except Exception as e:
        messages.error(request, f"Error deleting resume: {str(e)}")
        return redirect('upload')

def dashboard(request):
    """Resume analysis dashboard"""
    # Get user from existing session system
    if 'username' not in request.session and 'userid' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('user_login')
    
    try:
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Get user's analyses
    analyses = ResumeAnalysis.objects.filter(user=user).order_by('-created_at')
    quizzes = RoleQuiz.objects.filter(user=user).order_by('-created_at')
    eligibilities = RoleEligibility.objects.filter(user=user).order_by('-created_at')
    
    return render(request, 'resumeanalysis/dashboard.html', {
        'user': user,
        'analyses': analyses,
        'quizzes': quizzes,
        'eligibilities': eligibilities
    })

def start_test(request, role_id=None):
    """Start the career assessment test"""
    # Check for custom session authentication first (UserRegistration model)
    if 'username' not in request.session and 'userid' not in request.session:
        return redirect('user_login')
    
    try:
        # Try to get user by session first (primary auth method)
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    except Exception as e:
        messages.error(request, f"Error accessing user: {str(e)}")
        return redirect('user_login')
    
    # Handle POST request to start test
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        return redirect('resumeanalysis:start_test_with_role', role_id=role_id or '0')
    
    # Show test start page for GET request
    return render(request, 'resumeanalysis/test_start.html', {
        'user': user,
        'role_name': get_role_name(role_id) if role_id else 'General Assessment'
    })

def start_test_with_role(request, role_id):
    """Start test with specific role"""
    # Check for custom session authentication first (UserRegistration model)
    if 'username' not in request.session and 'userid' not in request.session:
        return redirect('user_login')
    
    try:
        # Try to get user by session first (primary auth method)
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    except Exception as e:
        messages.error(request, f"Error accessing user: {str(e)}")
        return redirect('user_login')
    
    # Get or create test questions
    questions = get_test_questions()
    
    # Prepare test data for frontend (simplified approach)
    test_data = {
        'attempt_id': str(uuid.uuid4()),  # Temporary ID
        'questions': questions,
        'total_questions': len(questions),
        'time_limit': 60,
        'role_name': get_role_name(role_id) if role_id != '0' else 'General Assessment'
    }
    
    return render(request, 'resumeanalysis/test.html', {
        'user': user,
        'test_data': test_data,
        'role_name': test_data['role_name']
    })

def submit_test(request):
    """Handle test submission"""
    # Check for custom session authentication first (UserRegistration model)
    if 'username' not in request.session and 'userid' not in request.session:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Try to get user by session first (primary auth method)
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    
    try:
        # Get test data
        data = json.loads(request.body)
        answers = data.get('answers', {})
        marked_for_review = data.get('marked_for_review', [])
        scores = data.get('scores', {})
        time_taken = data.get('time_taken', 0)
        
        # For now, just return success with a simple results page
        # In production, you would save to database here
        
        return JsonResponse({
            'success': True,
            'redirect_url': '/resumeanalysis/test-results/simple/'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def test_results_simple(request):
    """Simple test results page (without database models)"""
    # Check for custom session authentication first (UserRegistration model)
    if 'username' not in request.session and 'userid' not in request.session:
        return redirect('user_login')
    
    try:
        # Try to get user by session first (primary auth method)
        user_id = request.session.get('username') or request.session.get('userid')
        user = UserRegistration.objects.get(userid=user_id)
    except UserRegistration.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('user_login')
    
    # Mock results for now
    mock_results = {
        'total_score': 75,
        'general_score': 70,
        'tech_score': 80,
        'role_score': 75,
        'questions_answered': 10,
        'questions_correct': 8,
        'time_taken': 1800  # 30 minutes
    }
    
    return render(request, 'resumeanalysis/test_results_simple.html', {
        'user': user,
        'results': mock_results
    })

# Helper functions
def get_test_questions():
    """Get test questions for all categories"""
    questions = []
    
    # General questions (30%)
    general_questions = [
        {
            'id': 'gen_1',
            'category': 'general',
            'text': 'What is your primary career goal for the next 3-5 years?',
            'description': 'Select the option that best describes your career aspirations.',
            'options': [
                'Senior leadership position',
                'Technical expertise specialization',
                'Work-life balance optimization',
                'Starting own business'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'gen_2',
            'category': 'general',
            'text': 'How do you prefer to work in a team environment?',
            'description': 'Choose your preferred team collaboration style.',
            'options': [
                'Lead and coordinate team efforts',
                'Contribute specialized expertise',
                'Support and facilitate team harmony',
                'Work independently but coordinate when needed'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'gen_3',
            'category': 'general',
            'text': 'What motivates you most in your career?',
            'description': 'Select your primary career motivation factor.',
            'options': [
                'Financial compensation and benefits',
                'Learning and growth opportunities',
                'Work impact and recognition',
                'Job security and stability'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        }
    ]
    
    # Tech questions (30%)
    tech_questions = [
        {
            'id': 'tech_1',
            'category': 'tech',
            'text': 'Which programming paradigm do you prefer for complex projects?',
            'description': 'Choose your preferred programming approach.',
            'options': [
                'Object-Oriented Programming',
                'Functional Programming',
                'Procedural Programming',
                'Hybrid approach based on requirements'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'tech_2',
            'category': 'tech',
            'text': 'How do you approach debugging complex issues?',
            'description': 'Select your debugging methodology.',
            'options': [
                'Systematic elimination of variables',
                'Code review and pair programming',
                'Automated testing and logging',
                'Intuition and experience-based approach'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'tech_3',
            'category': 'tech',
            'text': 'What is your experience with cloud technologies?',
            'description': 'Rate your cloud computing expertise.',
            'options': [
                'Expert - Multiple cloud platforms certified',
                'Advanced - Production experience with major clouds',
                'Intermediate - Basic deployment and management',
                'Beginner - Learning cloud concepts'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        }
    ]
    
    # Role questions (40%)
    role_questions = [
        {
            'id': 'role_1',
            'category': 'role',
            'text': 'How do you handle project deadlines and pressure?',
            'description': 'Describe your approach to time-sensitive projects.',
            'options': [
                'Prioritize tasks and focus on critical path',
                'Work extended hours to meet deadlines',
                'Negotiate realistic timelines with stakeholders',
                'Delegate tasks effectively to team members'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'role_2',
            'category': 'role',
            'text': 'What is your approach to learning new technologies?',
            'description': 'How do you stay updated with technological changes?',
            'options': [
                'Structured learning through courses and certifications',
                'Hands-on experimentation and side projects',
                'Industry conferences and networking',
                'On-the-job learning as needed'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'role_3',
            'category': 'role',
            'text': 'How do you measure success in your role?',
            'description': 'What metrics indicate successful performance?',
            'options': [
                'Quantitative results and KPI achievement',
                'Team satisfaction and collaboration',
                'Innovation and process improvements',
                'Client satisfaction and feedback'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        },
        {
            'id': 'role_4',
            'category': 'role',
            'text': 'What leadership style do you prefer?',
            'description': 'Choose your preferred leadership approach.',
            'options': [
                'Transformational - Inspire and motivate team',
                'Servant - Support and enable team success',
                'Democratic - Collaborative decision making',
                'Autocratic - Clear direction and control'
            ],
            'correct_answer': 0,
            'difficulty': 'medium'
        }
    ]
    
    questions.extend(general_questions)
    questions.extend(tech_questions)
    questions.extend(role_questions)
    
    return questions

def get_role_name(role_id):
    """Get role name from role ID"""
    role_mapping = {
        '1': 'Software Developer',
        '2': 'Data Scientist',
        '3': 'Product Manager',
        '4': 'DevOps Engineer',
        '5': 'UI/UX Designer'
    }
    return role_mapping.get(str(role_id), 'General Assessment')

def create_role_eligibility(user, scores):
    """Create role eligibility based on test scores"""
    total_score = scores.get('total', 0)
    
    # Define role requirements
    roles = [
        {'name': 'Software Developer', 'min_score': 70, 'category': 'tech'},
        {'name': 'Data Scientist', 'min_score': 75, 'category': 'tech'},
        {'name': 'Product Manager', 'min_score': 65, 'category': 'role'},
        {'name': 'DevOps Engineer', 'min_score': 70, 'category': 'tech'},
        {'name': 'UI/UX Designer', 'min_score': 60, 'category': 'role'}
    ]
    
    for role in roles:
        eligibility_score = calculate_eligibility_score(scores, role['category'])
        
        RoleEligibility.objects.update_or_create(
            user=user,
            role_name=role['name'],
            defaults={
                'eligibility_score': eligibility_score,
                'is_eligible': eligibility_score >= role['min_score'],
                'recommended_roles': role['name'] if eligibility_score >= role['min_score'] else None,
                'skill_gaps': get_skill_gaps(scores, role['category']) if eligibility_score < role['min_score'] else None
            }
        )

def calculate_eligibility_score(scores, category):
    """Calculate eligibility score for a specific category"""
    category_scores = {
        'tech': scores.get('tech', 0),
        'role': scores.get('role', 0),
        'general': scores.get('general', 0)
    }
    
    if category in category_scores:
        return category_scores[category]
    
    return scores.get('total', 0)

def get_skill_gaps(scores, category):
    """Identify skill gaps based on scores"""
    gaps = []
    
    if category == 'tech' and scores.get('tech', 0) < 70:
        gaps.append('Technical skills need improvement')
    if category == 'role' and scores.get('role', 0) < 70:
        gaps.append('Role-specific competencies need development')
    if scores.get('general', 0) < 60:
        gaps.append('General aptitude areas need attention')
    
    return gaps if gaps else None
