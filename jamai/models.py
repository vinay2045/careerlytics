from django.db import models
from users.models import UserRegistration
from django.utils import timezone

class VoiceRecording(models.Model):
    """Model to store voice recordings"""
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, related_name='voice_recordings')
    title = models.CharField(max_length=200, default="Voice Recording")
    audio_file = models.FileField(upload_to='voice_recordings/')
    duration = models.DurationField(help_text="Duration of the recording")
    file_size = models.IntegerField(help_text="File size in bytes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AI Analysis Fields
    jam_score = models.FloatField(null=True, blank=True)
    performance_level = models.CharField(max_length=50, null=True, blank=True)
    voice_score = models.FloatField(null=True, blank=True)
    fluency_score = models.FloatField(null=True, blank=True)
    content_score = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    soft_skills_score = models.FloatField(null=True, blank=True)
    question_asked = models.TextField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Voice Recording"
        verbose_name_plural = "Voice Recordings"
    
    def __str__(self):
        return f"{self.title} - {self.user.userid}"
    
    @property
    def file_size_kb(self):
        """Return file size in KB"""
        return f"{self.file_size / 1024:.2f} KB"
    
    @property
    def duration_formatted(self):
        """Return formatted duration (MM:SS)"""
        total_seconds = int(self.duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
