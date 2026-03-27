from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
from functools import wraps
from users.models import UserRegistration
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, F, Sum, Avg
from django.urls import reverse
from datetime import date, timedelta
import json
import uuid

def session_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'userid' not in request.session:
            messages.error(request, "Please login first.")
            return redirect('users:user_login')
        
        try:
            # Get the user object from the custom session userid
            user = UserRegistration.objects.get(userid=request.session['userid'])
            request.user = user
        except UserRegistration.DoesNotExist:
             messages.error(request, "User session invalid.")
             return redirect('users:user_login')
             
        return view_func(request, *args, **kwargs)
    return wrapper

from .models import (
    PersonalizedPlan, WeeklyPlan, DailyTask, PlanProgress,
    AssessmentResult, WeakTopicDiagnosis, CorrectionPlan, FinalRetest,
    UserXP, XPReward, UserStreak, DailyActivity, ResumeImpact,
    AssessmentSession
)
from resumeanalysis.models import ResumeAnalysis
from users.views_mock_test import ROLE_TESTS, LANGUAGE_TESTS

@session_login_required
def personalized_plan_dashboard(request):
    """Main dashboard for personalized plan system"""
    try:
        # Get or create user XP record
        user_xp, created = UserXP.objects.get_or_create(user=request.user)
        
        # Get or create user streak record
        user_streak, created = UserStreak.objects.get_or_create(user=request.user)
        
        # Get active personalized plan
        active_plan = PersonalizedPlan.objects.filter(user=request.user, status='active').first()
        
        # Get recent XP rewards (Filtered by active plan if exists)
        if active_plan:
            recent_rewards = XPReward.objects.filter(
                user_xp=user_xp,
                created_at__gte=active_plan.created_at
            ).order_by('-created_at')[:10]
        else:
            recent_rewards = []
        
        # Get daily activity for last 30 days for heatmap
        today = timezone.now().date()
        last_30_days_start = today - timedelta(days=29)
        
        activities_query = DailyActivity.objects.filter(
            user=request.user, 
            date__gte=last_30_days_start,
            date__lte=today
        )
        activity_map = {activity.date: activity for activity in activities_query}
        
        # Calculate Plan-Specific Streak
        current_plan_streak = 0
        if active_plan:
            plan_start_date = active_plan.created_at.date()
            
            # Get all active dates for this user since plan start
            active_dates = DailyActivity.objects.filter(
                user=request.user,
                is_active=True,
                date__gte=plan_start_date
            ).values_list('date', flat=True).order_by('-date')
            
            active_dates_set = set(active_dates)
            
            # Check streak logic (Today OR Yesterday must be active to maintain streak)
            if today in active_dates_set:
                current_plan_streak = 1
                check_date = today - timedelta(days=1)
                while check_date >= plan_start_date and check_date in active_dates_set:
                    current_plan_streak += 1
                    check_date -= timedelta(days=1)
            elif (today - timedelta(days=1)) in active_dates_set:
                current_plan_streak = 1
                check_date = today - timedelta(days=2)
                while check_date >= plan_start_date and check_date in active_dates_set:
                    current_plan_streak += 1
                    check_date -= timedelta(days=1)
        
        heatmap_data = []
        for i in range(30):
            date_cursor = last_30_days_start + timedelta(days=i)
            activity = activity_map.get(date_cursor)
            
            # Only show activity as active if it's within the current plan's lifespan
            is_active = False
            if activity and activity.is_active:
                if active_plan and date_cursor >= active_plan.created_at.date():
                    is_active = True
            
            heatmap_data.append({
                'date': date_cursor,
                'is_active': is_active
            })

        # Calculate Test Stats (Total Tests and Avg Score)
        total_tests = AssessmentResult.objects.filter(user=request.user).count()
        avg_score_agg = AssessmentResult.objects.filter(user=request.user).aggregate(Avg('score'))
        avg_score = round(avg_score_agg['score__avg'] or 0)
        
        # Get daily activity for current month
        current_month = today.replace(day=1)
        daily_activities = DailyActivity.objects.filter(
            user=request.user,
            date__gte=current_month
        ).order_by('date')
        
        # Calculate chart data for Skill Radar
        chart_labels = []
        chart_values = []
        
        if active_plan:
            weekly_plans = WeeklyPlan.objects.filter(personalized_plan=active_plan).order_by('week_number')
            
            week_mapping = {
                1: "Fundamentals",
                2: "Advanced",
                3: "Best Practices",
                4: "Professionalism"
            }
            
            # Ensure we have data for all 4 weeks even if they don't exist yet (though they should)
            for i in range(1, 5):
                week = next((w for w in weekly_plans if w.week_number == i), None)
                label = week_mapping.get(i, f"Week {i}")
                chart_labels.append(label)
                
                if week:
                    total = DailyTask.objects.filter(weekly_plan=week).count()
                    completed = DailyTask.objects.filter(weekly_plan=week, status='completed').count()
                    val = int((completed / total) * 100) if total > 0 else 0
                else:
                    val = 0
                chart_values.append(val)
        else:
            # Default empty chart if no active plan
            chart_labels = ["Fundamentals", "Advanced", "Best Practices", "Professionalism"]
            chart_values = [0, 0, 0, 0]
        
        # Add dynamic stats
        chart_labels.append("Consistency")
        streak_val = min(int((user_streak.current_streak / 14) * 100), 100) # 14 days for max consistency score
        chart_values.append(streak_val)
        
        chart_labels.append("Experience")
        xp_val = user_xp.level_progress # Already 0-100
        chart_values.append(xp_val)
        
        # Calculate circular progress offset (Circumference is 502.4)
        plan_circle_offset = 502.4 # Default empty
        if active_plan:
             percentage = active_plan.completion_percentage
             plan_circle_offset = 502.4 - (percentage / 100) * 502.4

        context = {
            'user_xp': user_xp,
            'user_streak': user_streak,
            'current_plan_streak': current_plan_streak if active_plan else 0,
            'active_plan': active_plan,
            'recent_rewards': recent_rewards,
            'daily_activities': daily_activities,
            'heatmap_data': heatmap_data,
            'total_tests': total_tests,
            'avg_score': avg_score,
            'chart_labels': json.dumps(chart_labels),
            'chart_values': json.dumps(chart_values),
            'plan_circle_offset': plan_circle_offset,
        }
        
        return render(request, 'personalizedplan/dashboard.html', context)
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'personalizedplan/dashboard.html', {})

@session_login_required
def api_dashboard_stats(request):
    """API endpoint to get real-time dashboard statistics"""
    try:
        # Get or create user XP record
        user_xp, _ = UserXP.objects.get_or_create(user=request.user)
        
        # Get or create user streak record
        user_streak, _ = UserStreak.objects.get_or_create(user=request.user)
        
        # Get active personalized plan
        active_plan = PersonalizedPlan.objects.filter(user=request.user, status='active').first()
        
        data = {
            'user_xp': {
                'current_level': user_xp.current_level,
                'total_xp': user_xp.total_xp,
                'level_progress': user_xp.level_progress,
            },
            'user_streak': {
                'current_streak': user_streak.current_streak,
                'longest_streak': user_streak.longest_streak,
                'total_days_active': user_streak.total_days_active,
            },
        }
        
        if active_plan:
            # Calculate Plan-Specific Streak for API
            plan_start_date = active_plan.created_at.date()
            today = timezone.now().date()
            current_plan_streak = 0
            
            # Get all active dates for this user since plan start
            active_dates = DailyActivity.objects.filter(
                user=request.user,
                is_active=True,
                date__gte=plan_start_date
            ).values_list('date', flat=True).order_by('-date')
            
            active_dates_set = set(active_dates)
            
            if today in active_dates_set:
                current_plan_streak = 1
                check_date = today - timedelta(days=1)
                while check_date >= plan_start_date and check_date in active_dates_set:
                    current_plan_streak += 1
                    check_date -= timedelta(days=1)
            elif (today - timedelta(days=1)) in active_dates_set:
                current_plan_streak = 1
                check_date = today - timedelta(days=2)
                while check_date >= plan_start_date and check_date in active_dates_set:
                    current_plan_streak += 1
                    check_date -= timedelta(days=1)

            data['active_plan'] = {
                'current_week': active_plan.current_week,
                'current_day': active_plan.current_day,
                'total_xp_earned': active_plan.total_xp_earned,
                'target_xp': active_plan.target_xp,
                'xp_progress_percentage': active_plan.xp_progress_percentage,
                'completion_percentage': active_plan.completion_percentage,
                'streak_multiplier': active_plan.streak_multiplier,
                'tasks_completed': active_plan.tasks_completed,
                'total_tasks': active_plan.total_tasks,
                'current_plan_streak': current_plan_streak,
            }
            
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@session_login_required
def start_personalized_plan(request):
    """Start personalized plan selection"""
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        target = request.POST.get('target')
        
        if not target:
            messages.error(request, "Please select a target role or language.")
            return redirect('personalizedplan:start')
        
        # Check if user already has active plan
        existing_plan = PersonalizedPlan.objects.filter(user=request.user, status='active').first()
        if existing_plan:
            messages.warning(request, "You already have an active personalized plan.")
            return redirect('personalizedplan:dashboard')
        
        # Create assessment session
        import uuid
        session_key = str(uuid.uuid4())[:8]
        
        assessment_session = AssessmentSession.objects.create(
            user=request.user,
            session_key=session_key,
            plan_type=plan_type,
            target_role_language=target,
            status='started'
        )
        
        # Store assessment data in session
        request.session['personalized_plan_data'] = {
            'plan_type': plan_type,
            'target': target,
            'session_key': session_key
        }
        
        # Redirect to assessment interface
        return redirect('personalizedplan:testsystem:start_initial', category=target)
    
    # Get available roles and languages
    roles = list(ROLE_TESTS.keys())
    languages = list(LANGUAGE_TESTS.keys())
    
    return render(request, 'personalizedplan/start_plan.html', {
        'roles': roles,
        'languages': languages
    })

@session_login_required
def plan_detail(request, plan_id):
    """Display detailed plan with blur/lock system"""
    plan = get_object_or_404(PersonalizedPlan, id=plan_id, user=request.user)
    
    # Get weekly plans with daily tasks
    weekly_plans = WeeklyPlan.objects.filter(personalized_plan=plan).order_by('week_number')
    
    # Debug: Check if any weekly plan has 'failed' status
    failed_weeks = weekly_plans.filter(status='failed').exists()
    
    # Structure data for template
    plan_data = []
    for week_plan in weekly_plans:
        daily_tasks = DailyTask.objects.filter(weekly_plan=week_plan).order_by('day_number')
        
        # Check for revised tasks
        has_revised_tasks = daily_tasks.filter(topic__icontains="Revised Plan").exists()
        
        # Get top failed topics if available
        top_failed_topics = []
        if has_revised_tasks:
            # Try to get the latest weak topic diagnosis for this week
            latest_diagnosis = WeakTopicDiagnosis.objects.filter(
                assessment_result__personalized_plan=plan,
                assessment_result__test_type='weekly'
            ).order_by('-created_at').first()
            
            if latest_diagnosis and latest_diagnosis.weak_topics:
                top_failed_topics = latest_diagnosis.weak_topics.get('top_topics', [])
        
        plan_data.append({
            'week': week_plan,
            'tasks': daily_tasks,
            'has_revised': has_revised_tasks,
            'top_failed_topics': top_failed_topics
        })
    
    # Get user progress
    progress = PlanProgress.objects.filter(user=request.user, personalized_plan=plan).first()
    
    # Get user XP and Streak
    user_xp, _ = UserXP.objects.get_or_create(user=request.user)
    user_streak, _ = UserStreak.objects.get_or_create(user=request.user)
    
    return render(request, 'personalizedplan/plan_detail.html', {
        'plan': plan,
        'plan_data': plan_data,
        'progress': progress,
        'user_xp': user_xp,
        'user_streak': user_streak,
        'debug_failed': failed_weeks  # Temporary debug flag
    })

@session_login_required
def reset_plan(request):
    """Reset/Delete the user's active personalized plan"""
    if request.method == 'POST':
        # Find active plan
        active_plan = PersonalizedPlan.objects.filter(user=request.user, status='active').first()
        if active_plan:
            active_plan.delete()
            messages.success(request, "Your personalized plan has been reset successfully.")
        else:
            messages.warning(request, "No active plan found to reset.")
            
        return redirect('personalizedplan:start')
    
    return redirect('personalizedplan:dashboard')

@session_login_required
def delete_plan(request):
    """Delete the user's active personalized plan"""
    if request.method == 'POST':
        # Find active plan
        active_plan = PersonalizedPlan.objects.filter(user=request.user, status='active').first()
        if active_plan:
            active_plan.delete()
            messages.success(request, "Your personalized plan has been deleted successfully.")
        else:
            messages.warning(request, "No active plan found to delete.")
            
    return redirect('personalizedplan:dashboard')

@session_login_required
def complete_daily_task(request, task_id):
    """Mark daily task as complete and award XP"""
    if request.method == 'POST':
        task = get_object_or_404(DailyTask, id=task_id)
        
        # Check if task belongs to user's active plan
        if task.weekly_plan.personalized_plan.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        if task.status == 'completed':
            return JsonResponse({'error': 'Task already completed'}, status=400)
        
        # Mark task as completed
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        # Award XP
        user_xp, created = UserXP.objects.get_or_create(user=request.user)
        user_xp.total_xp += task.xp_reward
        user_xp.save()
        
        # Create XP reward record
        XPReward.objects.create(
            user_xp=user_xp,
            reward_type='daily_task',
            xp_amount=task.xp_reward,
            reason=f"Completed: {task.topic}",
            related_object_id=task.id
        )
        
        # Update streak
        update_user_streak(request.user)
        
        # Log daily activity
        log_daily_activity(request.user, task)
        
        # Check and unlock next task
        unlock_next_task(task)
        
        # Check for level up
        check_level_up(user_xp)
        
        return JsonResponse({
            'success': True,
            'xp_earned': task.xp_reward,
            'total_xp': user_xp.total_xp,
            'level': user_xp.current_level
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@session_login_required
def take_weekly_test(request, week_id):
    """Handle weekly test functionality - Redirect to new Test System"""
    return redirect('personalizedplan:testsystem:start_weekly', week_id=week_id)

@session_login_required
def create_plan_from_assessment(request):
    """Create personalized plan based on assessment results"""
    # Get assessment data from session
    plan_data = request.session.get('personalized_plan_data')
    if not plan_data:
        messages.error(request, "Assessment data not found. Please start again.")
        return redirect('personalizedplan:start')
    
    plan_type = plan_data['plan_type']
    target = plan_data['target']
    
    # Get the latest mock test result for this user
    from resumeanalysis.models import TestAttempt
    
    # Find the most recent test result for this user
    test_result = TestAttempt.objects.filter(
        user=request.user,
        status='completed'
    ).order_by('-started_at').first()
    
    if not test_result:
        messages.error(request, "No assessment test found. Please take the assessment first.")
        return redirect('personalizedplan:start')
    
    # Create new personalized plan
    plan = PersonalizedPlan.objects.create(
        user=request.user,
        plan_type=plan_type,
        target_role_language=target,
        status='active'
    )
    
    # Create initial assessment result linked to plan
    # Calculate weak areas from test results
    weak_areas_counts = {}
    incorrect_answers = test_result.answers.filter(is_correct=False)
    
    for answer in incorrect_answers:
        category = answer.question_category
        if category:
            weak_areas_counts[category] = weak_areas_counts.get(category, 0) + 1
            
    # Convert to list of weak areas (categories with failures)
    # Sort by count descending to prioritize most weak areas
    weak_areas_list = sorted(weak_areas_counts.keys(), key=lambda x: weak_areas_counts[x], reverse=True)

    assessment = AssessmentResult.objects.create(
        user=request.user,
        personalized_plan=plan,
        test_type='initial',
        score=test_result.total_score, # This is percentage (0-100)
        total_questions=test_result.total_questions,
        weak_areas=weak_areas_counts  # Store the counts dict for detailed record
    )
    
    # Generate weekly plans based on assessment results
    generate_personalized_plan(plan, plan_type, target, test_result.total_score, weak_areas_list)
    
    # Clear session data
    if 'personalized_plan_data' in request.session:
        del request.session['personalized_plan_data']
    
    messages.success(request, f"Personalized plan created based on your assessment! Score: {test_result.total_score}%")
    return redirect('personalizedplan:plan_detail', plan_id=plan.id)

@session_login_required
def resume_impact_dashboard(request):
    """Display resume improvement tracking"""
    # Get resume impacts for user
    impacts = ResumeImpact.objects.filter(user=request.user).order_by('-created_at')
    
    # Get latest resume analysis
    latest_analysis = ResumeAnalysis.objects.filter(user=request.user).order_by('-created_at').first()
    
    return render(request, 'personalizedplan/resume_impact.html', {
        'impacts': impacts,
        'latest_analysis': latest_analysis
    })

def generate_personalized_plan(plan, plan_type, target, assessment_score=None, weak_areas=None):
    """Generate 3-4 week personalized plan based on assessment"""
    
    # Use weak areas to customize topics if available
    week_topics = get_week_topics(plan_type, target, assessment_score, weak_areas)
    
    for week_num in range(1, 5):  # 4 weeks
        # Ensure we have topics for this week
        if week_num not in week_topics:
             continue

        week_plan = WeeklyPlan.objects.create(
            personalized_plan=plan,
            week_number=week_num,
            skill_focus=week_topics[week_num]['skill_focus'],
            topics=week_topics[week_num]['topics'],
            status='locked' if week_num > 1 else 'in_progress'
        )
        
        # Create daily tasks for each week
        topics_list = week_topics[week_num]['topics']
        for day_num in range(1, 8):  # 7 days
            # Handle case where we might have fewer topics than days
            if day_num <= len(topics_list):
                topic_name = topics_list[day_num-1]
                description = f"Focus on mastering {topic_name}. Review core concepts and complete practical exercises."
            else:
                topic_name = f"{target} Practice Day {day_num}"
                description = f"General practice and review of this week's concepts."

            DailyTask.objects.create(
                weekly_plan=week_plan,
                day_number=day_num,
                topic=topic_name,
                description=description,
                status='unlocked' if week_num == 1 and day_num == 1 else 'locked'
            )
    
    # Create initial progress record
    PlanProgress.objects.create(
        user=plan.user,
        personalized_plan=plan,
        current_week=1,
        current_day=1
    )

def get_week_topics(plan_type, target, assessment_score=None, weak_areas=None):
    """Get topics for each week based on plan type, target, and assessment score"""
    
    # Default structure
    topics_structure = {
        1: {'skill_focus': f'{target} Fundamentals', 'topics': []},
        2: {'skill_focus': f'Advanced {target} Concepts', 'topics': []},
        3: {'skill_focus': f'{target} Best Practices', 'topics': []},
        4: {'skill_focus': f'Professional {target} Development', 'topics': []}
    }
    
    # If we have assessment data, customize the plan
    if assessment_score is not None:
        # Normalize score to percentage (assuming max score is 100 or passed as percentage)
        # If score is > 100, assume it's raw score out of N, but here we expect percentage
        score_percentage = float(assessment_score)
        
        # 1. Low Score (< 50%): Intensive Remediation Plan
        if score_percentage < 50:
            topics_structure[1]['skill_focus'] = f'{target} Crash Course (Remediation)'
            topics_structure[1]['topics'] = [
                f'{target} Absolute Basics: Syntax & Variables',
                'Control Flow: Loops & Conditionals', 
                'Data Structures: Arrays & Objects',
                'Functions & Scope Fundamentals',
                'Error Handling Basics',
                'Basic DOM Manipulation / IO',
                'Mini Project: Calculator or To-Do List'
            ]
            
            topics_structure[2]['skill_focus'] = f'{target} Core Strengthening'
            topics_structure[2]['topics'] = [
                'Object-Oriented Programming Basics',
                'Modules & File Structure',
                'Asynchronous Programming Basics',
                'Working with APIs (Fetch/Requests)',
                'Debugging Techniques 101',
                'Code Style & Formatting',
                'Mini Project: Data Fetcher'
            ]

        # 2. Medium Score (50-79%): Balanced Growth Plan
        elif score_percentage < 80:
            topics_structure[1]['skill_focus'] = f'{target} Core Refresher'
            topics_structure[1]['topics'] = [
                f'{target} Ecosystem & Environment Setup',
                'Advanced Data Structures',
                'Modern Syntax Features (ES6+/Python3+)',
                'Functional Programming Concepts',
                'Async Programming Deep Dive',
                'Error Handling Patterns',
                'Unit Testing Basics'
            ]
            
            topics_structure[2]['skill_focus'] = f'{target} Application Building'
            topics_structure[2]['topics'] = [
                'State Management Strategies',
                'Routing & Navigation',
                'Form Handling & Validation',
                'Authentication Flow Basics',
                'API Integration Patterns',
                'Performance Optimization Basics',
                'Project: CRUD Application'
            ]

        # 3. High Score (80%+): Accelerator Plan
        else:
            topics_structure[1]['skill_focus'] = f'{target} Advanced Mastery'
            topics_structure[1]['topics'] = [
                f'{target} Internals & Memory Management',
                'Design Patterns (Singleton, Factory, Observer)',
                'Performance Profiling & Optimization',
                'Security Best Practices (OWASP)',
                'Advanced Typing / Metaprogramming',
                'Scalable Architecture Principles',
                'Contribution to Open Source'
            ]
            
            topics_structure[2]['skill_focus'] = f'{target} System Design'
            topics_structure[2]['topics'] = [
                'Microservices vs Monoliths',
                'Database Design & ORM Optimization',
                'Caching Strategies (Redis/Memcached)',
                'Message Queues & Event Driven Arch',
                'CI/CD Pipelines (GitHub Actions)',
                'Docker & Containerization',
                'Project: Scalable Backend Service'
            ]

    else:
        # Fallback default topics
        topics_structure[1]['topics'] = [f'{target} Basics', 'Setup & Env', 'Variables & Types', 'Control Flow', 'Functions', 'Data Structures', 'Basic IO']
        topics_structure[2]['topics'] = ['OOP Concepts', 'Modules', 'Error Handling', 'Async Basics', 'APIs', 'JSON Handling', 'Mini Project']

    # Incorporate Weak Areas if available (Inject into Week 1 & 2)
    # weak_areas is expected to be a dict or list of topic strings
    if weak_areas:
        weak_topics_list = []
        if isinstance(weak_areas, dict):
             weak_topics_list = list(weak_areas.keys())
        elif isinstance(weak_areas, list):
             weak_topics_list = weak_areas
        
        # Inject up to 3 weak topics into Week 1
        for i, weak_topic in enumerate(weak_topics_list[:3]):
             if i < len(topics_structure[1]['topics']):
                  topics_structure[1]['topics'][i] = f"Focus Area: {weak_topic} (Review)"
        
        # Inject next 3 weak topics into Week 2
        for i, weak_topic in enumerate(weak_topics_list[3:6]):
             if i < len(topics_structure[2]['topics']):
                  topics_structure[2]['topics'][i] = f"Deep Dive: {weak_topic} (Practice)"

    # Fill Weeks 3 & 4 with standard advanced/professional content if empty
    if not topics_structure[3]['topics']:
        topics_structure[3]['topics'] = ['Clean Code Principles', 'Refactoring Techniques', 'Documentation Standards', 'Code Review Etiquette', 'Agile/Scrum Basics', 'Git Workflow (Branching/Merging)', 'Career Readiness: Resume Prep']
    
    if not topics_structure[4]['topics']:
        topics_structure[4]['topics'] = ['System Design Interviews', 'Algorithm Challenges', 'Behavioral Interview Prep', 'Mock Interview Practice', 'Portfolio Project Polish', 'Networking Strategies', 'Final Assessment Prep']

    return topics_structure

def update_user_streak(user):
    """Update user streak based on daily activity"""
    today = timezone.now().date()
    user_streak, created = UserStreak.objects.get_or_create(user=user)
    
    if user_streak.last_activity_date:
        if user_streak.last_activity_date == today - timedelta(days=1):
            # Consecutive day
            user_streak.current_streak += 1
            user_streak.total_days_active += 1
            
            # Award streak XP
            user_xp = UserXP.objects.get(user=user)
            streak_xp = user_streak.current_streak * 5
            user_xp.total_xp += streak_xp
            user_xp.save()
            
            XPReward.objects.create(
                user_xp=user_xp,
                reward_type='streak',
                xp_amount=streak_xp,
                reason=f"Streak Day {user_streak.current_streak}"
            )
        elif user_streak.last_activity_date < today - timedelta(days=1):
            # Streak broken
            user_streak.current_streak = 1
        else:
            # Same day - no change
            pass
    else:
        # First activity
        user_streak.current_streak = 1
        user_streak.total_days_active = 1
    
    user_streak.last_activity_date = today
    user_streak.save()
    
    # Update longest streak
    if user_streak.current_streak > user_streak.longest_streak:
        user_streak.longest_streak = user_streak.current_streak
        user_streak.save()

def log_daily_activity(user, task):
    """Log daily activity for tracking"""
    today = timezone.now().date()
    
    activity, created = DailyActivity.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'week_number': task.weekly_plan.week_number,
            'day_number': task.day_number,
            'is_active': True,
            'tasks_completed': 1,
            'xp_earned': task.xp_reward
        }
    )
    
    if not created:
        activity.tasks_completed += 1
        activity.xp_earned += task.xp_reward
        activity.save()

def unlock_next_task(completed_task):
    """Unlock the next task in sequence"""
    week_plan = completed_task.weekly_plan
    
    # Find next task in same week
    next_task = DailyTask.objects.filter(
        weekly_plan=week_plan,
        day_number=completed_task.day_number + 1,
        status='locked'
    ).first()
    
    if next_task:
        next_task.status = 'unlocked'
        next_task.save()
    else:
        # Check if all tasks in week are completed
        total_tasks = DailyTask.objects.filter(weekly_plan=week_plan).count()
        completed_tasks = DailyTask.objects.filter(
            weekly_plan=week_plan,
            status='completed'
        ).count()
        
        if completed_tasks == total_tasks and week_plan.status in ['in_progress', 'failed']:
            week_plan.status = 'ready_for_test'
            week_plan.save()

def calculate_extra_days(score, total_questions):
    """Calculate extra days needed based on test performance"""
    percentage = score / total_questions
    
    if percentage >= 0.6:
        return 2  # Close to passing, minimal extra help
    elif percentage >= 0.4:
        return 3  # Moderate performance
    else:
        return 4  # Poor performance, maximum extra help

def check_level_up(user_xp):
    """Check and update user level based on XP"""
    new_level = (user_xp.total_xp // 100) + 1
    
    if new_level > user_xp.current_level:
        user_xp.current_level = new_level
        user_xp.level_progress = user_xp.total_xp % 100
        user_xp.save()
        
        # Award level up bonus
        XPReward.objects.create(
            user_xp=user_xp,
            reward_type='streak',  # Using streak type for level bonus
            xp_amount=50,  # Level up bonus
            reason=f"Reached Level {new_level}"
        )