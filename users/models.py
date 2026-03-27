from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import os

def resume_upload_path(instance, filename):
    """Generate upload path for resume files"""
    return f"resumes/{instance.user.userid}/{filename}"

def shard_upload_path(instance, filename):
    return f'documents/{instance.document.id}/shard_{instance.index}.bin'

class UserRegistration(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('non_student', 'Non Student'),
    ]
    
    COLLEGE_CHOICES = [
        ('SCCE', 'SCCE - SREE CHAITANYA COLLEGE OF ENGINEERING'),
        ('SCIT', 'SCIT - SREE CHAITANYA INSTITUTE OF TECHNOLOGICAL SCIENCES'),
    ]
    
    # Basic fields for all users
    userid = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    pic = models.FileField(upload_to='profile_pics/', blank=True, null=True)
    status = models.CharField(max_length=100, default='Activated')
    
    # User type selection
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    
    # Student-specific fields (optional for non-students)
    student_id = models.CharField(max_length=50, blank=True, null=True, help_text="Student ID (for students only)")
    college_name = models.CharField(max_length=10, choices=COLLEGE_CHOICES, blank=True, null=True, help_text="College (for students only)")
    year = models.CharField(max_length=20, blank=True, null=True, help_text="Academic Year (for students only)")
    branch = models.CharField(max_length=100, blank=True, null=True, help_text="Branch/Specialization (for students only)")
    academic_marks = models.FloatField(blank=True, null=True, help_text="Academic marks percentage (for students only)")
    backlog = models.IntegerField(default=0, help_text="Number of active backlogs (for students only)")

    def __str__(self):
        return f"{self.userid} ({self.get_user_type_display()})"

class Student(models.Model):
    COLLEGE_CHOICES = [
        ('SCCE', 'SCCE - SREE CHAITANYA COLLEGE OF ENGINEERING'),
        ('SCIT', 'SCIT - SREE CHAITANYA INSTITUTE OF TECHNOLOGICAL SCIENCES'),
    ]
    
    # Basic fields
    userid = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    pic = models.FileField(upload_to='profile_pics/', blank=True, null=True)
    status = models.CharField(max_length=100, default='Activated')
    
    # Student-specific fields
    student_id = models.CharField(max_length=50, help_text="Student ID")
    college_name = models.CharField(max_length=10, choices=COLLEGE_CHOICES, help_text="College")
    year = models.CharField(max_length=20, help_text="Academic Year")
    branch = models.CharField(max_length=100, help_text="Branch/Specialization")
    academic_marks = models.FloatField(help_text="Academic marks percentage")
    backlog = models.IntegerField(default=0, help_text="Number of active backlogs")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.userid} - {self.student_id} ({self.get_college_name_display()})"

class NonStudent(models.Model):
    # Basic fields
    userid = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    pic = models.FileField(upload_to='profile_pics/', blank=True, null=True)
    status = models.CharField(max_length=100, default='Activated')
    
    # Non-student specific fields
    profession = models.CharField(max_length=100, blank=True, null=True, help_text="Profession/Job Title")
    company = models.CharField(max_length=200, blank=True, null=True, help_text="Company/Organization")
    experience_years = models.FloatField(blank=True, null=True, help_text="Years of experience")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.userid} - {self.profession or 'Non-Student'}"

class Resume(models.Model):
    """Model to store uploaded resumes"""
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to=resume_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=10, help_text="File extension (pdf, docx, etc.)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.userid} - {self.original_filename}"

class ResumeRating(models.Model):
    """Model to store AI resume ratings and analysis"""
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='rating')
    
    # Overall rating (0-100)
    overall_score = models.FloatField(default=0.0, help_text="Overall resume score (0-100)")
    
    # Category scores (0-100)
    skills_score = models.FloatField(default=0.0, help_text="Skills relevance score")
    experience_score = models.FloatField(default=0.0, help_text="Experience quality score")
    education_score = models.FloatField(default=0.0, help_text="Education relevance score")
    format_score = models.FloatField(default=0.0, help_text="Resume format score")
    keywords_score = models.FloatField(default=0.0, help_text="Keywords relevance score")
    
    # Detailed analysis
    skills_analysis = models.TextField(blank=True, help_text="AI analysis of skills")
    experience_analysis = models.TextField(blank=True, help_text="AI analysis of experience")
    education_analysis = models.TextField(blank=True, help_text="AI analysis of education")
    format_analysis = models.TextField(blank=True, help_text="AI analysis of format")
    keywords_analysis = models.TextField(blank=True, help_text="AI analysis of keywords")
    
    # Recommendations
    strengths = models.TextField(blank=True, help_text="Identified strengths")
    improvements = models.TextField(blank=True, help_text="Suggested improvements")
    recommendations = models.TextField(blank=True, help_text="Specific recommendations")
    
    # Technical details
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    confidence_score = models.FloatField(default=0.0, help_text="AI confidence in rating (0-1)")
    
    # Additional analysis data
    extracted_text = models.TextField(blank=True, help_text="Extracted text from resume")
    word_count = models.IntegerField(default=0, help_text="Total word count in resume")
    character_count = models.IntegerField(default=0, help_text="Total character count in resume")
    
    # Analysis details
    skills_found = models.JSONField(default=dict, blank=True, help_text="Skills identified in resume")
    experience_years = models.FloatField(default=0.0, help_text="Years of experience detected")
    education_level = models.CharField(max_length=50, blank=True, help_text="Highest education level detected")
    contact_methods = models.IntegerField(default=0, help_text="Number of contact methods found")
    bullet_points = models.IntegerField(default=0, help_text="Number of bullet points found")
    
    # Analysis metadata
    analysis_version = models.CharField(max_length=20, default='1.0', help_text="Version of analysis algorithm")
    analysis_date = models.DateTimeField(auto_now_add=True, null=True, help_text="When analysis was performed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating for {self.resume.user.userid} - Score: {self.overall_score}"

class ResumeKeyword(models.Model):
    """Model to store predefined keywords for analysis"""
    category = models.CharField(max_length=50, help_text="Category (e.g., 'Programming', 'Soft Skills')")
    keyword = models.CharField(max_length=100, help_text="Keyword or phrase")
    weight = models.FloatField(default=1.0, help_text="Weight for scoring (0.1-5.0)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'keyword']
        unique_together = ['category', 'keyword']
    
    def __str__(self):
        return f"{self.category}: {self.keyword} (weight: {self.weight})"

class ResumeAnalysisLog(models.Model):
    """Model to log resume analysis attempts and results"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='analysis_logs', null=True, blank=True)
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    
    # Analysis details
    analysis_type = models.CharField(max_length=20, default='AI', help_text="Type of analysis performed")
    status = models.CharField(max_length=20, default='PENDING', help_text="Analysis status")
    
    # Results
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analysis log for {self.resume.user.userid} - {self.status}"

class AdminRegistration(models.Model):
    INSTITUTION_CHOICES = [
        ('SCCE', 'SCCE - SREE CHAITANYA COLLEGE OF ENGINEERING'),
        ('SCIT', 'SCIT - SREE CHAITANYA INSTITUTE OF TECHNOLOGICAL SCIENCES'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True, default='')
    institution_name = models.CharField(max_length=10, choices=INSTITUTION_CHOICES, default='SCCE')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=100, default='Activated')  # Activated / Not Activated

    def __str__(self):
        return f"{self.username} ({self.get_institution_name_display()})"

class Document(models.Model):
    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(default=timezone.now)
    merkle_root = models.CharField(max_length=128, blank=True, null=True)
    merkle_hmac = models.CharField(max_length=128, blank=True, null=True)
    master_salt = models.BinaryField(blank=True, null=True)
    file_data = models.BinaryField(null=True, blank=True)
    filesize = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.original_filename})"

class Shard(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shards')
    index = models.PositiveSmallIntegerField()  
    encrypted_data = models.FileField(upload_to=shard_upload_path)
    nonce = models.BinaryField()
    tag = models.BinaryField(blank=True, null=True)
    hash_hex = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField(default=timezone.now)

class ShardKey(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shardkeys')
    shard_index = models.PositiveSmallIntegerField()  
    key_hash = models.CharField(max_length=128)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

class DocumentPerformance(models.Model):
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='performance')
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    # Duration metrics in seconds (float)
    key_generation_time = models.FloatField(default=0.0)
    encryption_time = models.FloatField(default=0.0)
    decryption_time = models.FloatField(default=0.0)
    response_time = models.FloatField(default=0.0)
    computational_overhead = models.FloatField(default=0.0)
    total_change_rate = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"Performance Metrics for {self.document.title} ({self.uploaded_at})"

class AdminRegistration(models.Model):
    INSTITUTION_CHOICES = [
        ('SCCE', 'SCCE - SREE CHAITANYA COLLEGE OF ENGINEERING'),
        ('SCIT', 'SCIT - SREE CHAITANYA INSTITUTE OF TECHNOLOGICAL SCIENCES'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True, default='')
    institution_name = models.CharField(max_length=10, choices=INSTITUTION_CHOICES, default='SCCE')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=100, default='Activated')  # Activated / Not Activated

    def __str__(self):
        return f"{self.username} ({self.get_institution_name_display()})"
