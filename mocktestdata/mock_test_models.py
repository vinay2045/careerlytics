"""
Django Models for Mock Test System
Database models for storing test results and logs
"""

from django.db import models
from django.utils import timezone
import json


class MockTestResult(models.Model):
    """Model for storing mock test results"""
    
    TEST_TYPES = [
        ('resume_analysis', 'Resume Analysis'),
        ('ai_model', 'AI Model'),
        ('database', 'Database'),
        ('api', 'API'),
        ('performance', 'Performance'),
        ('security', 'Security'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    id = models.AutoField(primary_key=True)
    test_type = models.CharField(
        max_length=50,
        choices=TEST_TYPES,
        default='resume_analysis'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    message = models.TextField(
        blank=True,
        null=True
    )
    details = models.JSONField(
        default=list,
        blank=True
    )
    execution_time = models.FloatField(
        help_text="Execution time in seconds",
        null=True,
        blank=True
    )
    metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metrics and test data"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'mock_test_results'
        ordering = ['-created_at']
        verbose_name = 'Mock Test Result'
        verbose_name_plural = 'Mock Test Results'
        indexes = [
            models.Index(fields=['test_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_test_type_display()} - {self.get_status_display()}"
    
    def get_details_list(self):
        """Return details as list"""
        if isinstance(self.details, str):
            try:
                return json.loads(self.details)
            except json.JSONDecodeError:
                return []
        return self.details or []
    
    def is_successful(self):
        """Check if test was successful"""
        return self.status == 'success'
    
    def is_failed(self):
        """Check if test failed"""
        return self.status == 'error'
    
    def is_running(self):
        """Check if test is currently running"""
        return self.status == 'running'


class MockTestLog(models.Model):
    """Model for storing mock test logs"""
    
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.AutoField(primary_key=True)
    test_type = models.CharField(
        max_length=50,
        choices=MockTestResult.TEST_TYPES,
        default='resume_analysis'
    )
    log_level = models.CharField(
        max_length=20,
        choices=LOG_LEVELS,
        default='INFO'
    )
    message = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'mock_test_logs'
        ordering = ['-created_at']
        verbose_name = 'Mock Test Log'
        verbose_name_plural = 'Mock Test Logs'
        indexes = [
            models.Index(fields=['test_type']),
            models.Index(fields=['log_level']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.test_type} - {self.log_level}"


class MockTestConfiguration(models.Model):
    """Model for storing mock test configurations"""
    
    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(
        blank=True
    )
    configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text="Test configuration parameters"
    )
    is_active = models.BooleanField(
        default=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'mock_test_configurations'
        ordering = ['name']
        verbose_name = 'Mock Test Configuration'
        verbose_name_plural = 'Mock Test Configurations'
    
    def __str__(self):
        return self.name


class MockTestSchedule(models.Model):
    """Model for scheduling automated mock tests"""
    
    test_type = models.CharField(
        max_length=50,
        choices=MockTestResult.TEST_TYPES,
        default='resume_analysis'
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=[
            ('once', 'Once'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='once'
    )
    next_run = models.DateTimeField(
        help_text="Next scheduled run time"
    )
    is_active = models.BooleanField(
        default=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'mock_test_schedules'
        ordering = ['next_run']
        verbose_name = 'Mock Test Schedule'
        verbose_name_plural = 'Mock Test Schedules'
        indexes = [
            models.Index(fields=['test_type']),
            models.Index(fields=['next_run']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_test_type_display()} - {self.get_schedule_type_display()}"


class MockTestReport(models.Model):
    """Model for storing generated test reports"""
    
    name = models.CharField(
        max_length=200
    )
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('summary', 'Summary'),
            ('detailed', 'Detailed'),
            ('comparison', 'Comparison'),
        ],
        default='summary'
    )
    content = models.TextField()
    file_path = models.CharField(
        max_length=500,
        blank=True
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    generated_at = models.DateTimeField(
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'mock_test_reports'
        ordering = ['-generated_at']
        verbose_name = 'Mock Test Report'
        verbose_name_plural = 'Mock Test Reports'
        indexes = [
            models.Index(fields=['report_type']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return self.name
