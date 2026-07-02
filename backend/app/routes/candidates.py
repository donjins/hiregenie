import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from app.database import get_db
from app.auth import get_current_user
from app.agents.graph import run_recruitment_pipeline
from app.agents.ranker_agent import rank_candidates
from app.tools.vector_store_tool import vector_store
from app.config import settings

router = APIRouter()

@router.get("/")
def get_candidates(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = get_db()
    query = {}
    if job_id:
        query["job_id"] = job_id
    candidates = list(db["candidates"].find(query))
    for c in candidates:
        c["id"] = str(c["_id"])
        if "_id" in c:
            del c["_id"]
    return candidates

@router.get("/{candidate_id}")
def get_candidate_details(candidate_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    cand = db["candidates"].find_one({"_id": candidate_id})
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    cand["id"] = str(cand["_id"])
    del cand["_id"]
    return cand

@router.post("/upload")
async def upload_resume(
    job_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported currently.")
        
    db = get_db()
    # Ensure job exists
    job = db["job_descriptions"].find_one({"_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found")

    # Save PDF locally
    file_location = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # Trigger LangGraph Multi-Agent Pipeline
    print(f"Triggering recruitment pipeline for {file.filename}...")
    pipeline_result = run_recruitment_pipeline(file_location, job_id)
    
    if pipeline_result.get("error"):
        # Cleanup
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=pipeline_result["error"])
        
    cand_id = pipeline_result.get("candidate_id")
    profile = pipeline_result.get("candidate_profile")
    
    # Generate content description for semantic indexing
    text_to_embed = f"""
    Name: {profile.get('name')}
    Skills: {', '.join(profile.get('skills', []))}
    Experience: {'; '.join([e.get('role', '') + ' for ' + e.get('duration', '') for e in profile.get('experience', [])])}
    Education: {'; '.join([ed.get('degree', '') + ' at ' + ed.get('institution', '') for ed in profile.get('education', [])])}
    Certifications: {', '.join(profile.get('certifications', []))}
    """
    
    # Index candidate in vector store
    vector_store.add_candidate(cand_id, text_to_embed)
    
    # Log Activity
    db["activity_logs"].insert_one({
        "type": "resume_parsed",
        "description": f"Successfully parsed resume for {profile.get('name')} ({file.filename}).",
        "timestamp": "now"
    })
    
    # Retrieve updated candidate
    updated_cand = db["candidates"].find_one({"_id": cand_id})
    updated_cand["id"] = str(updated_cand["_id"])
    del updated_cand["_id"]
    
    return {
        "message": "Resume uploaded and parsed successfully",
        "candidate": updated_cand,
        "pipeline_summary": pipeline_result.get("match_details", {}).get("summary", "")
    }

@router.get("/search/semantic")
def search_semantic(query: str, current_user: dict = Depends(get_current_user)):
    """Semantic candidate search powered by FAISS."""
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")
        
    results = vector_store.search_candidates(query, top_k=5)
    formatted_results = []
    
    for item in results:
        cand = item["candidate"]
        cand["id"] = str(cand["_id"])
        del cand["_id"]
        formatted_results.append({
            "candidate": cand,
            "score": item["distance"] # distance: lower is closer/better
        })
        
    return formatted_results

@router.get("/rank/{job_id}")
def get_ranked_candidates(job_id: str, current_user: dict = Depends(get_current_user)):
    """Rank all candidates associated with a job description."""
    db = get_db()
    candidates = list(db["candidates"].find({"job_id": job_id}))
    
    if not candidates:
        return {
            "ranked_candidates": [],
            "selection_confidence_score": 0,
            "recruiter_recommendations": "No candidates have applied for this job description yet."
        }
        
    # Standardize ID representations
    for c in candidates:
        c["id"] = str(c["_id"])
        
    results = rank_candidates(candidates)
    return results

@router.post("/{candidate_id}/status")
def update_candidate_status(candidate_id: str, status_payload: dict, current_user: dict = Depends(get_current_user)):
    db = get_db()
    new_status = status_payload.get("status")
    if new_status not in ["Applied", "Shortlisted", "Rejected", "Hired"]:
        raise HTTPException(status_code=400, detail="Invalid status option.")
        
    res = db["candidates"].update_one(
        {"_id": candidate_id},
        {"$set": {"status": new_status}}
    )
    
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Log Activity
    db["activity_logs"].insert_one({
        "type": "status_updated",
        "description": f"Updated candidate {candidate_id} status to {new_status}.",
        "timestamp": "now"
    })
    
    return {"message": f"Candidate status updated to {new_status}"}
