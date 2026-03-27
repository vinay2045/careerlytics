import json
import random
import os
from typing import Dict, List, Any
from django.conf import settings

class QuizGenerator:
    """Generate role-specific quizzes with balanced question distribution"""
    
    def __init__(self):
        # Fix BASE_DIR path - it should point to Careerlytics directory
        base_dir = str(settings.BASE_DIR)
        if base_dir == 'D:\\':
            base_dir = 'D:\\Careerlytics'
        self.questions_dir = os.path.join(base_dir, 'resumeanalysis/questions')
        print(f"QuizGenerator initialized with questions_dir: {self.questions_dir}")  # Debug line
        self.question_cache = {}
    
    def generate_quiz(self, target_role: str, difficulty: str = 'mixed') -> Dict[str, Any]:
        """
        Generate a balanced quiz for the specified role
        
        Args:
            target_role: Target role (frontend, backend, devops, datascience)
            difficulty: Difficulty level (easy, medium, hard, mixed)
            
        Returns:
            Dictionary containing quiz questions and metadata
        """
        print(f"Starting quiz generation for target_role: {target_role}")  # Debug line
        
        # Load questions for each category
        general_questions = self._load_questions('general')
        tech_questions = self._load_questions('tech_fundamentals')
        role_questions = self._load_questions(target_role)
        
        print(f"Loaded questions: general={len(general_questions)}, tech={len(tech_questions)}, role={len(role_questions)}")  # Debug line
        
        # Select questions based on distribution (30% General, 30% Tech, 40% Role-specific)
        selected_general = self._select_questions(general_questions, 9, difficulty)
        selected_tech = self._select_questions(tech_questions, 9, difficulty)
        selected_role = self._select_questions(role_questions, 12, difficulty)
        
        # Combine and shuffle questions
        all_questions = selected_general + selected_tech + selected_role
        random.shuffle(all_questions)
        
        # Add question numbers and metadata
        quiz_data = {
            'questions': [
                {
                    'number': i + 1,
                    'id': q['id'],
                    'category': q['category'],
                    'difficulty': q['difficulty'],
                    'question_text': q['question_text'],
                    'options': q['options'],
                    'correct_answer': q.get('correct_answer'),
                    'explanation': q.get('explanation', ''),
                    'tags': q.get('tags', [])
                }
                for i, q in enumerate(all_questions)
            ],
            'metadata': {
                'target_role': target_role,
                'total_questions': len(all_questions),
                'distribution': {
                    'general_ability': len(selected_general),
                    'tech_fundamentals': len(selected_tech),
                    'role_specific': len(selected_role)
                },
                'time_limit': 1800,  # 30 minutes
                'difficulty': difficulty
            }
        }
        
        return quiz_data
    
    def _load_questions(self, category: str) -> List[Dict[str, Any]]:
        """Load questions from JSON file"""
        if category in self.question_cache:
            print(f"Using cached questions for category: {category}")  # Debug line
            return self.question_cache[category]
        
        try:
            file_path = os.path.join(self.questions_dir, category, 'questions.json')
            print(f"Loading questions from: {file_path}")  # Debug line
            print(f"File exists: {os.path.exists(file_path)}")  # Debug line
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")  # Debug line
                return []
                
            with open(file_path, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            print(f"Loaded {len(questions)} questions for category: {category}")  # Debug line
            print(f"First question sample: {questions[0] if questions else 'None'}")  # Debug line
            
            self.question_cache[category] = questions
            return questions
        except FileNotFoundError:
            print(f"Warning: Questions file not found for category: {category} at {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in questions file for category: {category} - {e}")
            return []
        except Exception as e:
            print(f"Unexpected error loading questions for category: {category} - {e}")
            return []
    
    def _select_questions(self, questions: List[Dict[str, Any]], 
                        count: int, difficulty: str) -> List[Dict[str, Any]]:
        """Select questions based on difficulty and count"""
        if not questions:
            return []
        
        # Filter by difficulty if specified
        if difficulty != 'mixed':
            filtered_questions = [q for q in questions if q['difficulty'] == difficulty]
        else:
            filtered_questions = questions
        
        # If not enough questions after filtering, use all available
        if len(filtered_questions) < count:
            selected = filtered_questions
        else:
            selected = random.sample(filtered_questions, count)
        
        return selected
    
    def calculate_quiz_score(self, responses: List[Dict[str, Any]], target_role: str = None) -> Dict[str, int]:
        """
        Calculate quiz scores from user responses
        
        Args:
            responses: List of user responses with question_id and selected_option
            target_role: Optional target role to load relevant questions
            
        Returns:
            Dictionary with scores for each category and total
        """
        # If target_role is provided, load relevant questions to populate cache
        if target_role:
            self._load_questions('general')
            self._load_questions('tech_fundamentals')
            self._load_questions(target_role)

        category_scores = {
            'general_ability': {'correct': 0, 'total': 0},
            'tech_fundamentals': {'correct': 0, 'total': 0},
            'role_specific': {'correct': 0, 'total': 0}
        }
        
        # Map categories to score categories
        category_mapping = {
            'general': 'general_ability',
            'tech_fundamentals': 'tech_fundamentals',
            'frontend': 'role_specific',
            'backend': 'role_specific',
            'devops': 'role_specific',
            'datascience': 'role_specific'
        }
        
        for response in responses:
            question_id = response.get('question_id')
            selected_option = response.get('selected_option')
            
            # Find the question (this would normally come from database)
            question = self._find_question_by_id(question_id)
            if not question:
                continue
            
            category = question['category']
            score_category = category_mapping.get(category, 'general_ability')
            
            # Update scores
            category_scores[score_category]['total'] += 1
            if selected_option == question['correct_answer']:
                category_scores[score_category]['correct'] += 1
        
        # Calculate percentages
        final_scores = {}
        for category, scores in category_scores.items():
            if scores['total'] > 0:
                final_scores[category] = int((scores['correct'] / scores['total']) * 100)
            else:
                final_scores[category] = 0
        
        # Calculate total score (weighted)
        weights = {
            'general_ability': 0.3,
            'tech_fundamentals': 0.3,
            'role_specific': 0.4
        }
        
        total_score = sum(
            final_scores[cat] * weight 
            for cat, weight in weights.items()
        )
        
        final_scores['total'] = int(total_score)
        
        return final_scores
    
    def _find_question_by_id(self, question_id: str) -> Dict[str, Any]:
        """Find question by ID (simplified version)"""
        # In a real implementation, this would query the database
        # For now, search through cached questions
        for category_questions in self.question_cache.values():
            for question in category_questions:
                if question.get('id') == question_id:
                    return question
        return None
    
    def get_quiz_statistics(self, target_role: str) -> Dict[str, Any]:
        """Get statistics about available questions for a role"""
        general_questions = self._load_questions('general')
        tech_questions = self._load_questions('tech_fundamentals')
        role_questions = self._load_questions(target_role)
        
        return {
            'target_role': target_role,
            'available_questions': {
                'general_ability': len(general_questions),
                'tech_fundamentals': len(tech_questions),
                'role_specific': len(role_questions),
                'total': len(general_questions) + len(tech_questions) + len(role_questions)
            },
            'difficulty_distribution': self._get_difficulty_distribution(
                general_questions + tech_questions + role_questions
            )
        }
    
    def _get_difficulty_distribution(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of question difficulties"""
        distribution = {'easy': 0, 'medium': 0, 'hard': 0}
        for question in questions:
            difficulty = question.get('difficulty', 'medium')
            if difficulty in distribution:
                distribution[difficulty] += 1
        return distribution

def generate_role_quiz(target_role: str, difficulty: str = 'mixed') -> Dict[str, Any]:
    """
    Convenience function to generate a role-specific quiz
    
    Args:
        target_role: Target role for the quiz
        difficulty: Difficulty level
        
    Returns:
        Generated quiz data
    """
    generator = QuizGenerator()
    return generator.generate_quiz(target_role, difficulty)

def calculate_quiz_scores(responses: List[Dict[str, Any]], target_role: str = None) -> Dict[str, int]:
    """
    Convenience function to calculate quiz scores
    
    Args:
        responses: List of user responses
        target_role: Optional target role for question lookup
        
    Returns:
        Score breakdown by category
    """
    generator = QuizGenerator()
    return generator.calculate_quiz_score(responses, target_role)
