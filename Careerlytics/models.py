from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_datetime

class PlacementCell(models.Model):
    """Model to store placement cell institution data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='placement_cell')
    placement_cell_id = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the placement cell")
    institution_name = models.CharField(max_length=200, help_text="Name of the institution")
    email = models.EmailField(help_text="Official email address")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")
    address = models.TextField(blank=True, null=True, help_text="Institution address")
    website = models.URLField(blank=True, null=True, help_text="Institution website")
    logo = models.ImageField(upload_to='placement_cell_logos/', blank=True, null=True, help_text="Institution logo")
    is_active = models.BooleanField(default=True, help_text="Whether the placement cell is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'placement_cells'
        verbose_name = 'Placement Cell'
        verbose_name_plural = 'Placement Cells'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.institution_name} ({self.placement_cell_id})"
    
    @property
    def total_students(self):
        """Get total number of students for this placement cell"""
        return self.students.count()
    
    @property
    def total_placements(self):
        """Get total number of placements for this placement cell"""
        return self.placements.count()
    
    @property
    def college_code(self):
        """Get college code for student filtering"""
        institution_mapping = {
            'SREE CHAITANYA COLLEGE OF ENGINEERING': 'SCCE',
            'SCCE': 'SCCE',
            'SREE CHAITANYA INSTITUTE OF TECHNOLOGICAL SCIENCES': 'SCIT',
            'SCIT': 'SCIT',
        }
        return institution_mapping.get(self.institution_name.upper(), None)

class PlacementCellStudent(models.Model):
    """Model to store student data under placement cells"""
    placement_cell = models.ForeignKey(PlacementCell, on_delete=models.CASCADE, related_name='students')
    student_id = models.CharField(max_length=50, help_text="Student ID")
    name = models.CharField(max_length=100, help_text="Student name")
    email = models.EmailField(help_text="Student email")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Student phone")
    department = models.CharField(max_length=100, help_text="Student department")
    year = models.IntegerField(help_text="Academic year")
    marks_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Student marks percentage", db_column='cgpa')
    backlog = models.IntegerField(default=0, help_text="Number of active backlogs")
    skills = models.TextField(blank=True, null=True, help_text="Student skills")
    resume = models.FileField(upload_to='student_resumes/', blank=True, null=True, help_text="Student resume file")
    is_active = models.BooleanField(default=True, help_text="Whether the student is active/linked")
    is_placed = models.BooleanField(default=False, help_text="Whether the student is placed")
    company_placed = models.CharField(max_length=200, blank=True, null=True, help_text="Company where student is placed")
    package_offered = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Package offered in LPA")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'placement_cell_students'
        verbose_name = 'Placement Cell Student'
        verbose_name_plural = 'Placement Cell Students'
        ordering = ['-created_at']
        unique_together = ['placement_cell', 'student_id']
    
    def __str__(self):
        return f"{self.name} - {self.placement_cell.institution_name}"

class Placement(models.Model):
    """Model to store placement records"""
    placement_cell = models.ForeignKey(PlacementCell, on_delete=models.CASCADE, related_name='placements')
    student = models.ForeignKey(PlacementCellStudent, on_delete=models.CASCADE, related_name='student_placements')
    company_name = models.CharField(max_length=200, help_text="Company name")
    job_role = models.CharField(max_length=200, help_text="Job role/position")
    package_offered = models.DecimalField(max_digits=10, decimal_places=2, help_text="Package offered in LPA")
    location = models.CharField(max_length=200, help_text="Job location")
    status = models.CharField(max_length=50, default='placed', help_text="Current status of placement")
    placement_date = models.DateField(help_text="Date of placement")
    offer_letter = models.FileField(upload_to='offer_letters/', blank=True, null=True, help_text="Offer letter file")
    is_verified = models.BooleanField(default=False, help_text="Whether the placement is verified")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'placements'
        verbose_name = 'Placement'
        verbose_name_plural = 'Placements'
        ordering = ['-placement_date']
    
    def __str__(self):
        return f"{self.student.name} - {self.company_name}"

class PlacementActivity(models.Model):
    """Model to track placement cell activities"""
    placement_cell = models.ForeignKey(PlacementCell, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('drive', 'Placement Drive'),
            ('readiness_test', 'Readiness Test'),
            ('workshop', 'Workshop'),
            ('seminar', 'Seminar'),
            ('training', 'Training'),
            ('other', 'Other'),
        ],
        help_text="Type of activity"
    )
    title = models.CharField(max_length=200, help_text="Activity title")
    description = models.TextField(help_text="Activity description")
    date = models.DateField(help_text="Activity date")
    time = models.TimeField(help_text="Activity time")
    location = models.CharField(max_length=200, help_text="Activity location")
    target_audience = models.CharField(max_length=200, help_text="Target audience")
    max_participants = models.IntegerField(help_text="Maximum participants allowed")
    current_participants = models.IntegerField(default=0, help_text="Current number of participants")
    is_active = models.BooleanField(default=True, help_text="Whether the activity is active")
    
    # Drive-specific fields
    company_name = models.CharField(max_length=200, blank=True, null=True, help_text="Company name (for drives)")
    job_role = models.CharField(max_length=200, blank=True, null=True, help_text="Job role/position (for drives)")
    package_range = models.CharField(max_length=100, blank=True, null=True, help_text="Package range (for drives)")
    drive_date = models.DateTimeField(blank=True, null=True, help_text="Drive date and time (for drives)")
    drive_end_date = models.DateTimeField(blank=True, null=True, help_text="Drive end date and time (for drives)")
    application_deadline = models.DateTimeField(blank=True, null=True, help_text="Application deadline (for drives)")
    contact_person = models.CharField(max_length=100, blank=True, null=True, help_text="Contact person (for drives)")
    contact_email = models.EmailField(blank=True, null=True, help_text="Contact email (for drives)")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone (for drives)")
    
    # Eligibility criteria
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, help_text="Minimum CGPA required")
    eligible_departments = models.TextField(blank=True, null=True, help_text="Comma-separated department names")
    eligible_years = models.TextField(blank=True, null=True, help_text="Comma-separated years (1,2,3,4)")
    additional_requirements = models.TextField(blank=True, null=True, help_text="Additional requirements")
    
    # Status management
    DRIVE_STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=DRIVE_STATUS_CHOICES, default='upcoming', blank=True, null=True, help_text="Drive status")
    
    # Test-specific fields
    exam_duration = models.IntegerField(blank=True, null=True, help_text="Exam duration in minutes")
    questions = models.JSONField(blank=True, null=True, help_text="Test questions in JSON format")
    
    # Application tracking
    max_applicants = models.IntegerField(default=100, blank=True, null=True, help_text="Maximum applicants allowed")
    current_applicants = models.IntegerField(default=0, help_text="Current number of applicants")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'placement_activities'
        verbose_name = 'Placement Activity'
        verbose_name_plural = 'Placement Activities'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.placement_cell.institution_name}"
    
    def save(self, *args, **kwargs):
        # Auto-update status based on date for drives
        if self.activity_type == 'drive':
            now = timezone.now()
            
            # Ensure drive_date is a datetime object and timezone-aware
            if isinstance(self.drive_date, str):
                self.drive_date = parse_datetime(self.drive_date)
            if self.drive_date and timezone.is_naive(self.drive_date):
                self.drive_date = timezone.make_aware(self.drive_date)

            # Ensure drive_end_date is a datetime object and timezone-aware
            if isinstance(self.drive_end_date, str):
                self.drive_end_date = parse_datetime(self.drive_end_date)
            if self.drive_end_date and timezone.is_naive(self.drive_end_date):
                self.drive_end_date = timezone.make_aware(self.drive_end_date)

            # Ensure application_deadline is a datetime object and timezone-aware
            if isinstance(self.application_deadline, str):
                self.application_deadline = parse_datetime(self.application_deadline)
            if self.application_deadline and timezone.is_naive(self.application_deadline):
                self.application_deadline = timezone.make_aware(self.application_deadline)
            
            # Check for Status based on Drive Dates
            if self.drive_date:
                drive_start = self.drive_date
                # If drive_date is a Date (not datetime), convert for comparison
                if not hasattr(drive_start, 'hour'):
                    drive_start = timezone.make_aware(timezone.datetime.combine(drive_start, timezone.datetime.min.time()))

                if self.drive_end_date:
                    drive_end = self.drive_end_date
                    if not hasattr(drive_end, 'hour'):
                        drive_end = timezone.make_aware(timezone.datetime.combine(drive_end, timezone.datetime.max.time()))
                    
                    if now < drive_start:
                        self.status = 'upcoming'
                    elif drive_start <= now <= drive_end:
                        self.status = 'ongoing'
                    else:
                        self.status = 'completed'
                else:
                    # Original logic if no end date
                    if now >= drive_start:
                        # If it's today or past, it's ongoing or completed
                        if drive_start.date() == now.date():
                            self.status = 'ongoing'
                        else:
                            self.status = 'completed'
                    else:
                        # Drive is in the future
                        self.status = 'upcoming'
            elif self.application_deadline:
                # Fallback to application deadline if no drive date
                if self.application_deadline > now:
                    self.status = 'upcoming'
                else:
                    self.status = 'ongoing'
        super().save(*args, **kwargs)

    @property
    def is_drive(self):
        return self.activity_type == 'drive'
    
    @property
    def is_readiness_test(self):
        return self.activity_type == 'readiness_test'
    
    @property
    def seats_available(self):
        """Get available seats for activity"""
        return self.max_participants - self.current_participants
    
    @property
    def drive_seats_available(self):
        """Get available seats for drive applications"""
        if self.max_applicants:
            return self.max_applicants - self.current_applicants
        return None

class DriveApplication(models.Model):
    """Model to track student applications for placement drives"""
    drive = models.ForeignKey(PlacementActivity, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey('users.UserRegistration', on_delete=models.CASCADE, related_name='drive_applications')
    application_date = models.DateTimeField(auto_now_add=True)
    
    APPLICATION_STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('round_1', 'Round 1'),
        ('round_2', 'Round 2'),
        ('round_3', 'Round 3'),
        ('hr_round', 'HR Round'),
        ('placed', 'Placed'),
    ]
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='applied')
    resume_uploaded = models.BooleanField(default=False)
    notes = models.TextField(blank=True, help_text="Admin notes about the application")
    
    # Student info for admin tracking
    student_classification = models.CharField(
        max_length=20,
        choices=[
            ('placement_ready', 'Placement Ready'),
            ('needs_improvement', 'Needs Improvement'),
            ('at_risk', 'At Risk'),
        ],
        blank=True
    )
    student_cgpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    student_department = models.CharField(max_length=100, blank=True, null=True)
    student_year = models.IntegerField(blank=True, null=True)
    
    # Additional application form fields
    full_name = models.CharField(max_length=200, help_text="Applicant's full name", blank=True, null=True)
    hall_ticket_number = models.CharField(max_length=50, help_text="Hall ticket number", blank=True, null=True)
    gmail = models.EmailField(help_text="Gmail address", blank=True, null=True)
    branch = models.CharField(max_length=100, help_text="Branch/Department", blank=True, null=True)
    percentage_cgpa = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage/CGPA", blank=True, null=True)
    phone_number = models.CharField(max_length=20, help_text="Phone number", blank=True, null=True)
    
    class Meta:
        db_table = 'drive_applications'
        verbose_name = 'Drive Application'
        verbose_name_plural = 'Drive Applications'
        unique_together = ['drive', 'student']
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.student.userid} - {self.drive.title}"

class ReadinessTest(models.Model):
    """Model to store readiness test configuration and status"""
    TEST_STATUS_CHOICES = [
        ('disabled', 'Disabled'),
        ('enabled', 'Enabled'),
    ]
    
    status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='disabled', help_text="Test status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'readiness_tests'
        verbose_name = 'Readiness Test'
        verbose_name_plural = 'Readiness Tests'
    
    def __str__(self):
        return f"Readiness Test - {self.get_status_display()}"

class ReadinessTestResult(models.Model):
    """Model to store student readiness test results"""
    student = models.ForeignKey('users.UserRegistration', on_delete=models.CASCADE, related_name='readiness_results')
    test = models.ForeignKey(ReadinessTest, on_delete=models.CASCADE, related_name='results')
    
    # Test timing
    started_at = models.DateTimeField(help_text="When student started the test")
    completed_at = models.DateTimeField(help_text="When student completed the test")
    time_taken = models.IntegerField(help_text="Time taken in minutes")
    
    # Scores by category
    aptitude_score = models.IntegerField(default=0, help_text="Aptitude questions correct")
    reasoning_score = models.IntegerField(default=0, help_text="Reasoning questions correct")
    english_score = models.IntegerField(default=0, help_text="English questions correct")
    core_score = models.IntegerField(default=0, help_text="Core subject questions correct")
    
    # Overall results
    total_questions = models.IntegerField(default=60, help_text="Total questions in test")
    total_correct = models.IntegerField(default=0, help_text="Total correct answers")
    percentage = models.FloatField(default=0.0, help_text="Overall percentage")
    
    # Classification
    CLASSIFICATION_CHOICES = [
        ('placement_ready', 'Placement Ready'),
        ('needs_improvement', 'Needs Improvement'),
        ('at_risk', 'At Risk'),
    ]
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, help_text="Student classification based on performance")
    
    # Detailed answers (JSON)
    answers = models.JSONField(default=dict, blank=True, help_text="Student answers in JSON format")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'readiness_test_results'
        verbose_name = 'Readiness Test Result'
        verbose_name_plural = 'Readiness Test Results'
        unique_together = ['student', 'test']
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.student.userid} - {self.percentage}% ({self.get_classification_display()})"
    
    def save(self, *args, **kwargs):
        # Calculate total correct and percentage
        self.total_correct = self.aptitude_score + self.reasoning_score + self.english_score + self.core_score
        if self.total_questions > 0:
            self.percentage = (self.total_correct / self.total_questions) * 100
        
        # Auto-classify based on percentage if not already set
        if not self.classification:
            if self.percentage >= 70:
                self.classification = 'placement_ready'
            elif self.percentage >= 40:
                self.classification = 'needs_improvement'
            else:
                self.classification = 'at_risk'
        
        super().save(*args, **kwargs)
