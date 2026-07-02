from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import get_current_user
from app.agents.chat_agent import get_chat_response

router = APIRouter()

class ChatQueryPayload(BaseModel):
    message: str

@router.post("/")
def chat_with_agent(payload: ChatQueryPayload, current_user: dict = Depends(get_current_user)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        response = get_chat_response(payload.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
