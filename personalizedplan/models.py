from django.db import models
from django.db.models import Sum
from users.models import UserRegistration
import uuid

# UserRegistration = get_user_model() # Removed to use custom user model

class PersonalizedPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=20, choices=(('role', 'Role'), ('language', 'Language')))
    target_role_language = models.CharField(max_length=50)
    current_week = models.IntegerField(default=1)
    current_day = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'personalizedplan_personalized_plan'

    def __str__(self):
        return f"{self.user.userid} - {self.target_role_language} Plan"

    @property
    def total_tasks(self):
        return DailyTask.objects.filter(weekly_plan__personalized_plan=self).count()

    @property
    def tasks_completed(self):
        return DailyTask.objects.filter(weekly_plan__personalized_plan=self, status='completed').count()

    @property
    def completion_percentage(self):
        total = self.total_tasks
        if total == 0:
            return 0
        return (self.tasks_completed / total) * 100

    @property
    def total_xp_earned(self):
        return DailyTask.objects.filter(
            weekly_plan__personalized_plan=self, 
            status='completed'
        ).aggregate(Sum('xp_reward'))['xp_reward__sum'] or 0

    @property
    def target_xp(self):
        return DailyTask.objects.filter(
            weekly_plan__personalized_plan=self
        ).aggregate(Sum('xp_reward'))['xp_reward__sum'] or 0

    @property
    def xp_progress_percentage(self):
        target = self.target_xp
        if target == 0:
            return 0
        return (self.total_xp_earned / target) * 100

    @property
    def streak_multiplier(self):
        try:
            streak = self.user.userstreak
            # Base multiplier 1.0, adds 0.1 for every 3 days of streak, max 2.0
            multiplier = 1.0 + (int(streak.current_streak / 3) * 0.1)
            return min(round(multiplier, 1), 2.0)
        except:
            return 1.0

    @property
    def weeks(self):
        return WeeklyPlan.objects.filter(personalized_plan=self).order_by('week_number')


class WeeklyPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    personalized_plan = models.ForeignKey(PersonalizedPlan, on_delete=models.CASCADE)
    week_number = models.IntegerField()
    skill_focus = models.CharField(max_length=100)
    topics = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[
        ('locked', 'Locked'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='locked')
    extra_days_added = models.IntegerField(default=0)
    weak_topics_focus = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_weekly_plan'

    def __str__(self):
        return f"Week {self.week_number} - {self.skill_focus}"

class DailyTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    weekly_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    topic = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
        ('completed', 'Completed')
    ], default='locked')
    completed_at = models.DateTimeField(null=True, blank=True)
    xp_reward = models.IntegerField(default=15)

    class Meta:
        db_table = 'personalizedplan_daily_task'

    def __str__(self):
        return f"Day {self.day_number} - {self.topic}"

class PlanProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    personalized_plan = models.ForeignKey(PersonalizedPlan, on_delete=models.CASCADE)
    current_week = models.IntegerField()
    current_day = models.IntegerField()
    total_days_completed = models.IntegerField(default=0)
    weekly_tests_passed = models.IntegerField(default=0)
    weekly_tests_failed = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'personalizedplan_plan_progress'

    def __str__(self):
        return f"{self.user.userid} - Progress: Week {self.current_week}, Day {self.current_day}"

class AssessmentResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    personalized_plan = models.ForeignKey(PersonalizedPlan, on_delete=models.CASCADE)
    test_type = models.CharField(max_length=20, choices=[
        ('initial', 'Initial'),
        ('weekly', 'Weekly'),
        ('final', 'Final'),
        ('correction', 'Correction')
    ])
    score = models.IntegerField()
    total_questions = models.IntegerField()
    weak_areas = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_assessment_result'

    def __str__(self):
        return f"{self.user.userid} - {self.test_type} Test: {self.score}/{self.total_questions}"

class WeakTopicDiagnosis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment_result = models.ForeignKey(AssessmentResult, on_delete=models.CASCADE)
    weak_topics = models.JSONField(default=dict)
    severity_level = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_weak_topic_diagnosis'

    def __str__(self):
        return f"Weak Topics - {self.severity_level} Severity"

class CorrectionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    personalized_plan = models.ForeignKey(PersonalizedPlan, on_delete=models.CASCADE)
    duration_weeks = models.IntegerField(default=2)
    all_topics = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_correction_plan'

    def __str__(self):
        return f"Correction Plan - {self.duration_weeks} weeks"

class FinalRetest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correction_plan = models.ForeignKey(CorrectionPlan, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField(default=60)
    career_recommendation = models.CharField(max_length=50)
    readiness_level = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_final_retest'

    def __str__(self):
        return f"Final Retest: {self.score}/{self.total_questions}"

class UserXP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(UserRegistration, on_delete=models.CASCADE)
    total_xp = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    xp_to_next_level = models.IntegerField(default=100)
    level_progress = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'personalizedplan_user_xp'

    def __str__(self):
        return f"{self.user.userid} - Level {self.current_level} ({self.total_xp} XP)"

class XPReward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_xp = models.ForeignKey(UserXP, on_delete=models.CASCADE)
    reward_type = models.CharField(max_length=20, choices=[
        ('daily_task', 'Daily Task'),
        ('weekly_test', 'Weekly Test'),
        ('streak', 'Streak'),
        ('recovery', 'Recovery'),
        ('speed', 'Speed'),
        ('consistency', 'Consistency')
    ])
    xp_amount = models.IntegerField()
    reason = models.CharField(max_length=200)
    related_object_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_xp_reward'

    def __str__(self):
        return f"{self.reward_type}: +{self.xp_amount} XP"

class UserStreak(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(UserRegistration, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    total_days_active = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_user_streak'

    def __str__(self):
        return f"{self.user.userid} - Streak: {self.current_streak} days"

class DailyActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    date = models.DateField()
    week_number = models.IntegerField()
    day_number = models.IntegerField()
    is_active = models.BooleanField(default=False)
    tasks_completed = models.IntegerField(default=0)
    xp_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_daily_activity'
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.userid} - {self.date}: {'Active' if self.is_active else 'Inactive'}"

class ResumeImpact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    skill = models.CharField(max_length=100)
    before_score = models.IntegerField()
    after_score = models.IntegerField()
    improvement_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizedplan_resume_impact'

    def __str__(self):
        return f"{self.user.userid} - {self.role} {self.skill}: {self.improvement_percentage}%"

class AssessmentSession(models.Model):
    """Track assessment sessions for personalized plan integration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100, unique=True)
    plan_type = models.CharField(max_length=20, choices=(('role', 'Role'), ('language', 'Language')))
    target_role_language = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned')
    ], default='started')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'personalizedplan_assessment_session'

    def __str__(self):
        return f"{self.user.userid} - {self.target_role_language} Assessment"
