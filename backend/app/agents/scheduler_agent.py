import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
from app.config import settings
from app.agents.agent_factory import calendar_scheduling_agent
from app.database import get_db

logger = logging.getLogger("hiregenie.scheduler")

DEFAULT_SLOTS = [
    "Tomorrow at 10:00 AM",
    "Tomorrow at 2:00 PM",
    "Day after tomorrow at 11:00 AM",
    "Day after tomorrow at 3:30 PM",
    "Next Monday at 9:30 AM",
    "Next Tuesday at 1:00 PM"
]

def get_available_slots(interviewer_id: str = "recruiter_1") -> List[str]:
    return DEFAULT_SLOTS

def schedule_interview(candidate_id: str, candidate_name: str, job_title: str, slot: str, interviewer_email: str = "hiring@hiregenie.ai") -> Dict[str, Any]:
    """Schedules interview by invoking the LangChain calendar_scheduling_agent."""
    if settings.USE_MOCK_LLM:
        # Fallback inline logic
        db = get_db()
        event = {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "job_title": job_title,
            "time_slot": slot,
            "interviewer": "HR Team Leader",
            "interviewer_email": interviewer_email,
            "status": "Scheduled",
            "meeting_link": f"https://meet.google.com/hgf-recr-{candidate_id[:4]}",
            "created_at": datetime.utcnow().isoformat()
        }
        res = db["interviews"].insert_one(event)
        event["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
        
        db["candidates"].update_one(
            {"_id": candidate_id},
            {"$set": {"status": "Shortlisted", "interview_scheduled": True, "interview_time": slot}}
        )
        return event

    prompt = (
        f"Schedule an interview for candidate '{candidate_name}' (ID: '{candidate_id}') "
        f"for position '{job_title}' in time slot '{slot}'."
    )
    
    try:
        response = calendar_scheduling_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        structured_res = response.get("structured_response")
        if structured_res:
            res_dict = structured_res.model_dump()
            res_dict["candidate_id"] = candidate_id
            return res_dict
    except Exception as e:
        logger.error(f"Error scheduling via agent: {e}")
        
    # Fallback to local
    db = get_db()
    event = {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "job_title": job_title,
        "time_slot": slot,
        "interviewer": "HR Team Leader",
        "interviewer_email": interviewer_email,
        "status": "Scheduled",
        "meeting_link": f"https://meet.google.com/hgf-recr-{candidate_id[:4]}",
        "created_at": datetime.utcnow().isoformat()
    }
    res = db["interviews"].insert_one(event)
    event["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
    db["candidates"].update_one(
        {"_id": candidate_id},
        {"$set": {"status": "Shortlisted", "interview_scheduled": True, "interview_time": slot}}
    )
    return event
