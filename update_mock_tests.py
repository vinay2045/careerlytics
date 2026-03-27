import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from resumeanalysis.models import MockTest

def update_mock_tests():
    print("Updating MockTest records...")
    # Update all MockTest records to have 30 questions and 30 minutes time limit
    updated_count = MockTest.objects.all().update(questions_count=30, time_limit=30)
    print(f"Successfully updated {updated_count} MockTest records.")

if __name__ == '__main__':
    update_mock_tests()
