import json
import logging
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
from app.agents.agent_factory import candidate_ranking_agent

logger = logging.getLogger("hiregenie.ranker")

def rank_candidates(candidates_with_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ranks candidates using the LangChain candidate_ranking_agent."""
    # Convert IDs to strings to avoid serialization issues
    serializable_candidates = []
    for cand in candidates_with_scores:
        c = cand.copy()
        if "_id" in c:
            c["id"] = str(c["_id"])
            del c["_id"]
        elif "id" in c:
            c["id"] = str(c["id"])
        serializable_candidates.append(c)
        
    prompt = f"Rank the following candidates for the job: {json.dumps(serializable_candidates, default=str)}"
    
    try:
        response = candidate_ranking_agent.invoke({"messages": [HumanMessage(content=prompt)]})
        structured_res = response.get("structured_response")
        if structured_res:
            return structured_res.model_dump()
    except Exception as e:
        logger.error(f"Error ranking candidates via agent: {e}")
        
    # Heuristic fallback if agent fails
    ranked_list = sorted(
        serializable_candidates, 
        key=lambda x: x.get("match_details", {}).get("match_percentage", 0) if isinstance(x.get("match_details"), dict) else x.get("ats_score", 0), 
        reverse=True
    )
    
    top_candidates = []
    for rank, cand in enumerate(ranked_list[:10], start=1):
        top_candidates.append({
            "rank": rank,
            "id": cand.get("id"),
            "name": cand.get("name"),
            "email": cand.get("email"),
            "match_percentage": cand.get("match_details", {}).get("match_percentage", 0) if isinstance(cand.get("match_details"), dict) else cand.get("ats_score", 0),
            "recommendation": cand.get("match_details", {}).get("recommendation", "Consider") if isinstance(cand.get("match_details"), dict) else "Consider",
            "key_skills": cand.get("skills", [])[:4]
        })
        
    selection_confidence = 0
    if top_candidates:
        top_scores = [c["match_percentage"] for c in top_candidates[:3]]
        selection_confidence = int(sum(top_scores) / len(top_scores))
        
    return {
        "ranked_candidates": top_candidates,
        "selection_confidence_score": selection_confidence,
        "recruiter_recommendations": "Completed fallback ranking."
    }
