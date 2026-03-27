from django import forms
from Careerlytics.models import DriveApplication


BRANCH_CHOICES = [
    ('', 'Select Branch'),
    ('B.Tech CSE', 'B.Tech CSE'),
    ('B.Tech ECE', 'B.Tech ECE'),
    ('B.Tech EEE', 'B.Tech EEE'),
    ('B.Tech MECH', 'B.Tech MECH'),
    ('B.Tech CIVIL', 'B.Tech CIVIL'),
    ('B.Tech IT', 'B.Tech IT'),
    ('BCA', 'BCA'),
    ('MCA', 'MCA'),
    ('M.Sc Computer Science', 'M.Sc Computer Science'),
    ('Other', 'Other'),
]


class DriveApplicationForm(forms.ModelForm):
    class Meta:
        model = DriveApplication
        fields = [
            'full_name',
            'hall_ticket_number', 
            'gmail',
            'branch',
            'percentage_cgpa',
            'phone_number'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your full name'
            }),
            'hall_ticket_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter hall ticket number'
            }),
            'gmail': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your Gmail address'
            }),
            'branch': forms.Select(choices=BRANCH_CHOICES, attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            }),
            'percentage_cgpa': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter percentage/CGPA',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter phone number'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.label_attrs = {'class': 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2'}