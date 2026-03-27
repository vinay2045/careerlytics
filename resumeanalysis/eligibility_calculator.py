import json
from typing import Dict, List, Tuple, Any
from .models import ResumeAnalysis, RoleQuiz, RoleEligibility, RecommendedRole

class EligibilityCalculator:
    """Calculate role eligibility and generate recommendations"""
    
    def __init__(self):
        self.role_weights = {
            'frontend': {
                'skills': ['html', 'css', 'javascript', 'react', 'vue', 'typescript', 'responsive-design'],
                'alternative_roles': ['backend', 'fullstack', 'devops', 'datascience']
            },
            'backend': {
                'skills': ['python', 'java', 'nodejs', 'api', 'database', 'microservices'],
                'alternative_roles': ['frontend', 'fullstack', 'devops', 'datascience']
            },
            'fullstack': {
                'skills': ['html', 'css', 'javascript', 'react', 'python', 'nodejs', 'database', 'api'],
                'alternative_roles': ['frontend', 'backend', 'devops', 'datascience']
            },
            'devops': {
                'skills': ['docker', 'kubernetes', 'aws', 'ci-cd', 'monitoring', 'infrastructure'],
                'alternative_roles': ['backend', 'fullstack', 'frontend', 'datascience']
            },
            'datascience': {
                'skills': ['python', 'machine-learning', 'statistics', 'data-analysis', 'pandas', 'numpy'],
                'alternative_roles': ['backend', 'fullstack', 'frontend', 'devops']
            }
        }
    
    def calculate_role_eligibility(self, resume_analysis: ResumeAnalysis, quiz: RoleQuiz) -> Dict[str, Any]:
        """
        Calculate overall eligibility for the target role
        
        Args:
            resume_analysis: Resume analysis results
            quiz: Quiz results
            
        Returns:
            Dictionary with eligibility scores and recommendations
        """
        # Weighted calculation (40% resume, 60% quiz) per paratoconresume.txt
        resume_weighted = resume_analysis.ats_score * 0.4
        quiz_weighted = quiz.total_score * 0.6
        total_eligibility = resume_weighted + quiz_weighted
        
        # Determine eligibility (>= 55 is Medium Risk/Trainable per paratoconresume.txt)
        is_eligible = total_eligibility >= 55
        
        # Generate recommendations
        recommended_roles = self._generate_recommendations(
            resume_analysis, quiz, quiz.target_role
        )
        
        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(
            resume_analysis, quiz, quiz.target_role
        )
        
        return {
            'target_role': quiz.target_role,
            'resume_score_weighted': resume_weighted,
            'quiz_score_weighted': quiz_weighted,
            'total_eligibility': total_eligibility,
            'is_eligible': is_eligible,
            'recommended_roles': recommended_roles,
            'improvement_areas': improvement_areas,
            'warning_level': self._get_warning_level(total_eligibility)
        }
    
    def _generate_recommendations(self, resume_analysis: ResumeAnalysis, 
                               quiz: RoleQuiz, target_role: str) -> List[Dict[str, Any]]:
        """Generate alternative role recommendations based on skills and performance"""
        recommendations = []
        user_skills = set(resume_analysis.skills_extracted)
        
        # Get alternative roles for target role
        alternative_roles = self.role_weights.get(target_role, {}).get('alternative_roles', [])
        
        for alt_role in alternative_roles:
            role_config = self.role_weights.get(alt_role, {})
            required_skills = set(role_config.get('skills', []))
            
            # Calculate skill overlap
            skill_overlap = len(user_skills & required_skills)
            skill_match_percentage = (skill_overlap / len(required_skills)) * 100 if required_skills else 0
            
            # Adjust based on quiz performance
            # Use skill_match_percentage as a proxy for role_specific_score for alternative roles
            quiz_adjustment = self._get_quiz_adjustment(quiz, alt_role, proxy_role_score=skill_match_percentage)
            
            # Calculate final match percentage
            match_percentage = min(100, (skill_match_percentage * 0.4) + (quiz_adjustment * 0.6))
            
            # Generate reasons
            reasons = self._generate_recommendation_reasons(
                user_skills, required_skills, quiz, alt_role, proxy_role_score=skill_match_percentage
            )
            
            if match_percentage >= 40:  # Only include meaningful recommendations
                recommendations.append({
                    'role_name': alt_role,
                    'match_percentage': round(match_percentage, 1),
                    'match_reasons': reasons
                })
        
        # Sort by match percentage
        recommendations.sort(key=lambda x: x['match_percentage'], reverse=True)
        return recommendations[:3]  # Top 3 recommendations
    
    def _get_quiz_adjustment(self, quiz: RoleQuiz, role: str, proxy_role_score: float = None) -> float:
        """Get quiz performance adjustment for alternative role"""
        # Map quiz categories to role relevance
        role_relevance = {
            'frontend': {
                'general_ability': 0.3,
                'tech_fundamentals': 0.3,
                'role_specific': 0.4
            },
            'backend': {
                'general_ability': 0.3,
                'tech_fundamentals': 0.3,
                'role_specific': 0.4
            },
            'fullstack': {
                'general_ability': 0.3,
                'tech_fundamentals': 0.3,
                'role_specific': 0.4
            },
            'devops': {
                'general_ability': 0.3,
                'tech_fundamentals': 0.3,
                'role_specific': 0.4
            },
            'datascience': {
                'general_ability': 0.3,
                'tech_fundamentals': 0.3,
                'role_specific': 0.4
            }
        }
        
        relevance = role_relevance.get(role, role_relevance['frontend'])
        
        # Use proxy score if provided (for alternative roles), otherwise use actual quiz score
        role_score = proxy_role_score if proxy_role_score is not None else quiz.role_specific_score
        
        # Calculate weighted score for this role
        adjusted_score = (
            quiz.general_ability_score * relevance['general_ability'] +
            quiz.tech_fundamentals_score * relevance['tech_fundamentals'] +
            role_score * relevance['role_specific']
        )
        
        return adjusted_score
    
    def _generate_recommendation_reasons(self, user_skills: set, required_skills: set,
                                     quiz: RoleQuiz, role: str, proxy_role_score: float = None) -> List[str]:
        """Generate reasons for role recommendation"""
        reasons = []
        
        # Skill-based reasons
        matching_skills = user_skills & required_skills
        if matching_skills:
            reasons.append(f"Strong match in {len(matching_skills)} key skills")
        
        # Quiz performance reasons
        if quiz.tech_fundamentals_score >= 70:
            reasons.append("Strong technical fundamentals")
        
        if quiz.general_ability_score >= 70:
            reasons.append("Good problem-solving abilities")
        
        # Role-specific reasons
        # Use proxy score if provided, otherwise check if it's the target role (unlikely here)
        role_score = proxy_role_score if proxy_role_score is not None else (
            quiz.role_specific_score if role == quiz.target_role else 0
        )
        
        if role_score >= 60:
            reasons.append("Relevant specialized knowledge")
        
        return reasons[:3]  # Top 3 reasons
    
    def _identify_improvement_areas(self, resume_analysis: ResumeAnalysis,
                                quiz: RoleQuiz, target_role: str) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []
        
        # Resume-based improvements
        if resume_analysis.skills_match_score < 70:
            improvements.append("Develop more role-specific skills")
        
        if resume_analysis.experience_score < 60:
            improvements.append("Gain more relevant work experience")
        
        if resume_analysis.education_score < 70:
            improvements.append("Consider additional certifications or education")
        
        # Quiz-based improvements
        if quiz.general_ability_score < 60:
            improvements.append("Work on problem-solving and analytical skills")
        
        if quiz.tech_fundamentals_score < 60:
            improvements.append("Strengthen technical fundamentals")
        
        if quiz.role_specific_score < 60:
            improvements.append("Deepen role-specific knowledge")
        
        return improvements
    
    def _get_warning_level(self, eligibility_score: float) -> str:
        """Determine warning level based on eligibility score (paratoconresume.txt)"""
        if eligibility_score >= 75:
            return 'Low Risk - job ready'
        elif eligibility_score >= 55:
            return 'Medium Risk - trainable'
        else:
            return 'High Risk - career mismatch'
    
    def generate_role_fit_analysis(self, resume_analysis: ResumeAnalysis,
                                 quiz: RoleQuiz) -> Dict[str, Any]:
        """Generate comprehensive role fit analysis"""
        return {
            'resume_analysis': {
                'ats_score': resume_analysis.ats_score,
                'skills_match': resume_analysis.skills_match_score,
                'experience_relevance': resume_analysis.experience_score,
                'education_background': resume_analysis.education_score,
                'skill_level': resume_analysis.skill_level,
                'extracted_skills': resume_analysis.skills_extracted
            },
            'quiz_performance': {
                'general_ability': quiz.general_ability_score,
                'tech_fundamentals': quiz.tech_fundamentals_score,
                'role_specific': quiz.role_specific_score,
                'total_score': quiz.total_score,
                'time_taken': quiz.time_taken
            },
            'eligibility_breakdown': {
                'resume_weight': 0.4,
                'quiz_weight': 0.6,
                'resume_contribution': resume_analysis.ats_score * 0.4,
                'quiz_contribution': quiz.total_score * 0.6
            }
        }

def calculate_role_eligibility(resume_analysis: ResumeAnalysis, 
                            quiz: RoleQuiz) -> Dict[str, Any]:
    """
    Convenience function to calculate role eligibility
    
    Args:
        resume_analysis: Resume analysis results
        quiz: Quiz results
        
    Returns:
        Eligibility calculation results
    """
    calculator = EligibilityCalculator()
    return calculator.calculate_role_eligibility(resume_analysis, quiz)
