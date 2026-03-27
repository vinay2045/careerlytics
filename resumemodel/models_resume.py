from django.db import models
from django.contrib.auth.models import User
import os

# Import UserRegistration from the same app
from .models import UserRegistration

def resume_upload_path(instance, filename):
    """Generate upload path for resume files"""
    return f"resumes/{instance.user.userid}/{filename}"

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
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='analysis_logs')
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
