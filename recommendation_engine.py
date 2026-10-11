"""
Recommendation Engine for InternSpark
A transparent, modular, rule-based matching engine that operates locally
without external AI APIs.

Scoring Formula:
- 70% of score: Overlap between student skills and required internship skills.
- 30% of score: Match between student interests and internship category.
"""

import re
from typing import List, Dict, Any, Tuple, Set


def parse_tag_list(raw_text: str) -> List[str]:
    """
    Split comma or semicolon separated text into normalized lowercase tokens.
    """
    if not raw_text:
        return []
    # Split by comma, semicolon, or newline
    items = re.split(r'[,;\n]+', raw_text)
    cleaned = []
    for item in items:
        token = item.strip().lower()
        if token:
            cleaned.append(token)
    return cleaned


def normalize_skill(skill: str) -> str:
    """Normalize skill name for fuzzy/synonym matching."""
    s = skill.strip().lower()
    # Normalize punctuation like c++ -> cpp, node.js -> nodejs
    s = re.sub(r'[\.\-\_\s]+', '', s)
    return s


class RuleBasedRecommendationEngine:
    """
    Rule-based recommendation engine for matching student profiles to internships.
    Designed modularly to allow plug-in of future Machine Learning models.
    """

    SKILL_SYNONYMS = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'ai': 'artificialintelligence',
        'ml': 'machinelearning',
        'dl': 'deeplearning',
        'nlp': 'naturallanguageprocessing',
        'frontend': 'front-end',
        'backend': 'back-end',
        'fullstack': 'full-stack',
        'node': 'nodejs',
        'react': 'reactjs',
        'vue': 'vuejs',
        'next': 'nextjs',
        'sql': 'databasesql',
        'postgres': 'postgresql',
        'mongo': 'mongodb',
    }

    @classmethod
    def match_token(cls, token1: str, token2: str) -> bool:
        """Check if two tokens match directly or via synonym/substring."""
        t1 = normalize_skill(token1)
        t2 = normalize_skill(token2)
        if t1 == t2:
            return True
        t1_syn = cls.SKILL_SYNONYMS.get(t1, t1)
        t2_syn = cls.SKILL_SYNONYMS.get(t2, t2)
        if t1_syn == t2_syn:
            return True
        if len(t1) >= 4 and len(t2) >= 4:
            if t1 in t2 or t2 in t1:
                return True
        return False

    @classmethod
    def calculate_match(cls, profile: Dict[str, Any], internship: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the match score and explanation between a student profile and an internship.
        
        Formula:
          Total Score = (0.7 * Skill_Score) + (0.3 * Interest_Score)
        """
        student_skills_raw = profile.get('skills') or ''
        student_interests_raw = profile.get('interests') or ''

        internship_skills_raw = internship.get('required_skills') or ''
        internship_category = (internship.get('category') or '').strip().lower()

        student_skills = parse_tag_list(student_skills_raw)
        student_interests = parse_tag_list(student_interests_raw)
        intern_skills = parse_tag_list(internship_skills_raw)

        # Fallback handling for empty profile
        if not student_skills and not student_interests:
            return {
                'score': 0,
                'skill_score': 0,
                'interest_score': 0,
                'matched_skills': [],
                'missing_skills': intern_skills,
                'total_required_skills': len(intern_skills),
                'interest_match': False,
                'explanation': 'Add your skills and interests in your profile to see personalized match scores.',
                'badge_color': 'gray'
            }

        # 1. 70% Skill Overlap
        matched_skills = []
        missing_skills = []

        if intern_skills:
            for req in intern_skills:
                is_matched = any(cls.match_token(req, s_skill) for s_skill in student_skills)
                if is_matched:
                    matched_skills.append(req.title())
                else:
                    missing_skills.append(req.title())
            skill_ratio = len(matched_skills) / len(intern_skills)
        else:
            skill_ratio = 1.0  # No skills required

        skill_score = skill_ratio * 100.0

        # 2. 30% Interest / Category Overlap
        interest_match = False
        if student_interests and internship_category:
            for interest in student_interests:
                if cls.match_token(interest, internship_category) or interest in internship_category or internship_category in interest:
                    interest_match = True
                    break
        interest_score = 100.0 if interest_match else 0.0

        # Weighted calculation: 70% skill + 30% interest
        total_score = round((0.7 * skill_score) + (0.3 * interest_score))
        total_score = min(max(total_score, 0), 100)

        # Build readable, transparent explanation
        explanation_parts = []
        if intern_skills:
            if len(matched_skills) == len(intern_skills):
                explanation_parts.append(f"Matches all {len(intern_skills)} required skills ({', '.join(matched_skills)})")
            elif matched_skills:
                explanation_parts.append(f"Matches {len(matched_skills)} of {len(intern_skills)} required skills ({', '.join(matched_skills)})")
            else:
                explanation_parts.append(f"No direct skill overlap with your profile ({len(intern_skills)} required)")
        else:
            explanation_parts.append("No specific skills required")

        if interest_match:
            explanation_parts.append(f"Category matches your interest in '{internship.get('category', '')}'")

        explanation = " • ".join(explanation_parts)

        # Color badges for score presentation
        if total_score >= 80:
            badge_color = 'green'
        elif total_score >= 50:
            badge_color = 'purple'
        elif total_score >= 25:
            badge_color = 'blue'
        else:
            badge_color = 'gray'

        return {
            'score': total_score,
            'skill_score': round(skill_score),
            'interest_score': round(interest_score),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'total_required_skills': len(intern_skills),
            'interest_match': interest_match,
            'explanation': explanation,
            'badge_color': badge_color
        }

    @classmethod
    def rank_internships(cls, profile: Dict[str, Any], internships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks a list of internships by match score descending.
        Attaches 'match_details' to each internship dictionary.
        """
        scored_internships = []
        for item in internships:
            # item may be a sqlite3.Row or dict
            item_dict = dict(item)
            details = cls.calculate_match(profile, item_dict)
            item_dict['match_details'] = details
            item_dict['match_score'] = details['score']
            scored_internships.append(item_dict)

        # Sort by match_score descending, then by posted_date/id
        scored_internships.sort(key=lambda x: (x['match_score'], x.get('id', 0)), reverse=True)
        return scored_internships
