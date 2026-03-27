from django.contrib import admin
from .models import (
    PersonalizedPlan, WeeklyPlan, DailyTask, PlanProgress,
    AssessmentResult, WeakTopicDiagnosis, CorrectionPlan, FinalRetest,
    UserXP, XPReward, UserStreak, DailyActivity, ResumeImpact
)

@admin.register(PersonalizedPlan)
class PersonalizedPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_role_language', 'plan_type', 'status', 'current_week', 'current_day', 'created_at']
    list_filter = ['plan_type', 'status', 'created_at']
    search_fields = ['user__username', 'target_role_language']

@admin.register(WeeklyPlan)
class WeeklyPlanAdmin(admin.ModelAdmin):
    list_display = ['personalized_plan', 'week_number', 'skill_focus', 'status', 'extra_days_added', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['skill_focus', 'personalized_plan__user__username']

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ['weekly_plan', 'day_number', 'topic', 'status', 'xp_reward', 'completed_at']
    list_filter = ['status', 'completed_at']
    search_fields = ['topic', 'weekly_plan__skill_focus']

@admin.register(PlanProgress)
class PlanProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'personalized_plan', 'current_week', 'current_day', 'total_days_completed', 'last_activity']
    list_filter = ['last_activity']
    search_fields = ['user__username']

@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'personalized_plan', 'test_type', 'score', 'total_questions', 'created_at']
    list_filter = ['test_type', 'created_at']
    search_fields = ['user__username']

@admin.register(WeakTopicDiagnosis)
class WeakTopicDiagnosisAdmin(admin.ModelAdmin):
    list_display = ['assessment_result', 'severity_level', 'created_at']
    list_filter = ['severity_level', 'created_at']

@admin.register(CorrectionPlan)
class CorrectionPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'personalized_plan', 'duration_weeks', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username']

@admin.register(FinalRetest)
class FinalRetestAdmin(admin.ModelAdmin):
    list_display = ['correction_plan', 'score', 'total_questions', 'career_recommendation', 'readiness_level', 'created_at']
    list_filter = ['career_recommendation', 'readiness_level', 'created_at']

@admin.register(UserXP)
class UserXPAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_xp', 'current_level', 'level_progress', 'last_updated']
    list_filter = ['current_level', 'last_updated']
    search_fields = ['user__username']

@admin.register(XPReward)
class XPRewardAdmin(admin.ModelAdmin):
    list_display = ['user_xp', 'reward_type', 'xp_amount', 'reason', 'created_at']
    list_filter = ['reward_type', 'created_at']
    search_fields = ['reason', 'user_xp__user__username']

@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'longest_streak', 'total_days_active', 'last_activity_date']
    list_filter = ['last_activity_date']
    search_fields = ['user__username']

@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'week_number', 'day_number', 'is_active', 'tasks_completed', 'xp_earned']
    list_filter = ['is_active', 'date']
    search_fields = ['user__username']

@admin.register(ResumeImpact)
class ResumeImpactAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'skill', 'before_score', 'after_score', 'improvement_percentage', 'created_at']
    list_filter = ['role', 'skill', 'created_at']
    search_fields = ['user__username', 'role', 'skill']
