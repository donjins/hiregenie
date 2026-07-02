import json
import logging
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
from app.config import settings
from app.agents.agent_factory import interview_question_agent

logger = logging.getLogger("hiregenie.question")

# Static questions database for heuristic fallback
STATIC_TECH_QUESTIONS = {
    "python": {
        "Beginner": [
            {"question": "Explain the difference between a list and a tuple in Python.", "answer": "Lists are mutable; tuples are immutable."},
            {"question": "What are Python decorators?", "answer": "Decorators modify or extend function behavior dynamically."}
        ],
        "Intermediate": [
            {"question": "How does memory management work in Python?", "answer": "Python uses automatic garbage collection and reference counting on a private heap."}
        ],
        "Advanced": [
            {"question": "Explain Python's GIL.", "answer": "The Global Interpreter Lock prevents multi-threaded CPU execution from executing concurrently in Python."}
        ]
    },
    "react": {
        "Beginner": [
            {"question": "What is the Virtual DOM in React?", "answer": "An in-memory representation of the DOM synced using reconciliation."}
        ]
    }
}

def heuristic_generate_questions(skills: List[str]) -> Dict[str, Any]:
    hr_questions = [
        {"question": "Tell me about yourself and your journey as a software professional.", "intent": "Icebreaker and communication skills check."},
        {"question": "Describe a difficult technical challenge you solved. How did you approach it?", "intent": "Assess problem-solving methodology."}
    ]
    
    tech_questions = {"Beginner": [], "Intermediate": [], "Advanced": []}
    matched_cats = [s.lower() for s in skills if s.lower() in STATIC_TECH_QUESTIONS]
    
    for level in ["Beginner", "Intermediate", "Advanced"]:
        for cat in matched_cats:
            if level in STATIC_TECH_QUESTIONS[cat]:
                tech_questions[level].extend(STATIC_TECH_QUESTIONS[cat][level])
                
        # Supplement default questions
        while len(tech_questions[level]) < 2:
            tech_questions[level].append({
                "question": f"Explain key features and architecture of building robust applications utilizing {skills[0] if skills else 'Software Engineering'}.",
                "answer": "Use modular, clean, documented code and testing."
            })
            
    return {
        "hr_questions": hr_questions,
        "technical_questions": tech_questions
    }

def generate_interview_questions(candidate_skills: List[str], job_desc: Dict[str, Any]) -> Dict[str, Any]:
    """Generates interview questions using the LangChain interview_question_agent."""
    if settings.USE_MOCK_LLM:
        return heuristic_generate_questions(candidate_skills)
        
    prompt = (
        f"Generate interview questions for candidate with skills: {', '.join(candidate_skills)} "
        f"applying for job: {json.dumps(job_desc, default=str)}"
    )
    
    try:
        response = interview_question_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        structured_res = response.get("structured_response")
        if structured_res:
            res_dict = structured_res.model_dump()
            # Map schema lists back to difficulty mappings
            return {
                "hr_questions": res_dict["hr_questions"],
                "technical_questions": {
                    "Beginner": res_dict["technical_questions"]["Beginner"],
                    "Intermediate": res_dict["technical_questions"]["Intermediate"],
                    "Advanced": res_dict["technical_questions"]["Advanced"]
                }
            }
    except Exception as e:
        logger.error(f"Error generating questions via agent: {e}")
        
    return heuristic_generate_questions(candidate_skills)
