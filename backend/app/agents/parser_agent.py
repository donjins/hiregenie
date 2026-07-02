import re
import json
import logging
from typing import Dict, List, Any
from pypdf import PdfReader
from langchain_core.messages import HumanMessage
from app.config import settings
from app.agents.agent_factory import resume_parsing_agent

logger = logging.getLogger("hiregenie.parser")

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""

def heuristic_parse_resume(text: str) -> dict:
    profile = {
        "name": "Candidate",
        "email": "",
        "phone": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "languages": []
    }
    
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        profile["email"] = email_match.group(0)
        local_part = profile["email"].split('@')[0]
        profile["name"] = " ".join([p.capitalize() for p in re.split(r'[\._-]', local_part) if p.isalpha()])
        
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        profile["phone"] = phone_match.group(0)
    else:
        intl_match = re.search(r'\+?\d[\d -\(\)]{8,}\d', text)
        if intl_match:
            profile["phone"] = intl_match.group(0)

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        for line in lines[:3]:
            if len(line.split()) >= 2 and len(line.split()) <= 4 and all(part.isalpha() for part in line.split() if len(part) > 1):
                profile["name"] = line
                break

    known_skills = [
        "Python", "Java", "React", "Node.js", "SQL", "Machine Learning", "Cloud", "DevOps",
        "TypeScript", "JavaScript", "HTML", "CSS", "C++", "C#", "Go", "Docker", "Kubernetes",
        "AWS", "GCP", "Azure", "Git", "FastAPI", "Django", "Flask", "PostgreSQL", "MongoDB",
        "Redis", "Kafka", "PyTorch", "TensorFlow", "Scikit-Learn", "CI/CD", "Terraform"
    ]
    
    found_skills = []
    for skill in known_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found_skills.append(skill)
    profile["skills"] = list(set(found_skills))

    experience_list = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in ["engineer", "developer", "manager", "architect", "analyst", "lead", "intern"]):
            year_match = re.search(r'\b(19\d{2}|20\d{2})\s*[-–]\s*(19\d{2}|20\d{2}|present|current)\b', line, re.IGNORECASE)
            role_desc = line.strip()
            
            desc_lines = []
            j = i + 1
            while j < len(lines) and j < i + 4:
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                if any(term in next_line.lower() for term in ["education", "skills", "experience", "projects", "certifications"]):
                    break
                if any(term in next_line.lower() for term in ["engineer", "developer", "manager", "architect", "lead"]):
                    break
                desc_lines.append(next_line)
                j += 1
                
            experience_list.append({
                "role": role_desc,
                "duration": year_match.group(0) if year_match else "N/A",
                "description": " ".join(desc_lines) if desc_lines else "Experience in this role."
            })
    profile["experience"] = experience_list if experience_list else [{"role": "Software Developer", "duration": "3 years", "description": "General software engineering work."}]

    education_list = []
    for line in lines:
        if any(term in line.lower() for term in ["bachelor", "master", "phd", "ph.d", "b.s", "m.s", "b.tech", "m.tech", "university", "college", "institute"]):
            education_list.append({
                "degree": line.strip(),
                "institution": "University / Institution"
            })
    profile["education"] = education_list if education_list else [{"degree": "B.S. Computer Science", "institution": "State University"}]

    certifications = []
    for line in lines:
        if any(term in line.lower() for term in ["certified", "certification", "cert", "aws", "gcp", "azure", "scrum"]):
            if len(line.strip()) < 80:
                certifications.append(line.strip())
    profile["certifications"] = certifications[:5]

    languages = []
    for lang in ["English", "Spanish", "French", "German", "Mandarin", "Japanese", "Chinese"]:
        if re.search(r'\b' + re.escape(lang) + r'\b', text, re.IGNORECASE):
            languages.append(lang)
    profile["languages"] = languages if languages else ["English"]

    projects = []
    for line in lines:
        if "project" in line.lower() or "portfolio" in line.lower():
            if len(line.strip()) < 60:
                projects.append({
                    "title": line.strip(),
                    "description": "Developed dynamic solutions."
                })
    profile["projects"] = projects[:3] if projects else [{"title": "Personal Portfolio Website", "description": "Showcasing projects and skills."}]

    return profile

def parse_resume(pdf_path: str) -> dict:
    """Parses resume PDF using the LangChain resume_parsing_agent."""
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return heuristic_parse_resume("Empty resume placeholder")
        
    if settings.USE_MOCK_LLM:
        return heuristic_parse_resume(text)
        
    try:
        response = resume_parsing_agent.invoke({"messages": [HumanMessage(content=f"Parse this resume content:\n{text}")]})
        structured_res = response.get("structured_response")
        if structured_res:
            return structured_res.model_dump()
    except Exception as e:
        logger.error(f"Error parsing resume via agent: {e}")
        
    return heuristic_parse_resume(text)
