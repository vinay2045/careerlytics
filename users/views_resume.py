from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import math
import os
import time

from .models import UserRegistration, Resume, ResumeRating, ResumeAnalysisLog
from .resume_analyzer import resume_analyzer

def upload_resume_v1(request):
    """Legacy resume upload view - deprecated in favor of resumeanalysis.views.upload_resume"""
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please login to upload your resume.")
        return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            # Handle file upload
            uploaded_file = request.FILES.get('resume_file')
            if not uploaded_file:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Please select a resume file to upload.'})
                messages.error(request, "Please select a resume file to upload.")
                context = {'user': user}
                return render(request, 'resumeanalysis/upload_resume.html', context)
            
            # Validate file type
            allowed_extensions = ['.pdf', '.docx', '.doc']
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Only PDF and DOCX files are allowed.'})
                messages.error(request, "Only PDF and DOCX files are allowed.")
                context = {'user': user}
                return render(request, 'resumeanalysis/upload_resume.html', context)
            
            # Validate file size (max 5MB)
            if uploaded_file.size > 5 * 1024 * 1024:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'File size must be less than 5MB.'})
                messages.error(request, "File size must be less than 5MB.")
                context = {'user': user}
                return render(request, 'resumeanalysis/upload_resume.html', context)
            
            # Create resume record
            resume = Resume.objects.create(
                user=user,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=file_extension[1:]  # Remove the dot
            )
            
            # Save the resume first, then access the fields
            resume.save()
            
            # Create analysis log
            analysis_log = ResumeAnalysisLog.objects.create(
                resume=resume,
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                analysis_type='AI',
                status='PENDING',
                processing_time=None,
                error_message=None
            )
            
            # Perform AI analysis
            try:
                # Get file path for analysis
                file_path = resume.file.path
                
                # Add timeout handling for long-running analysis
                import threading
                import queue
                
                def analyze_with_timeout():
                    return resume_analyzer.analyze_resume(file_path, file_extension[1:])
                
                # Create a queue to get the result
                result_queue = queue.Queue()
                
                # Run analysis in a separate thread
                analysis_thread = threading.Thread(target=lambda: result_queue.put(analyze_with_timeout()))
                analysis_thread.start()
                
                # Wait for completion with timeout (60 seconds)
                analysis_thread.join(timeout=60)
                
                if analysis_thread.is_alive():
                    # Analysis timed out
                    analysis_log.status = 'TIMEOUT'
                    analysis_log.success = False
                    analysis_log.error_message = 'Analysis timed out after 60 seconds'
                    analysis_log.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Resume analysis timed out. Please try again with a smaller file.'})
                    messages.error(request, "Resume analysis timed out. Please try again with a smaller file.")
                    return redirect('upload_resume')
                
                # Get the result
                analysis_result = result_queue.get()
                
                if analysis_result['success']:
                    # Extract additional data from analysis
                    extracted_text = resume_analyzer.extract_text_from_file(file_path, file_extension[1:])
                    word_count = len(extracted_text.split())
                    character_count = len(extracted_text)
                    
                    # Extract detailed information from analysis details if available
                    details = analysis_result.get('details', {})
                    
                    # Create rating record with comprehensive data
                    rating = ResumeRating.objects.create(
                        resume=resume,
                        overall_score=analysis_result['overall_score'],
                        skills_score=analysis_result['skills_score'],
                        experience_score=analysis_result['experience_score'],
                        education_score=analysis_result['education_score'],
                        format_score=analysis_result['format_score'],
                        keywords_score=analysis_result['keywords_score'],
                        
                        skills_analysis=analysis_result['skills_analysis'],
                        experience_analysis=analysis_result['experience_analysis'],
                        education_analysis=analysis_result['education_analysis'],
                        format_analysis=analysis_result['format_analysis'],
                        keywords_analysis=analysis_result['keywords_analysis'],
                        
                        strengths=analysis_result['strengths'],
                        improvements=analysis_result['improvements'],
                        recommendations=json.dumps(analysis_result['recommendations']),
                        
                        processing_time=analysis_result['processing_time'],
                        confidence_score=analysis_result['confidence_score'],
                        
                        # Additional analysis data
                        extracted_text=extracted_text,
                        word_count=word_count,
                        character_count=character_count,
                        
                        # Analysis details
                        skills_found=details.get('skills', {}),
                        experience_years=details.get('experience_years', 0.0),
                        education_level=details.get('education_level', ''),
                        contact_methods=details.get('contact_methods', 0),
                        bullet_points=details.get('bullet_points', 0),
                        
                        # Analysis metadata
                        analysis_version='1.0'
                    )
                    
                    # Update resume and log status
                    resume.processed = True
                    resume.save()
                    
                    analysis_log.status = 'COMPLETED'
                    analysis_log.success = True
                    analysis_log.processing_time = analysis_result['processing_time']
                    analysis_log.save()
                    
                    messages.success(request, f"Resume analyzed successfully! Overall Score: {analysis_result['overall_score']}/100")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True, 
                            'resume_id': resume.id,
                            'message': f"Resume analyzed successfully! Overall Score: {analysis_result['overall_score']}/100"
                        })
                    
                else:
                    # Analysis failed
                    analysis_log.status = 'FAILED'
                    analysis_log.success = False
                    analysis_log.error_message = analysis_result['error']
                    analysis_log.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': f"Resume analysis failed: {analysis_result['error']}"})
                    messages.error(request, f"Resume analysis failed: {analysis_result['error']}")
                    return redirect('upload_resume')
                    
            except Exception as e:
                # Log the error
                analysis_log.status = 'ERROR'
                analysis_log.success = False
                analysis_log.error_message = f"Resume analysis error: {str(e)}"
                analysis_log.processing_time = time.time() - start_time
                analysis_log.save()
                
                return {
                    'success': False,
                    'error': f"Resume analysis failed: {str(e)}",
                    'processing_time': time.time() - start_time
                }
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': f"Upload failed: {str(e)}"})
            messages.error(request, f"Upload failed: {str(e)}")
            return redirect('upload_resume')
    
    # GET request - show upload form
    context = {
        'user': user
    }
    return render(request, 'resumeanalysis/upload_resume.html', context)

def my_resumes(request):
    """Display user's uploaded resumes"""
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please login to view your resumes.")
        return redirect('unified_login')
    
    # Get user's resume analyses from resumeanalysis app
    from resumeanalysis.models import ResumeAnalysis, RoleQuiz
    resumes = ResumeAnalysis.objects.filter(user=user).order_by('-created_at')
    
    # Calculate processed count
    processed_count = resumes.count()
    
    # Add quiz information to each resume
    for resume in resumes:
        try:
            quiz = RoleQuiz.objects.get(resume_analysis=resume, status='completed')
            resume.has_quiz = True
            resume.quiz_id = quiz.id
        except RoleQuiz.DoesNotExist:
            resume.has_quiz = False
            resume.quiz_id = None
    
    # Helper function to format file size
    def format_file_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 1)
        return f"{s} {size_name[i]}"
    
    # Add formatted file sizes and normalize scores for template
    for resume in resumes:
        if resume.resume_file:
            try:
                resume.formatted_file_size = format_file_size(resume.resume_file.size)
            except:
                resume.formatted_file_size = "Unknown"
        else:
            resume.formatted_file_size = "No file"
        
        # Normalize score names for template (my_resumes.html uses skills_score)
        if hasattr(resume, 'skills_match_score') and not hasattr(resume, 'skills_score'):
            resume.skills_score = resume.skills_match_score
        
        # Use ATS score for display
        score = resume.ats_score if hasattr(resume, 'ats_score') else 0
        resume.stroke_dashoffset = 251 - (score * 2.51)
    
    context = {
        'resumes': resumes,
        'processed_count': processed_count,
        'user': user
    }
    
    return render(request, 'users/my_resumes.html', context)

@require_POST
@csrf_exempt
def analyze_resume_api(request):
    """API endpoint for resume analysis"""
    try:
        # Get user from session or Django auth
        from users.utils import get_user_registration
        user = get_user_registration(request)
        
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'})
        
        # Get resume ID
        resume_id = request.POST.get('resume_id')
        if not resume_id:
            return JsonResponse({'success': False, 'error': 'Resume ID required'})
        
        # Get resume
        try:
            resume = Resume.objects.get(id=resume_id, user=user)
        except Resume.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Resume not found'})
        
        # Check if already processed
        if resume.processed:
            try:
                rating = resume.rating
                return JsonResponse({
                    'success': True,
                    'already_processed': True,
                    'overall_score': rating.overall_score,
                    'skills_score': rating.skills_score,
                    'experience_score': rating.experience_score,
                    'education_score': rating.education_score,
                    'format_score': rating.format_score,
                    'keywords_score': rating.keywords_score
                })
            except ResumeRating.DoesNotExist:
                pass  # Continue with re-analysis
        
        # Perform analysis
        file_extension = resume.file_type
        file_path = resume.file.path
        
        analysis_result = resume_analyzer.analyze_resume(file_path, file_extension)
        
        if analysis_result['success']:
            # Save results
            rating = ResumeRating.objects.create(
                resume=resume,
                overall_score=analysis_result['overall_score'],
                skills_score=analysis_result['skills_score'],
                experience_score=analysis_result['experience_score'],
                education_score=analysis_result['education_score'],
                format_score=analysis_result['format_score'],
                keywords_score=analysis_result['keywords_score'],
                
                skills_analysis=analysis_result['skills_analysis'],
                experience_analysis=analysis_result['experience_analysis'],
                education_analysis=analysis_result['education_analysis'],
                format_analysis=analysis_result['format_analysis'],
                keywords_analysis=analysis_result['keywords_analysis'],
                
                strengths=analysis_result['strengths'],
                improvements=analysis_result['improvements'],
                recommendations=json.dumps(analysis_result['recommendations']),
                
                processing_time=analysis_result['processing_time'],
                confidence_score=analysis_result['confidence_score']
            )
            
            # Update resume status
            resume.processed = True
            resume.save()
            
            return JsonResponse({
                'success': True,
                'overall_score': analysis_result['overall_score'],
                'skills_score': analysis_result['skills_score'],
                'experience_score': analysis_result['experience_score'],
                'education_score': analysis_result['education_score'],
                'format_score': analysis_result['format_score'],
                'keywords_score': analysis_result['keywords_score'],
                'processing_time': analysis_result['processing_time']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': analysis_result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def download_resume(request, resume_id):
    """Download resume file"""
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please login to download resume.")
        return redirect('unified_login')
    
    # Get resume analysis from resumeanalysis app
    from resumeanalysis.models import ResumeAnalysis
    resume = get_object_or_404(ResumeAnalysis, id=resume_id, user=user)
    
    # Serve file
    try:
        if resume.resume_file:
            file_path = resume.resume_file.path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachment; filename="{resume.original_filename}"'
                    return response
            else:
                messages.error(request, "Resume file not found.")
                return redirect('my_resumes')
        else:
            messages.error(request, "No file associated with this resume.")
            return redirect('my_resumes')
    except Exception as e:
        messages.error(request, f"Error downloading file: {str(e)}")
        return redirect('my_resumes')

def delete_resume(request, resume_id):
    """Delete resume and its analysis"""
    from users.utils import get_user_registration
    user = get_user_registration(request)
    
    if not user:
        messages.error(request, "Please login to delete resume.")
        return redirect('unified_login')
    
    # Get resume analysis from resumeanalysis app
    from resumeanalysis.models import ResumeAnalysis
    resume = get_object_or_404(ResumeAnalysis, id=resume_id, user=user)
    
    try:
        # Delete file
        if resume.resume_file and os.path.exists(resume.resume_file.path):
            os.remove(resume.resume_file.path)
        
        # Delete database record
        resume.delete()
        
        messages.success(request, "Resume deleted successfully.")
        return redirect('my_resumes')
        
    except Exception as e:
        messages.error(request, f"Error deleting resume: {str(e)}")
        return redirect('my_resumes')
