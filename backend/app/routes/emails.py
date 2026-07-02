from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.auth import get_current_user
from app.agents.email_agent import generate_and_send_email

router = APIRouter()

class EmailSendPayload(BaseModel):
    candidate_name: str
    recipient_email: EmailStr
    job_title: str
    template_type: str # invitation, shortlist, rejection, offer
    time_slot: str = "TBD"
    meeting_link: str = "TBD"

@router.get("/")
def list_email_history(current_user: dict = Depends(get_current_user)):
    db = get_db()
    emails = list(db["emails"].find())
    for e in emails:
        e["id"] = str(e["_id"])
        if "_id" in e:
            del e["_id"]
    return emails

@router.post("/send")
def trigger_email(payload: EmailSendPayload, current_user: dict = Depends(get_current_user)):
    if payload.template_type not in ["invitation", "shortlist", "rejection", "offer"]:
        raise HTTPException(status_code=400, detail="Invalid email template type specified.")
        
    try:
        email = generate_and_send_email(
            candidate_name=payload.candidate_name,
            candidate_email=str(payload.recipient_email),
            job_title=payload.job_title,
            template_type=payload.template_type,
            details={
                "time_slot": payload.time_slot,
                "meeting_link": payload.meeting_link
            }
        )
        return {"message": "Email sent successfully", "email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
