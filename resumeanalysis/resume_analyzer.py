import re
import json
import time
from collections import Counter
from typing import Dict, List, Tuple, Any

# Role-specific skill mappings
ROLE_SKILLS = {
    'frontend': {
        'core': ['html', 'css', 'javascript', 'react', 'vue', 'angular', 'typescript'],
        'frameworks': ['bootstrap', 'tailwind', 'material-ui', 'antd', 'chakra-ui'],
        'tools': ['git', 'webpack', 'npm', 'yarn', 'figma', 'photoshop'],
        'concepts': ['responsive-design', 'cross-browser', 'accessibility', 'performance', 'seo']
    },
    'backend': {
        'core': ['python', 'java', 'nodejs', 'c#', 'php', 'ruby', 'go'],
        'frameworks': ['django', 'flask', 'express', 'spring', 'laravel', 'rails'],
        'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
        'concepts': ['api-design', 'microservices', 'authentication', 'security', 'scalability']
    },
    'devops': {
        'core': ['docker', 'kubernetes', 'jenkins', 'gitlab-ci', 'github-actions'],
        'cloud': ['aws', 'azure', 'gcp', 'terraform', 'ansible'],
        'monitoring': ['prometheus', 'grafana', 'elk-stack', 'splunk'],
        'concepts': ['ci-cd', 'infrastructure-as-code', 'devsecops', 'automation']
    },
    'datascience': {
        'core': ['python', 'r', 'sql', 'jupyter', 'pandas', 'numpy'],
        'ml': ['scikit-learn', 'tensorflow', 'pytorch', 'keras', 'xgboost'],
        'visualization': ['matplotlib', 'seaborn', 'plotly', 'tableau', 'power-bi'],
        'concepts': ['machine-learning', 'deep-learning', 'statistics', 'data-analysis', 'nlp']
    }
}

# Common tech keywords
TECH_KEYWORDS = [
    'javascript', 'python', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
    'html', 'css', 'typescript', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql',
    'react', 'vue', 'angular', 'django', 'flask', 'express', 'spring', 'laravel',
    'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'linux', 'ubuntu',
    'rest', 'api', 'microservices', 'agile', 'scrum', 'tdd', 'cicd'
]

class ResumeAnalyzer:
    """AI-powered resume analysis system"""
    
    def __init__(self):
        self.processing_start = time.time()
    
    def analyze_resume(self, file_content: str, filename: str, target_role: str) -> Dict[str, Any]:
        """
        Analyze resume content and return comprehensive analysis
        
        Args:
            file_content: Text content of resume
            filename: Original filename
            target_role: Target role for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        # Extract text and clean it
        cleaned_text = self._clean_text(file_content)
        
        # Extract various components
        skills = self._extract_skills(cleaned_text, target_role)
        experience = self._extract_experience(cleaned_text)
        education = self._extract_education(cleaned_text)
        
        # Calculate scores
        scores = self._calculate_scores(skills, experience, education, target_role)
        
        # Determine skill level
        skill_level = self._determine_skill_level(scores['skills_match'], experience['years'])
        
        # Calculate processing time
        processing_time = time.time() - self.processing_start
        
        return {
            'ats_score': scores['total'],
            'skills_extracted': skills,
            'experience_years': experience['years'],
            'skill_level': skill_level,
            'skills_match_score': scores['skills_match'],
            'experience_score': scores['experience'],
            'education_score': scores['education'],
            'format_score': scores['format'],
            'processing_time': processing_time,
            'analysis_version': '1.0'
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\.\,\-\+\#\@\(\)]', ' ', text)
        # Convert to lowercase for processing
        return text.lower().strip()
    
    def _extract_skills(self, text: str, target_role: str) -> List[str]:
        """Extract skills from resume text"""
        found_skills = []
        text_lower = text.lower()
        
        # Get role-specific skills
        role_skills = ROLE_SKILLS.get(target_role, {})
        all_role_skills = []
        for category, skills in role_skills.items():
            all_role_skills.extend(skills)
        
        # Check for role-specific skills
        for skill in all_role_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        # Check for common tech keywords
        for keyword in TECH_KEYWORDS:
            if keyword in text_lower:
                found_skills.append(keyword)
        
        # Extract skills using patterns
        # Programming languages
        prog_languages = re.findall(r'\b(python|java|javascript|c\+\+|c\#|php|ruby|go|rust|swift|kotlin)\b', text_lower)
        found_skills.extend([lang for lang in prog_languages if lang not in found_skills])
        
        # Frameworks and libraries
        frameworks = re.findall(r'\b(react|vue|angular|django|flask|express|spring|laravel|rails)\b', text_lower)
        found_skills.extend([fw for fw in frameworks if fw not in found_skills])
        
        # Tools and platforms
        tools = re.findall(r'\b(git|docker|kubernetes|aws|azure|gcp|jenkins|terraform|ansible)\b', text_lower)
        found_skills.extend([tool for tool in tools if tool not in found_skills])
        
        return list(set(found_skills))  # Remove duplicates
    
    def _extract_experience(self, text: str) -> Dict[str, Any]:
        """Extract work experience information"""
        experience = {
            'years': 0,
            'entries': [],
            'total_months': 0
        }
        
        # Look for years of experience patterns
        year_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience[:\s]*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:work|professional)?'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                experience['years'] = max(int(match) for match in matches)
                break
        
        # Extract individual experience entries
        # Look for date ranges like "2020-2023" or "Jan 2020 - Dec 2023"
        date_ranges = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|\bpresent\b)', text.lower())
        for start, end in date_ranges:
            end_year = 2024 if end == 'present' else int(end)
            months = (end_year - int(start)) * 12
            experience['total_months'] += months
            experience['entries'].append({
                'start': int(start),
                'end': end_year,
                'months': months
            })
        
        # Calculate total years from entries
        if experience['total_months'] > 0:
            experience['years'] = max(experience['years'], experience['total_months'] / 12)
        
        return experience
    
    def _extract_education(self, text: str) -> Dict[str, Any]:
        """Extract education information"""
        education = {
            'degrees': [],
            'has_degree': False,
            'level': 'unknown'
        }
        
        # Degree patterns
        degree_patterns = [
            r'(bachelor|master|phd|doctorate|associate|b\.s\.|m\.s\.|ph\.d\.)',
            r'(b\.tech|m\.tech|m\.c\.a|b\.e\.|m\.e\.)',
            r'(engineering|computer science|information technology|data science)'
        ]
        
        text_lower = text.lower()
        for pattern in degree_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                education['degrees'].extend(matches)
                education['has_degree'] = True
        
        # Determine education level
        if 'phd' in text_lower or 'doctorate' in text_lower:
            education['level'] = 'phd'
        elif 'master' in text_lower or 'm.' in text_lower:
            education['level'] = 'masters'
        elif 'bachelor' in text_lower or 'b.' in text_lower:
            education['level'] = 'bachelors'
        elif 'associate' in text_lower:
            education['level'] = 'associate'
        
        return education
    
    def _calculate_scores(self, skills: List[str], experience: Dict, education: Dict, target_role: str) -> Dict[str, int]:
        """Calculate various scoring components"""
        
        # Skills Match Score (40% of total)
        skills_match = self._calculate_skills_match(skills, target_role)
        
        # Experience Score (30% of total)
        experience_score = self._calculate_experience_score(experience['years'])
        
        # Education Score (15% of total)
        education_score = self._calculate_education_score(education)
        
        # Format Score (15% of total) - simplified for now
        format_score = 85  # Assume decent format
        
        # Calculate weighted total
        total = int(
            (skills_match * 0.4) +
            (experience_score * 0.3) +
            (education_score * 0.15) +
            (format_score * 0.15)
        )
        
        return {
            'skills_match': skills_match,
            'experience': experience_score,
            'education': education_score,
            'format': format_score,
            'total': min(100, total)  # Cap at 100
        }
    
    def _calculate_skills_match(self, skills: List[str], target_role: str) -> int:
        """Calculate skills match score for target role"""
        role_skills = ROLE_SKILLS.get(target_role, {})
        all_required_skills = []
        
        for category, skill_list in role_skills.items():
            all_required_skills.extend(skill_list)
        
        # Count matching skills
        matching_skills = set(skills) & set(all_required_skills)
        
        if not all_required_skills:
            return 50  # Default score if no role skills defined
        
        match_percentage = (len(matching_skills) / len(all_required_skills)) * 100
        
        # Bonus for having extra relevant skills
        bonus = min(20, len(set(skills) - set(all_required_skills)) * 2)
        
        return min(100, match_percentage + bonus)
    
    def _calculate_experience_score(self, years: float) -> int:
        """Calculate experience relevance score"""
        if years >= 10:
            return 100
        elif years >= 7:
            return 90
        elif years >= 5:
            return 80
        elif years >= 3:
            return 70
        elif years >= 2:
            return 60
        elif years >= 1:
            return 50
        else:
            return 30
    
    def _calculate_education_score(self, education: Dict) -> int:
        """Calculate education background score"""
        if not education['has_degree']:
            return 40
        
        level_scores = {
            'phd': 100,
            'masters': 90,
            'bachelors': 80,
            'associate': 70
        }
        
        return level_scores.get(education['level'], 60)
    
    def _determine_skill_level(self, skills_score: int, experience_years: float) -> str:
        """Determine overall skill level"""
        combined_score = (skills_score + min(100, experience_years * 10)) / 2
        
        if combined_score >= 85:
            return 'expert'
        elif combined_score >= 70:
            return 'advanced'
        elif combined_score >= 55:
            return 'intermediate'
        else:
            return 'beginner'

def analyze_resume_text(text_content: str, filename: str, target_role: str) -> Dict[str, Any]:
    """
    Convenience function to analyze resume text
    
    Args:
        text_content: Text content of resume
        filename: Original filename
        target_role: Target role for analysis
        
    Returns:
        Analysis results dictionary
    """
    analyzer = ResumeAnalyzer()
    return analyzer.analyze_resume(text_content, filename, target_role)
