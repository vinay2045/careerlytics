
import os
import django
import sys

sys.path.append('d:\\Careerlytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from users.models import Resume, ResumeRating

print("--- Debugging Resume Ratings ---")
try:
    resumes = Resume.objects.all()
    for r in resumes:
        print(f"Resume ID: {r.id}, User: {r.user.userid}, Processed: {r.processed}")
        try:
            rating = r.rating
            print(f"  Rating found: Score {rating.overall_score}")
        except Exception as e:
            print(f"  Rating NOT found: {e}")

except Exception as e:
    print(f"Error: {e}")
