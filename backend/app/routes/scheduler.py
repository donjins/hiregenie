from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user
from app.agents.scheduler_agent import get_available_slots, schedule_interview

router = APIRouter()

class ManualSchedulePayload(BaseModel):
    candidate_id: str
    candidate_name: str
    job_title: str
    time_slot: str

@router.get("/interviews")
def list_interviews(current_user: dict = Depends(get_current_user)):
    db = get_db()
    interviews = list(db["interviews"].find())
    for i in interviews:
        i["id"] = str(i["_id"])
        if "_id" in i:
            del i["_id"]
    return interviews

@router.get("/slots")
def list_slots(current_user: dict = Depends(get_current_user)):
    return {"slots": get_available_slots()}

@router.post("/schedule")
def create_interview(payload: ManualSchedulePayload, current_user: dict = Depends(get_current_user)):
    try:
        event = schedule_interview(
            candidate_id=payload.candidate_id,
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            slot=payload.time_slot
        )
        return {"message": "Interview scheduled successfully", "event": event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
