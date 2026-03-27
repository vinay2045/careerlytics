from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import json
import uuid

# Import UserRegistration from users app
from users.models import UserRegistration

def resume_upload_path(instance, filename):
    """Generate upload path for resume files"""
    return f"resumeanalysis/resumes/{instance.user.userid}/{uuid.uuid4()}_{filename}"

class ResumeAnalysis(models.Model):
    """Store AI analysis results for uploaded resumes"""
    
    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='resume_analyses')
    resume_file = models.FileField(upload_to=resume_upload_path)
    original_filename = models.CharField(max_length=255)
    
    # AI Analysis Results
    ats_score = models.IntegerField(help_text="ATS compatibility score (0-100)")
    skills_extracted = models.JSONField(default=list, help_text="List of extracted skills")
    experience_years = models.FloatField(null=True, blank=True, help_text="Total years of experience")
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default='beginner')
    
    # Detailed Scores
    skills_match_score = models.IntegerField(default=0, help_text="Skills match score (0-100)")
    experience_score = models.IntegerField(default=0, help_text="Experience relevance score (0-100)")
    education_score = models.IntegerField(default=0, help_text="Education background score (0-100)")
    format_score = models.IntegerField(default=0, help_text="Format and keywords score (0-100)")
    
    # Analysis Metadata
    analysis_version = models.CharField(max_length=20, default='1.0')
    processing_time = models.FloatField(help_text="Processing time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.userid} - Resume Analysis ({self.ats_score}%)"

class Role(models.Model):
    """Role definitions for mock tests"""
    key = models.CharField(max_length=50, unique=True, help_text="Unique key for the role (e.g., 'frontend')")
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Material Symbol icon name")
    color = models.CharField(max_length=50, help_text="Color theme (e.g., 'blue', 'green')")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    """Language definitions for mock tests"""
    key = models.CharField(max_length=50, unique=True, help_text="Unique key for the language (e.g., 'python')")
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Material Symbol icon name")
    color = models.CharField(max_length=50, help_text="Color theme (e.g., 'blue', 'green')")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class MockTest(models.Model):
    """Specific mock tests available for a role or language"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='tests', null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='tests', null=True, blank=True)
    name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=200, help_text="Question file name")
    questions_count = models.IntegerField(default=20)
    time_limit = models.IntegerField(help_text="Time in minutes")
    difficulty = models.CharField(max_length=20, choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.role:
            return f"{self.role.name} - {self.name}"
        elif self.language:
            return f"{self.language.name} - {self.name}"
        return self.name

class RoleQuiz(models.Model):
    """Quiz sessions for role-based assessments"""
    
    ROLE_CHOICES = [
        ('frontend', 'Frontend Developer'),
        ('backend', 'Backend Developer'),
        ('devops', 'DevOps Engineer'),
        ('datascience', 'Data Scientist'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='role_quizzes')
    resume_analysis = models.ForeignKey(ResumeAnalysis, on_delete=models.CASCADE, null=True, blank=True)
    
    # Quiz Configuration
    target_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    total_questions = models.IntegerField(default=30)
    time_limit = models.IntegerField(default=1800, help_text="Time limit in seconds (30 minutes)")
    
    # Quiz Results
    general_ability_score = models.IntegerField(default=0, help_text="General ability score (0-100)")
    tech_fundamentals_score = models.IntegerField(default=0, help_text="Tech fundamentals score (0-100)")
    role_specific_score = models.IntegerField(default=0, help_text="Role-specific score (0-100)")
    total_score = models.IntegerField(default=0, help_text="Total quiz score (0-100)")
    
    # Quiz Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.IntegerField(null=True, blank=True, help_text="Time taken in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.userid} - {self.get_target_role_display()} Quiz"

class QuizQuestion(models.Model):
    """Individual quiz questions"""
    
    CATEGORY_CHOICES = [
        ('general', 'General Ability'),
        ('tech_fundamentals', 'Tech Fundamentals'),
        ('frontend', 'Frontend Specific'),
        ('backend', 'Backend Specific'),
        ('devops', 'DevOps Specific'),
        ('datascience', 'Data Science Specific'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Question Content
    question_text = models.TextField()
    options = models.JSONField(help_text="List of 4 options")
    correct_answer = models.IntegerField(help_text="Index of correct option (0-3)")
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    
    # Metadata
    tags = models.JSONField(default=list, help_text="Tags for question categorization")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'difficulty']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.question_text[:50]}..."

class QuizResponse(models.Model):
    """User responses to quiz questions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(RoleQuiz, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, null=True, blank=True)
    session_question_id = models.CharField(max_length=50, null=True, blank=True, help_text="Question ID for session-based questions")
    
    # Response Data
    user_answer = models.IntegerField(help_text="Index of selected option (0-3)")
    is_correct = models.BooleanField()
    time_taken = models.IntegerField(help_text="Time taken for this question in seconds")
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['answered_at']
    
    def __str__(self):
        if self.question:
            return f"{self.quiz.user.userid} - Q{self.question.id} - {self.is_correct}"
        else:
            return f"{self.quiz.user.userid} - {self.session_question_id} - {self.is_correct}"

# Test Models (temporarily commented out for basic flow)
# class TestAttempt(models.Model):
#     """Track test attempts and results"""
#     
#     TEST_STATUS_CHOICES = [
#         ('in_progress', 'In Progress'),
#         ('completed', 'Completed'),
#         ('abandoned', 'Abandoned'),
#         ('expired', 'Expired'),
#     ]
#     
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='test_attempts')
#     role_id = models.IntegerField(null=True, blank=True, help_text="Target role ID if specified")
#     
#     # Test Configuration
#     total_questions = models.IntegerField(help_text="Total number of questions")
#     time_limit = models.IntegerField(help_text="Time limit in minutes")
#     time_taken = models.IntegerField(default=0, help_text="Actual time taken in seconds")
#     
#     # Test Status
#     status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='in_progress')
#     started_at = models.DateTimeField(auto_now_add=True)
#     completed_at = models.DateTimeField(null=True, blank=True)
#     
#     # Scores (General 30%, Tech 30%, Role 40%)
#     general_score = models.IntegerField(default=0, help_text="General aptitude score (0-100)")
#     tech_score = models.IntegerField(default=0, help_text="Technical knowledge score (0-100)")
#     role_score = models.IntegerField(default=0, help_text="Role-specific score (0-100)")
#     total_score = models.IntegerField(default=0, help_text="Weighted total score (0-100)")
#     
#     # Additional Metrics
#     questions_answered = models.IntegerField(default=0, help_text="Number of questions answered")
#     questions_correct = models.IntegerField(default=0, help_text="Number of correct answers")
#     questions_marked_review = models.IntegerField(default=0, help_text="Questions marked for review")
#     
#     class Meta:
#         ordering = ['-started_at']
#     
#     def __str__(self):
#         return f"{self.user.userid} - Test {self.id} ({self.status})"
#     
#     @property
#     def accuracy_percentage(self):
#         """Calculate accuracy percentage"""
#         if self.questions_answered == 0:
#             return 0
#         return round((self.questions_correct / self.questions_answered) * 100, 1)
#     
#     @property
#     def completion_percentage(self):
#         """Calculate completion percentage"""
#         if self.total_questions == 0:
#             return 0
#         return round((self.questions_answered / self.total_questions) * 100, 1)

# class TestAnswer(models.Model):
#     """Store individual test answers"""
#     
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     test_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
#     
#     # Question Data
#     question_id = models.CharField(max_length=50, help_text="Question identifier")
#     question_category = models.CharField(max_length=20, help_text="Question category (general/tech/role)")
#     question_text = models.TextField(help_text="Full question text")
#     question_options = models.JSONField(help_text="List of question options")
#     correct_answer = models.IntegerField(help_text="Index of correct answer")
#     
#     # User Response
#     selected_answer = models.IntegerField(help_text="Index of selected answer")
#     is_correct = models.BooleanField(help_text="Whether the answer is correct")
#     is_marked_for_review = models.BooleanField(default=False, help_text="Marked for review by user")
#     time_spent = models.IntegerField(default=0, help_text="Time spent on this question in seconds")
#     
#     # Metadata
#     answered_at = models.DateTimeField(auto_now_add=True)
#     
#     class Meta:
#         ordering = ['answered_at']
#         unique_together = ['test_attempt', 'question_id']
#     
#     def __str__(self):
#         return f"{self.test_attempt.user.userid} - {self.question_id} ({'Correct' if self.is_correct else 'Incorrect'})"

class RoleEligibility(models.Model):
    """Store role eligibility scores and recommendations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='role_eligibilities')
    
    # Optional relationships - can be from quiz or test
    quiz = models.ForeignKey(RoleQuiz, on_delete=models.CASCADE, null=True, blank=True)
    # test_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, null=True, blank=True)
    resume_analysis = models.ForeignKey(ResumeAnalysis, on_delete=models.CASCADE, null=True, blank=True)
    
    # Eligibility Data
    role_name = models.CharField(max_length=50, default="General", help_text="Target role name")
    eligibility_score = models.FloatField(default=0.0, help_text="Overall eligibility score (0-100)")
    is_eligible = models.BooleanField(help_text="Eligible for role")
    
    # Score Breakdown
    general_score = models.FloatField(default=0, help_text="General aptitude score")
    tech_score = models.FloatField(default=0, help_text="Technical knowledge score")
    role_score = models.FloatField(default=0, help_text="Role-specific score")
    resume_score = models.FloatField(default=0, help_text="Resume analysis score")
    
    # Recommendations
    recommended_roles = models.JSONField(default=list, help_text="List of recommended roles")
    skill_gaps = models.JSONField(default=list, help_text="Areas needing improvement")
    improvement_suggestions = models.JSONField(default=list, help_text="Specific improvement suggestions")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-eligibility_score']
    
    def __str__(self):
        return f"{self.user.userid} - {self.role_name} ({self.eligibility_score}%)"

class RecommendedRole(models.Model):
    """Alternative role recommendations based on analysis"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='recommended_roles')
    eligibility = models.ForeignKey(RoleEligibility, on_delete=models.CASCADE)
    
    # Role Data
    role_name = models.CharField(max_length=50)
    match_percentage = models.FloatField(help_text="Match percentage for this role")
    match_reasons = models.JSONField(default=list, help_text="Reasons for this recommendation")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-match_percentage']
    
    def __str__(self):
        return f"{self.user.userid} - {self.role_name} ({self.match_percentage}%)"

# Test Models
class TestAttempt(models.Model):
    """Track test attempts and results"""
    
    TEST_STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='test_attempts')
    role_id = models.IntegerField(null=True, blank=True, help_text="Target role ID if specified")
    
    # Core Assessment Fields
    test_type = models.CharField(max_length=20, default='mock', help_text="Type of test: 'mock' or 'core'")
    category = models.CharField(max_length=50, null=True, blank=True, help_text="Test category (e.g., 'frontend', 'aptitude')")
    module_index = models.IntegerField(null=True, blank=True, help_text="Module index for core assessments (0-based)")
    
    # Test Configuration
    total_questions = models.IntegerField(help_text="Total number of questions")
    time_limit = models.IntegerField(help_text="Time limit in minutes")
    time_taken = models.IntegerField(default=0, help_text="Actual time taken in seconds")
    
    # Test Status
    status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Scores (General 30%, Tech 30%, Role 40%)
    general_score = models.IntegerField(default=0, help_text="General aptitude score (0-100)")
    tech_score = models.IntegerField(default=0, help_text="Technical knowledge score (0-100)")
    role_score = models.IntegerField(default=0, help_text="Role-specific score (0-100)")
    total_score = models.IntegerField(default=0, help_text="Weighted total score (0-100)")
    
    # Additional Metrics
    questions_answered = models.IntegerField(default=0, help_text="Number of questions answered")
    questions_correct = models.IntegerField(default=0, help_text="Number of correct answers")
    questions_marked_review = models.IntegerField(default=0, help_text="Questions marked for review")
    xp_earned = models.IntegerField(default=0, help_text="XP earned from this attempt")
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.userid} - Test {self.id} ({self.status})"
    
    @property
    def accuracy_percentage(self):
        """Calculate accuracy percentage"""
        if self.questions_answered == 0:
            return 0
        return round((self.questions_correct / self.questions_answered) * 100, 1)
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.total_questions == 0:
            return 0
        return round((self.questions_answered / self.total_questions) * 100, 1)

class TestAnswer(models.Model):
    """Store individual test answers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    
    # Question Data
    question_id = models.CharField(max_length=50, help_text="Question identifier")
    question_category = models.CharField(max_length=20, help_text="Question category (general/tech/role)")
    question_text = models.TextField(help_text="Full question text")
    question_options = models.JSONField(help_text="List of question options")
    correct_answer = models.IntegerField(help_text="Index of correct answer")
    
    # User Response
    selected_answer = models.IntegerField(help_text="Index of selected answer")
    is_correct = models.BooleanField(help_text="Whether the answer is correct")
    is_marked_for_review = models.BooleanField(default=False, help_text="Marked for review by user")
    time_spent = models.IntegerField(default=0, help_text="Time spent on this question in seconds")
    
    # Metadata
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['answered_at']
        unique_together = ['test_attempt', 'question_id']
    
    def __str__(self):
        return f"{self.test_attempt.user.userid} - {self.question_id} ({'Correct' if self.is_correct else 'Incorrect'})"

class MockTestXP(models.Model):
    """
    Track user XP and level progress for mock tests.
    Stored in 'mock_test_db' (D:\Careerlytics\mocktestdata\mocktest_xp.db).
    """
    user_id = models.CharField(max_length=100, unique=True)  # Stores UserRegistration.userid
    total_xp = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)
    tests_completed = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def calculate_level(self):
        """Calculate level based on total XP"""
        # Simple formula: Level = 1 + (Total XP / 1000)
        return 1 + (self.total_xp // 1000)

    def update_progress(self, xp_gained):
        """Update progress with new XP"""
        self.total_xp += xp_gained
        self.tests_completed += 1
        self.current_level = self.calculate_level()
        self.save()

    def __str__(self):
        return f"{self.user_id} - Level {self.current_level} ({self.total_xp} XP)"

