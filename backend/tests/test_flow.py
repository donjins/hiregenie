import sys
import os
import unittest

# Append project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.agents.matcher_agent import match_candidate_to_job
from app.agents.ranker_agent import rank_candidates
from app.agents.question_agent import generate_interview_questions
from app.agents.scheduler_agent import schedule_interview
from app.agents.email_agent import generate_and_send_email

class TestRecruitmentPipelineFlow(unittest.TestCase):
    def setUp(self):
        # Trigger local JSON database mock context
        self.db = get_db()
        
    def test_job_matching_logic(self):
        job = {
            "title": "Senior Python Developer",
            "description": "Looking for a professional Python and SQL coder with AWS Docker.",
            "requirements": "Python, SQL, AWS, Docker",
            "experience_years": 3,
            "education_requirements": "Bachelor's Degree"
        }
        
        # Candidate with perfect match
        perfect_cand = {
            "name": "Jane Developer",
            "skills": ["Python", "SQL", "AWS", "Docker", "Git"],
            "experience": [{"role": "Software Engineer", "duration": "4 years", "description": "Python coder"}],
            "education": [{"degree": "B.S. Computer Science", "institution": "State College"}],
            "certifications": ["AWS Certified Cloud Practitioner"]
        }
        
        result = match_candidate_to_job(perfect_cand, job)
        self.assertEqual(result["recommendation"], "Hire")
        self.assertGreaterEqual(result["match_percentage"], 85)
        
        # Candidate with weak match
        weak_cand = {
            "name": "Junior Dev",
            "skills": ["Java", "HTML", "CSS"],
            "experience": [],
            "education": [],
            "certifications": []
        }
        
        result_weak = match_candidate_to_job(weak_cand, job)
        self.assertEqual(result_weak["recommendation"], "Reject")
        self.assertLess(result_weak["match_percentage"], 50)
        
    def test_ranking_logic(self):
        candidates = [
            {
                "name": "Candidate A",
                "email": "a@test.com",
                "match_details": {"match_percentage": 85, "recommendation": "Hire"},
                "skills": ["Python", "SQL"]
            },
            {
                "name": "Candidate B",
                "email": "b@test.com",
                "match_details": {"match_percentage": 50, "recommendation": "Consider"},
                "skills": ["React"]
            }
        ]
        
        ranking = rank_candidates(candidates)
        self.assertEqual(ranking["ranked_candidates"][0]["name"], "Candidate A")
        self.assertGreater(ranking["selection_confidence_score"], 0)
        
    def test_question_generation(self):
        skills = ["Python", "React"]
        job = {"title": "Full Stack Dev", "requirements": "Python, React"}
        
        questions = generate_interview_questions(skills, job)
        self.assertIn("hr_questions", questions)
        self.assertIn("technical_questions", questions)
        self.assertIn("Beginner", questions["technical_questions"])

if __name__ == "__main__":
    unittest.main()
