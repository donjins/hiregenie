import json
import logging
from datetime import datetime
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from app.config import settings
from app.agents.agent_factory import email_agent
from app.database import get_db

logger = logging.getLogger("hiregenie.emails")

def generate_and_send_email(candidate_name: str, candidate_email: str, job_title: str, template_type: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generates and sends recruitment notifications using the LangChain email_agent."""
    if settings.USE_MOCK_LLM:
        # Fallback local logic
        db = get_db()
        email_record = {
            "candidate_name": candidate_name,
            "recipient_email": candidate_email,
            "job_title": job_title,
            "subject": f"Update regarding your application for {job_title}",
            "body": f"Dear {candidate_name},\n\nWe are reviewing your application.",
            "type": template_type,
            "status": "Sent",
            "sent_at": datetime.utcnow().isoformat()
        }
        res = db["emails"].insert_one(email_record)
        email_record["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
        return email_record

    details = details or {}
    prompt = (
        f"Draft and send a recruitment email to candidate '{candidate_name}' (Email: '{candidate_email}') "
        f"for job title '{job_title}'. Template Type: '{template_type}'. Details: {json.dumps(details, default=str)}"
    )
    
    try:
        response = email_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        structured_res = response.get("structured_response")
        if structured_res:
            return structured_res.model_dump()
    except Exception as e:
        logger.error(f"Error sending email via agent: {e}")
        
    # Fallback
    db = get_db()
    email_record = {
        "candidate_name": candidate_name,
        "recipient_email": candidate_email,
        "job_title": job_title,
        "subject": f"Application status update: {job_title}",
        "body": f"Dear {candidate_name},\n\nThis is an automated update about your application status for {job_title}.",
        "type": template_type,
        "status": "Sent",
        "sent_at": datetime.utcnow().isoformat()
    }
    res = db["emails"].insert_one(email_record)
    email_record["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
    return email_record
