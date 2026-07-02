import re
import json
import logging
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage
from app.config import settings
from app.agents.agent_factory import ats_matching_agent

logger = logging.getLogger("hiregenie.matcher")

def heuristic_match_job(candidate: Dict[str, Any], job_desc: Dict[str, Any]) -> Dict[str, Any]:
    # Extract skills from job description text
    job_text = job_desc.get("description", "") + " " + job_desc.get("requirements", "")
    
    known_skills = [
        "Python", "Java", "React", "Node.js", "SQL", "Machine Learning", "Cloud", "DevOps",
        "TypeScript", "JavaScript", "HTML", "CSS", "C++", "C#", "Go", "Docker", "Kubernetes",
        "AWS", "GCP", "Azure", "Git", "FastAPI", "Django", "Flask", "PostgreSQL", "MongoDB",
        "Redis", "Kafka", "PyTorch", "TensorFlow", "Scikit-Learn", "CI/CD", "Terraform"
    ]
    
    job_skills = []
    for skill in known_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', job_text, re.IGNORECASE):
            job_skills.append(skill)
            
    if not job_skills:
        job_skills = ["Python", "SQL", "Git"]
        
    candidate_skills = candidate.get("skills", [])
    
    # Calculate score
    matched_skills = [s for s in candidate_skills if s.lower() in [js.lower() for js in job_skills]]
    missing_skills = [s for s in job_skills if s.lower() not in [cs.lower() for cs in candidate_skills]]
    
    skill_score = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 100
    
    # Education score
    edu_score = 0
    candidate_edu_text = " ".join([e.get("degree", "") for e in candidate.get("education", [])]).lower()
    job_edu_req = job_desc.get("education_requirements", "Bachelor").lower()
    
    if "phd" in job_edu_req or "ph.d" in job_edu_req:
        if "phd" in candidate_edu_text or "ph.d" in candidate_edu_text:
            edu_score = 100
        elif "master" in candidate_edu_text or "m.s" in candidate_edu_text:
            edu_score = 70
        else:
            edu_score = 40
    elif "master" in job_edu_req or "m.s" in job_edu_req:
        if "phd" in candidate_edu_text or "ph.d" in candidate_edu_text or "master" in candidate_edu_text or "m.s" in candidate_edu_text:
            edu_score = 100
        else:
            edu_score = 60
    else:  # Bachelor/Default
        if any(term in candidate_edu_text for term in ["bachelor", "master", "phd", "b.s", "m.s", "b.tech", "degree"]):
            edu_score = 100
        else:
            edu_score = 50
            
    # Experience score
    total_years = 0
    experience_items = candidate.get("experience", [])
    for exp in experience_items:
        duration_str = exp.get("duration", "")
        year_match = re.search(r'(\d+)\s*(year|yr)', duration_str, re.IGNORECASE)
        if year_match:
            total_years += int(year_match.group(1))
            
    if total_years == 0:
        total_years = len(experience_items) * 1.5
 
    required_years = float(job_desc.get("experience_years", 2))
    if total_years >= required_years:
        exp_score = 100
    else:
        exp_score = (total_years / required_years) * 100 if required_years else 100
        
    ats_score = int((skill_score * 0.5) + (edu_score * 0.2) + (exp_score * 0.3))
    ats_score = min(max(ats_score, 10), 100)
    
    strengths = []
    if matched_skills:
        strengths.append(f"Demonstrates proficiency in key technologies: {', '.join(matched_skills[:4])}.")
    if total_years >= required_years:
        strengths.append(f"Meets or exceeds the required {required_years} years of work experience (has ~{int(total_years)} years).")
    else:
        strengths.append("Has direct project or workplace experience in software development.")
        
    if len(candidate.get("education", [])) > 0:
        strengths.append("Possesses relevant academic qualifications.")
 
    weaknesses = []
    if missing_skills:
        weaknesses.append(f"Missing knowledge of relevant requirements: {', '.join(missing_skills[:3])}.")
    if total_years < required_years:
        weaknesses.append(f"Work experience length (~{int(total_years)} years) is below target of {required_years} years.")
 
    if ats_score >= 80:
        recommendation = "Hire"
    elif ats_score >= 50:
        recommendation = "Consider"
    else:
        recommendation = "Reject"
        
    learning_resources = []
    for skill in missing_skills[:3]:
        learning_resources.append({
            "skill": skill,
            "resource_name": f"Official {skill} Documentation & Getting Started Guide",
            "url": f"https://www.google.com/search?q={skill}+learning+course"
        })
    if not learning_resources:
        learning_resources.append({
            "skill": "Advanced Architecture",
            "resource_name": "System Design Primer",
            "url": "https://github.com/donnemartin/system-design-primer"
        })
        
    summary = f"Candidate matches {ats_score}% of requirements. Key strengths include {', '.join(matched_skills[:3]) if matched_skills else 'general engineering background'}. Main skill gap is {', '.join(missing_skills[:2]) if missing_skills else 'none'}."
    
    return {
        "match_percentage": ats_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_skills": missing_skills,
        "recommendation": recommendation,
        "learning_resources": learning_resources,
        "summary": summary
    }

def match_candidate_to_job(candidate: Dict[str, Any], job_desc: Dict[str, Any]) -> Dict[str, Any]:
    """Matches candidate to job using the LangChain ats_matching_agent."""
    if settings.USE_MOCK_LLM:
        return heuristic_match_job(candidate, job_desc)
        
    prompt = (
        f"Compare candidate:\n{json.dumps(candidate, default=str)}\n"
        f"Against job requirements:\n{json.dumps(job_desc, default=str)}"
    )
    
    try:
        response = ats_matching_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        structured_res = response.get("structured_response")
        if structured_res:
            return structured_res.model_dump()
    except Exception as e:
        logger.error(f"Error matching via agent: {e}")
        
    return heuristic_match_job(candidate, job_desc)
