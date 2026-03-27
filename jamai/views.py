from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.files.base import ContentFile
from django.utils import timezone
import base64
import io
from datetime import timedelta
from .models import VoiceRecording
from .ai_model import SoftSkillsAIModel
import os
from django.conf import settings
from users.models import UserRegistration
from functools import wraps

# Initialize AI Model
QUESTIONS_PATH = os.path.join(settings.BASE_DIR, 'jamai', 'question', 'question.txt')
PARAMS_PATH = os.path.join(settings.BASE_DIR, 'jamai', 'question', 'para.txt')
ai_model = SoftSkillsAIModel(QUESTIONS_PATH, PARAMS_PATH)

def custom_login_required(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if 'userid' not in request.session:
            messages.error(request, "Please login first to access this page.")
            return redirect('unified_login')
        
        try:
            request.custom_user = UserRegistration.objects.get(userid=request.session['userid'])
        except UserRegistration.DoesNotExist:
            messages.error(request, "User session invalid. Please login again.")
            return redirect('unified_login')
            
        return f(request, *args, **kwargs)
    return wrap

@custom_login_required
def jamai_page(request):
    """Main jamai page"""
    recordings = VoiceRecording.objects.filter(user=request.custom_user).order_by('-created_at')
    random_question = ai_model.get_random_question()
    
    context = {
        'user': request.custom_user,
        'recordings': recordings,
        'total_recordings': recordings.count(),
        'question': random_question
    }
    return render(request, 'jamai.html', context)

@csrf_exempt
@require_http_methods(["POST"])
@custom_login_required
def save_recording(request):
    """Save voice recording to database"""
    try:
        # Get audio data from request (check both POST and FILES)
        audio_data = request.POST.get('audio_data')
        audio_file = request.FILES.get('audio_data')
        
        duration = request.POST.get('duration', '01:00')
        title = request.POST.get('title', 'JAM Session')
        question_asked = request.POST.get('question_asked') or request.POST.get('question', '')
        
        if not audio_data and not audio_file:
            return JsonResponse({'status': 'error', 'message': 'No audio data provided'}, status=400)
        
        # Parse duration
        try:
            minutes, seconds = map(int, duration.split(':'))
            total_seconds = minutes * 60 + seconds
            duration_timedelta = timedelta(minutes=minutes, seconds=seconds)
        except (ValueError, AttributeError):
            total_seconds = 60
            duration_timedelta = timedelta(minutes=1)
        
        # Get audio bytes and base64 string for AI analysis
        if audio_file:
            audio_bytes = audio_file.read()
            audio_data_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            # Add prefix if needed by AI model
            audio_data_for_ai = f"data:audio/wav;base64,{audio_data_base64}"
        else:
            # Handle base64 from POST
            audio_data_clean = audio_data.split(',')[1] if ',' in audio_data else audio_data
            audio_bytes = base64.b64decode(audio_data_clean)
            audio_data_for_ai = audio_data
        
        # Run AI Analysis
        analysis_results = ai_model.analyze_voice(audio_data_for_ai, total_seconds)
        
        # Create recording with AI scores
        recording = VoiceRecording(
            user=request.custom_user,
            title=title,
            duration=duration_timedelta,
            file_size=len(audio_bytes),
            question_asked=question_asked,
            jam_score=analysis_results['jam_score'],
            performance_level=analysis_results['performance_level'],
            voice_score=analysis_results['breakdown']['voice'],
            fluency_score=analysis_results['breakdown']['fluency'],
            content_score=analysis_results['breakdown']['content'],
            confidence_score=analysis_results['breakdown']['confidence'],
            soft_skills_score=analysis_results['breakdown']['soft_skills'],
            feedback=analysis_results.get('feedback', '')
        )
        
        # Save audio file
        filename = f"recording_{request.custom_user.userid}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.wav"
        recording.audio_file.save(filename, ContentFile(audio_bytes), save=True)
        
        return JsonResponse({
            'status': 'success',
            'recording_id': recording.id,
            'message': 'Recording saved and analyzed successfully!',
            'analysis': analysis_results,
            'recording': {
                'id': recording.id,
                'title': recording.title,
                'duration': recording.duration_formatted,
                'file_size': recording.file_size_kb,
                'created_at': recording.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'audio_url': recording.audio_file.url,
                'jam_score': recording.jam_score,
                'performance_level': recording.performance_level
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error saving recording: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
@custom_login_required
def delete_recording(request, recording_id):
    """Delete voice recording"""
    try:
        recording = VoiceRecording.objects.get(id=recording_id, user=request.custom_user)
        recording.audio_file.delete()  # Delete file from storage
        recording.delete()  # Delete record from database
        
        return JsonResponse({
            'status': 'success',
            'message': 'Recording deleted successfully!'
        })
        
    except VoiceRecording.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Recording not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@custom_login_required
def get_recordings(request):
    """Get all recordings for the user"""
    try:
        recordings = VoiceRecording.objects.filter(user=request.custom_user).order_by('-created_at')
        
        recordings_data = []
        for recording in recordings:
            recordings_data.append({
                'id': recording.id,
                'title': recording.title,
                'duration': recording.duration_formatted,
                'file_size': recording.file_size_kb,
                'created_at': recording.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'audio_url': recording.audio_file.url
            })
        
        return JsonResponse({
            'success': True,
            'recordings': recordings_data,
            'total_count': len(recordings_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
