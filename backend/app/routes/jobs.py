from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()

class JobDescriptionCreate(BaseModel):
    title: str
    description: str
    requirements: str
    experience_years: int = 2
    education_requirements: str = "Bachelor's Degree"

@router.get("/")
def get_jobs(current_user: dict = Depends(get_current_user)):
    db = get_db()
    jobs = list(db["job_descriptions"].find())
    for j in jobs:
        j["id"] = str(j["_id"])
        if "_id" in j:
            del j["_id"]
    return jobs

@router.get("/{job_id}")
def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    job = db["job_descriptions"].find_one({"_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found")
    job["id"] = str(job["_id"])
    del job["_id"]
    return job

@router.post("/", status_code=201)
def create_job(job_in: JobDescriptionCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    jobs_coll = db["job_descriptions"]
    
    job_record = job_in.model_dump()
    job_record["created_at"] = datetime.utcnow().isoformat()
    
    res = jobs_coll.insert_one(job_record)
    job_record["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
    
    # Log Activity
    db["activity_logs"].insert_one({
        "type": "job_created",
        "description": f"Created new job description: {job_in.title}.",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return job_record

@router.delete("/{job_id}")
def delete_job(job_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    res = db["job_descriptions"].delete_one({"_id": job_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job description not found")
        
    # Cascade clean candidates and scores (optional but good practice)
    db["candidates"].delete_one({"job_id": job_id})
    
    return {"message": "Job description deleted successfully"}
