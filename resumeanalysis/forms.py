from django import forms
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from .models import ResumeAnalysis, RoleQuiz

class ResumeUploadForm(forms.ModelForm):
    """Form for resume upload with role selection"""
    
    ROLE_CHOICES = [
        ('', 'Select a role...'),
        ('frontend', 'Frontend Developer'),
        ('backend', 'Backend Developer'),
        ('devops', 'DevOps Engineer'),
        ('datascience', 'Data Scientist'),
    ]
    
    target_role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'required': True
        }),
        label='Target Role'
    )
    
    resume_file = forms.FileField(
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc']),
        ],
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'accept': '.pdf,.docx,.doc',
            'required': True
        }),
        label='Resume File',
        help_text='Upload your resume (PDF, DOCX, or DOC format, max 5MB)'
    )
    
    agree_to_analysis = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
        }),
        label='I agree to AI analysis of my resume for role matching and skill assessment'
    )
    
    class Meta:
        model = ResumeAnalysis
        fields = ['resume_file']
    
    def clean_resume_file(self):
        file = self.cleaned_data.get('resume_file')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('File size must be less than 5MB.')
            
            # Check if file can be read (basic encoding test)
            try:
                # Try to read first few bytes to check if file is readable
                file.seek(0)
                chunk = file.read(1024)  # Read first 1KB
                file.seek(0)  # Reset file pointer
                
                # Try to decode with UTF-8
                try:
                    chunk.decode('utf-8')
                except UnicodeDecodeError:
                    # If UTF-8 fails, the file might have encoding issues
                    # But we'll handle this in the view, so just warn for now
                    pass
                    
            except Exception as e:
                raise forms.ValidationError(f'File appears to be corrupted or unreadable: {str(e)}')
                
        return file

class QuizStartForm(forms.ModelForm):
    """Form for starting a quiz session"""
    
    class Meta:
        model = RoleQuiz
        fields = []  # All fields are auto-populated
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any custom initialization if needed
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class QuizAnswerForm(forms.Form):
    """Form for submitting quiz answers"""
    
    question_id = forms.CharField(widget=forms.HiddenInput())
    selected_option = forms.IntegerField(
        widget=forms.RadioSelect(),
        validators=[
            MinValueValidator(0),
            MaxValueValidator(3)
        ]
    )
    time_taken = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, question_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selected_option'].widget = forms.RadioSelect(
            choices=[(i, option) for i, option in enumerate(question_data.get('options', []))],
            attrs={'class': 'space-y-2'}
        )
        self.fields['selected_option'].label = question_data.get('question_text', '')

class RoleSelectionForm(forms.Form):
    """Form for role selection when score is below 60%"""
    
    ACTION_CHOICES = [
        ('continue', 'Continue with selected role'),
        ('switch', 'Switch to general mock test'),
        ('results', 'View detailed results'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2'
        }),
        label='Choose your next step',
        initial='results'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['action'].widget.attrs.update({'class': 'space-y-2'})
