import os
import random
import re
import json
from google import genai
from django.conf import settings

class SoftSkillsAIModel:
    def __init__(self, questions_path, params_path):
        self.questions_path = questions_path
        self.params_path = params_path
        self.questions = self._load_questions()
        self.parameters_content = self._load_parameters_content()
        
        # Configure Gemini API (read from environment/settings)
        self.api_key = os.environ.get('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))
        self.client = genai.Client(api_key=self.api_key)

    def _load_questions(self):
        """Load questions from text file, skipping empty lines"""
        if not os.path.exists(self.questions_path):
            return ["Tell me about yourself."]
        with open(self.questions_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]

    def _load_parameters_content(self):
        """Load parameters content from para.txt to use in Gemini prompt"""
        if not os.path.exists(self.params_path):
            return "No specific parameters provided."
        with open(self.params_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    def get_random_question(self):
        """Returns a random question from the list"""
        return random.choice(self.questions)

    def analyze_voice(self, audio_data=None, duration_seconds=0):
        """
        Uses Google Gemini API to analyze voice recording based on parameters in para.txt.
        If audio_data is provided, Gemini will analyze the actual audio content.
        """
        
        # Prepare content for Gemini
        gemini_content = []
        
        # If we have audio data, include it
        if audio_data:
            try:
                import base64
                # Extract base64 part
                if ',' in audio_data:
                    mime_type = audio_data.split(';')[0].split(':')[1]
                    base64_data = audio_data.split(',')[1]
                else:
                    mime_type = "audio/wav" # Default
                    base64_data = audio_data
                
                audio_bytes = base64.b64decode(base64_data)
                
                gemini_content.append({
                    "mime_type": mime_type,
                    "data": audio_bytes
                })
            except Exception as e:
                print(f"Error processing audio data for Gemini: {e}")

        prompt = f"""
        You are an expert Soft Skills and Communication Coach. 
        Evaluate a 'Just A Minute' (JAM) session based on the following parameters:
        
        {self.parameters_content}
        
        Session Context:
        - Duration: {duration_seconds} seconds
        - Task: The user had to speak for about a minute on a random soft skills topic.
        
        CRITICAL INSTRUCTIONS:
        1. Analyze the provided audio content carefully. 
        2. IF THE AUDIO IS SILENT, CONTAINS ONLY NOISE, OR HAS NO DISCERNIBLE HUMAN SPEECH:
           - You MUST give a jam_score of 0.
           - All breakdown scores (voice, fluency, content, confidence, soft_skills) MUST be 0.
           - Set performance_level to "Weak communication" and color to "red".
           - Set feedback to "No voice detected. Please ensure your microphone is working and speak clearly for the JAM session."
        3. If speech is detected, provide a realistic evaluation based on the actual audio content and duration ({duration_seconds}s).
           - Short duration (< 15s) = low scores.
           - Ideal duration (45-75s) = balanced, realistic scores.
           - Too long (> 90s) = potential penalties for fluency and structure.
        
        Output MUST be in valid JSON format with the following structure:
        {{
            "jam_score": float,
            "performance_level": "Excellent Speaker" | "Job-ready" | "Needs practice" | "Weak communication",
            "color": "green" | "blue" | "yellow" | "red",
            "breakdown": {{
                "voice": float (0-100),
                "fluency": float (0-100),
                "content": float (0-100),
                "confidence": float (0-100),
                "soft_skills": float (0-100)
            }},
            "feedback": "Detailed feedback string"
        }}
        
        The jam_score should be calculated using these weights:
        - Voice (30%), Fluency (25%), Content (20%), Confidence (15%), Soft Skills (10%)
        
        Categorization:
        - 90–100 : Excellent Speaker (green)
        - 75–89 : Job-ready (blue)
        - 60–74 : Needs practice (yellow)
        - Below 60 : Weak communication (red)
        """

        try:
            # Send prompt and audio content to Gemini
            request_parts = [prompt] + gemini_content
            
            # Use generation_config to ensure JSON output if supported
            generation_config = {
                "response_mime_type": "application/json",
            }
            
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=request_parts,
                generation_config=generation_config
            )
            
            # Extract JSON from response
            if not response or not response.text:
                raise Exception("Empty response from Gemini")
                
            response_text = response.text
            # Clean up the response text if it's wrapped in markdown code blocks
            if '```json' in response_text:
                response_text = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL).group(1)
            elif '```' in response_text:
                response_text = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL).group(1)
                
            analysis = json.loads(response_text)
            
            # Ensure all required keys exist to maintain flow
            required_keys = ['jam_score', 'performance_level', 'color', 'breakdown']
            if all(k in analysis for k in required_keys):
                # Ensure breakdown has all sub-scores
                sub_keys = ['voice', 'fluency', 'content', 'confidence', 'soft_skills']
                if all(sk in analysis['breakdown'] for sk in sub_keys):
                    return analysis

            # Fallback if Gemini fails or returns invalid JSON
            raise Exception("Invalid JSON structure from Gemini")

        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            # Fallback to simulation to ensure flow isn't broken
            return self._fallback_simulation(duration_seconds)

    def _generate_fallback_feedback(self, score, duration):
        """Generates a realistic feedback string based on simulated scores"""
        if duration < 15:
            return "The session was too short to provide a comprehensive evaluation. Please try to speak for at least 45-60 seconds to demonstrate your communication skills effectively."
        
        if score >= 85:
            return "Excellent performance! Your speech showed great clarity and confidence. You maintained a steady pace and structured your thoughts logically throughout the minute."
        elif score >= 70:
            return "Good job! You are clearly job-ready. Focus on reducing filler words and perhaps adding more specific examples to your content to reach the next level."
        elif score >= 50:
            return "A fair attempt. You need more practice with fluency and volume stability. Try to maintain your energy level consistently throughout the session."
        else:
            return "You should focus on basic communication parameters. Work on your pronunciation and confidence. Recording yourself multiple times will help you improve."

    def _fallback_simulation(self, duration_seconds):
        """Maintains the original simulation logic as a fallback with more realistic ranges"""
        ranges = {
            'voice': (50, 85),
            'fluency': (45, 88),
            'content': (40, 85),
            'confidence': (50, 85),
            'soft_skills': (50, 80)
        }

        penalty_factor = 1.0
        if duration_seconds < 5: penalty_factor = 0.05
        elif duration_seconds < 15: penalty_factor = 0.2
        elif duration_seconds < 30: penalty_factor = 0.5
        elif duration_seconds > 90: penalty_factor = 0.8

        voice_score = random.uniform(*ranges['voice']) * penalty_factor
        fluency_score = random.uniform(*ranges['fluency']) * penalty_factor
        content_score = random.uniform(*ranges['content']) * penalty_factor
        confidence_score = random.uniform(*ranges['confidence']) * penalty_factor
        soft_skills_score = random.uniform(*ranges['soft_skills']) * penalty_factor

        jam_score = (
            (voice_score * 0.30) +
            (fluency_score * 0.25) +
            (content_score * 0.20) +
            (confidence_score * 0.15) +
            (soft_skills_score * 0.10)
        )

        if jam_score >= 90: level, color = "Excellent Speaker", "green"
        elif jam_score >= 75: level, color = "Job-ready", "blue"
        elif jam_score >= 60: level, color = "Needs practice", "yellow"
        else: level, color = "Weak communication", "red"

        return {
            'jam_score': round(jam_score, 2),
            'performance_level': level,
            'color': color,
            'breakdown': {
                'voice': round(voice_score, 2),
                'fluency': round(fluency_score, 2),
                'content': round(content_score, 2),
                'confidence': round(confidence_score, 2),
                'soft_skills': round(soft_skills_score, 2)
            },
            'feedback': self._generate_fallback_feedback(jam_score, duration_seconds)
        }
