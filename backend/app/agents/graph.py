import json
import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, SystemMessage, AIMessage, HumanMessage
from datetime import datetime
from langgraph.checkpoint.memory import MemorySaver
from app.database import get_db

from app.agents.agent_factory import (
    supervisor_agent,
    agents_map,
    ResumeParsingOutput,
    ATSMatchingOutput,
    CandidateRankingOutput,
    SkillGapOutput,
    InterviewQuestionOutput,
    RecruiterSummaryOutput,
    EmailOutput,
    CalendarSchedulingOutput,
    CompanyPolicyRAGOutput,
    SemanticSearchOutput
)

logger = logging.getLogger("hiregenie.graph")
logger.setLevel(logging.INFO)

# --- 1. STATE DEFINITION ---

class OrchestratorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_agent: Optional[str]
    instructions: Optional[str]
    # Storage for structural outputs between stages
    parsing_result: Optional[dict]
    matching_result: Optional[dict]
    ranking_result: Optional[dict]
    skill_gap_result: Optional[dict]
    interview_questions_result: Optional[dict]
    recruiter_summary_result: Optional[dict]
    email_result: Optional[dict]
    scheduling_result: Optional[dict]
    policy_rag_result: Optional[dict]
    semantic_search_result: Optional[dict]

# --- 2. NODE FUNCTIONS ---

def supervisor_node(state: OrchestratorState) -> dict:
    """Invokes supervisor_agent to route the workflow."""
    logger.info("[GRAPH] Running supervisor_node...")
    # Invoke agent with conversation context
    try:
        response = supervisor_agent.invoke({"messages": state["messages"]})
        structured_res = response.get("structured_response")
        
        next_agent = "FINISH"
        instructions = "Wrap up the response."
        
        if structured_res:
            next_agent = structured_res.next_agent
            instructions = structured_res.instructions
            
        logger.info(f"[GRAPH] Supervisor decision: next_agent='{next_agent}', instructions='{instructions[:60]}...'")
        
        return {
            "next_agent": next_agent,
            "instructions": instructions
        }
    except Exception as e:
        logger.error(f"[GRAPH] Supervisor node failed: {e}")
        return {
            "next_agent": "FINISH",
            "instructions": f"Encountered system error: {e}"
        }

def make_specialist_node(agent_name: str, state_key: str):
    """Factory helper to build a node for a specialist agent."""
    def node_func(state: OrchestratorState) -> dict:
        logger.info(f"[GRAPH] Running specialist node '{agent_name}'...")
        agent = agents_map[agent_name]
        
        # Build prompt using instructions
        instructions = state.get("instructions") or "Please perform your tasks."
        agent_messages = list(state["messages"]) + [
            SystemMessage(content=f"Supervisor Instructions: {instructions}")
        ]
        
        try:
            response = agent.invoke({"messages": agent_messages})
            structured_res = response.get("structured_response")
            
            res_dict = {}
            if structured_res:
                # Handle nested pydantic schemas cleanly if present
                if hasattr(structured_res, "model_dump"):
                    res_dict = structured_res.model_dump()
                else:
                    res_dict = dict(structured_res)
                    
            # Log result message in conversation history so supervisor sees outcomes
            result_msg = AIMessage(
                content=f"Agent '{agent_name}' completed task. Output payload:\n{json.dumps(res_dict, indent=2)}",
                name=agent_name
            )
            
            return {
                "messages": [result_msg],
                state_key: res_dict,
                "next_agent": None,
                "instructions": None
            }
        except Exception as e:
            logger.error(f"[GRAPH] Agent {agent_name} failed: {e}")
            err_msg = f"Error running agent {agent_name}: {e}"
            return {
                "messages": [AIMessage(content=err_msg, name=agent_name)],
                "next_agent": "FINISH",
                "instructions": "Error handling."
            }
            
    return node_func

# --- 3. CONSTRUCT STATE GRAPH ---

workflow = StateGraph(OrchestratorState)

# Add supervisor node
workflow.add_node("supervisor", supervisor_node)

# Add specialist nodes using factory
workflow.add_node("resume_parsing_agent", make_specialist_node("resume_parsing_agent", "parsing_result"))
workflow.add_node("ats_matching_agent", make_specialist_node("ats_matching_agent", "matching_result"))
workflow.add_node("candidate_ranking_agent", make_specialist_node("candidate_ranking_agent", "ranking_result"))
workflow.add_node("skill_gap_agent", make_specialist_node("skill_gap_agent", "skill_gap_result"))
workflow.add_node("interview_question_agent", make_specialist_node("interview_question_agent", "interview_questions_result"))
workflow.add_node("recruiter_summary_agent", make_specialist_node("recruiter_summary_agent", "recruiter_summary_result"))
workflow.add_node("email_agent", make_specialist_node("email_agent", "email_result"))
workflow.add_node("calendar_scheduling_agent", make_specialist_node("calendar_scheduling_agent", "scheduling_result"))
workflow.add_node("policy_rag_agent", make_specialist_node("policy_rag_agent", "policy_rag_result"))
workflow.add_node("semantic_search_agent", make_specialist_node("semantic_search_agent", "semantic_search_result"))

# Route supervisor edge
def route_next(state: OrchestratorState) -> str:
    next_agent = state.get("next_agent")
    if not next_agent or next_agent == "FINISH":
        return END
    if next_agent not in agents_map:
        logger.warning(f"[GRAPH] Routing target '{next_agent}' not in agents map. Ending pipeline.")
        return END
    return next_agent

workflow.add_conditional_edges("supervisor", route_next)

# Spoke nodes map back to supervisor hub
for agent_name in agents_map.keys():
    workflow.add_edge(agent_name, "supervisor")

# Set entry point
workflow.set_entry_point("supervisor")

# Compile with memory checkpointing
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# --- 4. GRAPH UTILITY RUNNERS ---

def run_recruitment_pipeline(pdf_path: str, job_id: str) -> dict:
    """Convenience pipeline trigger to run parsing and matching sequentially."""
    logger.info(f"[GRAPH] Running pipeline for resume {pdf_path} and job {job_id}")
    
    # Generate structured input to feed supervisor
    initial_prompt = (
        f"Parse the candidate resume PDF file located at path: '{pdf_path}'. "
        f"Once parsed, match the candidate against Job ID '{job_id}' to calculate ATS score, "
        f"generate technical interview questions, schedule an interview slot, and draft an invitation email."
    )
    
    config = {"configurable": {"thread_id": f"pipeline_run_{job_id}_{datetime_now_str()}"}}
    
    initial_state = {
        "messages": [HumanMessage(content=initial_prompt)],
        "next_agent": None,
        "instructions": None,
        "parsing_result": None,
        "matching_result": None,
        "ranking_result": None,
        "skill_gap_result": None,
        "interview_questions_result": None,
        "recruiter_summary_result": None,
        "email_result": None,
        "scheduling_result": None,
        "policy_rag_result": None,
        "semantic_search_result": None
    }
    
    try:
        final_state = graph.invoke(initial_state, config=config)
        
        # Build structured unified response for legacy routes
        # Check if parsing was success
        parsing_res = final_state.get("parsing_result")
        matching_res = final_state.get("matching_result")
        questions_res = final_state.get("interview_questions_result")
        scheduling_res = final_state.get("scheduling_result")
        email_res = final_state.get("email_result")
        
        # Fallback if agent pipeline failed to run (e.g. 401 Unauthorized API key error)
        if not parsing_res:
            logger.info("Agent parsing returned empty. Falling back to heuristic pipeline execution.")
            from app.agents.parser_agent import heuristic_parse_resume, extract_text_from_pdf
            from app.agents.matcher_agent import heuristic_match_job
            from app.agents.question_agent import heuristic_generate_questions
            from app.agents.scheduler_agent import DEFAULT_SLOTS, schedule_interview as local_schedule
            from app.agents.email_agent import generate_and_send_email
            
            # 1. Parse resume
            resume_text = extract_text_from_pdf(pdf_path)
            parsing_res = heuristic_parse_resume(resume_text)
            
            # Save candidate
            db = get_db()
            existing = db["candidates"].find_one({"email": parsing_res["email"]})
            cand_data = parsing_res.copy()
            cand_data["status"] = "Applied"
            cand_data["job_id"] = job_id
            cand_data["interview_scheduled"] = False
            cand_data["interview_time"] = None
            
            if existing:
                cand_id = str(existing["_id"])
                db["candidates"].update_one({"_id": cand_id}, {"$set": cand_data})
            else:
                res = db["candidates"].insert_one(cand_data)
                cand_id = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
                
            # 2. Match candidate
            job = db["job_descriptions"].find_one({"_id": job_id}) or {}
            matching_res = heuristic_match_job(parsing_res, job)
            db["candidates"].update_one(
                {"_id": cand_id},
                {"$set": {
                    "match_details": matching_res,
                    "ats_score": matching_res["match_percentage"]
                }}
            )
            db["ats_scores"].insert_one({
                "candidate_id": cand_id,
                "job_id": job_id,
                "score": matching_res["match_percentage"],
                "recommendation": matching_res["recommendation"],
                "summary": matching_res["summary"]
            })
            
            # 3. Questions
            questions_res = heuristic_generate_questions(parsing_res.get("skills", []))
            db["candidates"].update_one({"_id": cand_id}, {"$set": {"generated_questions": questions_res}})
            
            # 4. Schedule
            if matching_res["recommendation"] != "Reject":
                slot = DEFAULT_SLOTS[0]
                scheduling_res = local_schedule(cand_id, parsing_res["name"], job.get("title", "Software Developer"), slot)
            else:
                db["candidates"].update_one({"_id": cand_id}, {"$set": {"status": "Rejected"}})
                scheduling_res = None
                
            # 5. Email
            email_type = "rejection" if matching_res["recommendation"] == "Reject" else "invitation"
            email_res = generate_and_send_email(
                candidate_name=parsing_res["name"],
                candidate_email=parsing_res["email"],
                job_title=job.get("title", "Software Developer"),
                template_type=email_type,
                details={
                    "time_slot": scheduling_res.get("time_slot", "TBD") if scheduling_res else "TBD",
                    "meeting_link": scheduling_res.get("meeting_link", "TBD") if scheduling_res else "TBD"
                }
            )
        else:
            db = get_db()
            existing = db["candidates"].find_one({"email": parsing_res["email"]})
            
            cand_data = parsing_res.copy()
            cand_data["status"] = "Applied"
            cand_data["job_id"] = job_id
            
            # Populate ATS score and matching details if matcher_agent executed
            if matching_res:
                cand_data["match_details"] = matching_res
                cand_data["ats_score"] = matching_res.get("match_percentage", 0)
                if matching_res.get("recommendation") == "Reject":
                    cand_data["status"] = "Rejected"
            
            # Populate interview schedules if calendar_scheduling_agent executed
            if scheduling_res:
                cand_data["status"] = "Shortlisted"
                cand_data["interview_scheduled"] = True
                cand_data["interview_time"] = scheduling_res.get("time_slot")
                
            if existing:
                cand_id = str(existing["_id"])
                db["candidates"].update_one({"_id": cand_id}, {"$set": cand_data})
                logger.info(f"Updated candidate {parsing_res['name']} ({cand_id}) in DB via agent pipeline.")
            else:
                res = db["candidates"].insert_one(cand_data)
                cand_id = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
                logger.info(f"Inserted candidate {parsing_res['name']} ({cand_id}) in DB via agent pipeline.")
                
            # Log ATS score entry if matcher ran
            if matching_res:
                db["ats_scores"].insert_one({
                    "candidate_id": cand_id,
                    "job_id": job_id,
                    "score": matching_res.get("match_percentage", 0),
                    "recommendation": matching_res.get("recommendation", "Consider"),
                    "summary": matching_res.get("summary", "")
                })
            
        return {
            "candidate_id": cand_id,
            "candidate_profile": parsing_res,
            "match_details": matching_res,
            "questions": questions_res,
            "interview_event": scheduling_res,
            "email_sent": email_res,
            "error": None
        }
    except Exception as e:
        logger.error(f"Pipeline invocation failed: {e}")
        return {"error": str(e)}

def datetime_now_str() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
