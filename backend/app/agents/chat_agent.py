import re
from typing import Dict, Any, List
from app.config import settings
from app.database import get_db
from app.tools.vector_store_tool import vector_store
from app.agents.question_agent import generate_interview_questions
from app.agents.scheduler_agent import schedule_interview, DEFAULT_SLOTS
from app.agents.email_agent import generate_and_send_email

def rule_based_chat(query: str) -> str:
    db = get_db()
    query_lower = query.lower()
    
    # 1. Company policy check (RAG)
    if any(term in query_lower for term in ["policy", "reimbursement", "referral", "probation", "background check"]):
        matches = vector_store.search_company_policy(query, top_k=2)
        policy_resp = "\n".join([f"- {m}" for m in matches])
        return f"Based on the company policies retrieved, here is what I found:\n\n{policy_resp}\n\nHope this helps!"

    # 2. Show top X developers (Python, React, etc.)
    match_top = re.search(r'show\s+me\s+(?:the\s+)?(?:top\s+)?(\w+)?\s*(python|react|java|sql|ml|javascript)\s+developer', query_lower)
    if not match_top:
         match_top = re.search(r'top\s+(\d+)?\s*(python|react|java|sql|ml|javascript)\s+developer', query_lower)
         
    if match_top:
        skill = match_top.group(2).capitalize()
        # Find candidates with this skill
        candidates = list(db["candidates"].find())
        matched = []
        for cand in candidates:
            # check if candidate has skill
            if any(skill.lower() == s.lower() for s in cand.get("skills", [])):
                matched.append(cand)
                
        # Sort by ATS score if present
        matched = sorted(matched, key=lambda x: x.get("ats_score", 0), reverse=True)
        
        limit = 5
        limit_match = re.search(r'(?:top\s+)?(\d+)', query_lower)
        if limit_match:
            limit = int(limit_match.group(1))
            
        if not matched:
            return f"I searched the database but couldn't find any candidates with **{skill}** listed in their skills."
            
        results = [f"Here are the top {min(limit, len(matched))} candidates for **{skill}** developer positions:"]
        for idx, cand in enumerate(matched[:limit], start=1):
            ats = cand.get("ats_score", 70)
            results.append(f"{idx}. **{cand['name']}** (Email: {cand['email']}) - ATS Score: **{ats}%** | Status: `{cand.get('status', 'Applied')}`")
        return "\n".join(results)

    # 3. Candidates with > X years of experience
    match_exp = re.search(r'(\d+)\s*years?\s*(?:of\s*)?(\w+)?\s*experience', query_lower)
    if match_exp:
        years = int(match_exp.group(1))
        skill = match_exp.group(2)
        candidates = list(db["candidates"].find())
        matched = []
        for cand in candidates:
            # count years
            cand_years = 0
            for exp in cand.get("experience", []):
                dur = exp.get("duration", "")
                y_m = re.search(r'(\d+)\s*(year|yr)', dur, re.IGNORECASE)
                if y_m:
                    cand_years += int(y_m.group(1))
            if cand_years == 0:
                cand_years = len(cand.get("experience", [])) * 1.5
                
            if cand_years >= years:
                if not skill or any(skill.lower() in s.lower() for s in cand.get("skills", [])):
                    cand["total_exp_years"] = cand_years
                    matched.append(cand)
                    
        matched = sorted(matched, key=lambda x: x.get("ats_score", 0), reverse=True)
        if not matched:
            return f"I couldn't find any candidates matching that experience criteria (>= {years} years)."
            
        res = [f"Found {len(matched)} candidates with {years}+ years of experience:"]
        for idx, cand in enumerate(matched, start=1):
            res.append(f"{idx}. **{cand['name']}** - {int(cand['total_exp_years'])} yrs exp | Skills: {', '.join(cand.get('skills', [])[:3])} | ATS Match: **{cand.get('ats_score', 0)}%**")
        return "\n".join(res)

    # 4. Applicants matching above X%
    match_score = re.search(r'match\s+(?:this\s+job\s+)?above\s+(\d+)\s*%', query_lower)
    if not match_score:
        match_score = re.search(r'above\s+(\d+)\s*%\s*(?:match)?', query_lower)
        
    if match_score:
        min_score = int(match_score.group(1))
        candidates = list(db["candidates"].find())
        matched = [c for c in candidates if c.get("ats_score", 0) >= min_score]
        matched = sorted(matched, key=lambda x: x.get("ats_score", 0), reverse=True)
        
        if not matched:
            return f"No applicants have an ATS score above **{min_score}%**."
            
        res = [f"Found {len(matched)} candidates matching above **{min_score}%**:"]
        for idx, cand in enumerate(matched, start=1):
            res.append(f"{idx}. **{cand['name']}** - Match Score: **{cand.get('ats_score')}%** | Status: `{cand.get('status')}`")
        return "\n".join(res)

    # 5. Summarize a candidate
    match_sum = re.search(r'summarize\s+(?:candidate\s+)?(\w+)(?:\s+(\w+))?', query_lower)
    if match_sum:
        first = match_sum.group(1)
        last = match_sum.group(2) or ""
        name_query = f"{first} {last}".strip()
        
        candidates = list(db["candidates"].find())
        cand = None
        for c in candidates:
            if first in c["name"].lower():
                cand = c
                break
                
        if not cand:
            return f"Could not find candidate matching '{name_query}'."
            
        match_details = cand.get("match_details", {})
        summary_text = f"""### Candidate Summary: **{cand['name']}**
- **Email**: {cand['email']} | **Phone**: {cand['phone']}
- **Status**: `{cand.get('status', 'Applied')}`
- **ATS Match Score**: **{cand.get('ats_score', 0)}%**
- **Key Skills**: {', '.join(cand.get('skills', []))}
- **Education**: {', '.join([e.get('degree','') for e in cand.get('education',[])])}
- **Recruiter Notes**: {match_details.get('summary', 'Profile uploaded and parsed. Recommended for initial screen.')}
- **Strengths**: 
  {chr(10).join(['  - ' + s for s in match_details.get('strengths', ['Solid technical background'])])}
"""
        return summary_text

    # 6. Generate interview questions for an applicant
    if "question" in query_lower or "interview questions" in query_lower:
        candidates = list(db["candidates"].find())
        cand = None
        for c in candidates:
            # Check if name is in query
            if c["name"].lower() in query_lower or any(part in query_lower for part in c["name"].lower().split()):
                cand = c
                break
        if not cand and candidates:
            cand = candidates[0] # fallback to first candidate
            
        if not cand:
            return "No candidates available to generate questions for."
            
        job = db["job_descriptions"].find_one() or {}
        questions = generate_interview_questions(cand.get("skills", []), job)
        
        # Save to database
        db["candidates"].update_one({"_id": cand["_id"]}, {"$set": {"generated_questions": questions}})
        
        hr_q = "\n".join([f"- **Q**: {q.get('question')}\n  *Intent*: {q.get('intent')}" for q in questions["hr_questions"]])
        tech_q = []
        for level, q_list in questions["technical_questions"].items():
            tech_q.append(f"#### {level} Level:")
            for q in q_list:
                tech_q.append(f"- **Q**: {q.get('question')}\n  *Expected Answer*: {q.get('answer')}")
                
        return f"""### Interview Questions for **{cand['name']}**

#### HR Behavioral Questions:
{hr_q}

#### Technical Interview Questions:
{chr(10).join(tech_q)}
"""

    # 7. Schedule an interview
    if "schedule" in query_lower or "book" in query_lower or "interview for" in query_lower:
        candidates = list(db["candidates"].find())
        cand = None
        for c in candidates:
            if c["name"].lower() in query_lower or any(part in query_lower for part in c["name"].lower().split()):
                cand = c
                break
        if not cand and candidates:
            # Fallback to the first candidate who doesn't have an interview scheduled yet
            available_cands = [c for c in candidates if not c.get("interview_scheduled")]
            cand = available_cands[0] if available_cands else candidates[0]
            
        if not cand:
            return "Could not find a suitable candidate to schedule an interview for."
            
        slot = DEFAULT_SLOTS[1] # "Tomorrow at 2:00 PM"
        # Parse custom slot if specified e.g. "tomorrow afternoon", "next monday"
        if "tomorrow morning" in query_lower:
            slot = "Tomorrow at 10:00 AM"
        elif "tomorrow afternoon" in query_lower:
            slot = "Tomorrow at 2:00 PM"
        elif "next monday" in query_lower:
            slot = "Next Monday at 9:30 AM"
            
        job = db["job_descriptions"].find_one() or {}
        event = schedule_interview(
            candidate_id=cand["_id"],
            candidate_name=cand["name"],
            job_title=job.get("title", "Software Developer"),
            slot=slot
        )
        
        return f"Successfully scheduled interview for **{cand['name']}**!\n\n- **Position**: {event['job_title']}\n- **Interviewer**: {event['interviewer']}\n- **Scheduled Time**: **{event['time_slot']}**\n- **Meeting Link**: [Google Meet]({event['meeting_link']})"

    # 8. Send interview invitations / email notifications
    if "send" in query_lower or "email" in query_lower or "invite" in query_lower:
        # Check if candidate name is specified
        candidates = list(db["candidates"].find())
        cand = None
        for c in candidates:
            if c["name"].lower() in query_lower or any(part in query_lower for part in c["name"].lower().split()):
                cand = c
                break
                
        # Send emails to all shortlisted or specific
        if cand:
            job = db["job_descriptions"].find_one() or {}
            email_type = "invitation" if cand.get("interview_scheduled") else "shortlist"
            email = generate_and_send_email(
                candidate_name=cand["name"],
                candidate_email=cand["email"],
                job_title=job.get("title", "Software Developer"),
                template_type=email_type,
                details={
                    "time_slot": cand.get("interview_time", "TBD"),
                    "meeting_link": f"https://meet.google.com/hgf-recr-{cand['_id'][:4]}"
                }
            )
            return f"Sent **{email_type}** email to candidate **{cand['name']}** ({cand['email']}) successfully!"
        else:
            # Bulk email to all shortlisted candidates who haven't been emailed yet or general shortlist notification
            shortlisted = [c for c in candidates if c.get("status") == "Shortlisted"]
            if not shortlisted:
                return "There are no shortlisted candidates to email. Please shortlist candidates first."
                
            sent_count = 0
            job = db["job_descriptions"].find_one() or {}
            for cand in shortlisted:
                generate_and_send_email(
                    candidate_name=cand["name"],
                    candidate_email=cand["email"],
                    job_title=job.get("title", "Software Developer"),
                    template_type="invitation",
                    details={
                        "time_slot": cand.get("interview_time", "Tomorrow at 2:00 PM"),
                        "meeting_link": f"https://meet.google.com/hgf-recr-{cand['_id'][:4]}"
                    }
                )
                sent_count += 1
            return f"Bulk dispatch complete. Sent invitation emails to **{sent_count}** shortlisted candidates."

    # Fallback response
    return """I am HireGenie's recruitment AI assistant. I can help you manage candidates, job matches, and scheduling. Try asking me:
- *"Show me the top 5 Python developers"*
- *"Rank candidates with more than 3 years of React experience"*
- *"Which applicants match this job above 85%?"*
- *"Summarize candidate John Doe"*
- *"Generate interview questions for John Doe"*
- *"Schedule an interview with John Doe for tomorrow afternoon"*
- *"Send interview invitations to shortlisted candidates"*
- *"What is the policy for interview travel reimbursement?"*"""

def llm_chat(query: str) -> str:
    from app.agents.graph import graph
    from langchain_core.messages import HumanMessage
    
    # Invoke the supervisor agent LangGraph workflow
    config = {"configurable": {"thread_id": "global_recruiter_chat"}}
    
    try:
        final_state = graph.invoke(
            {"messages": [HumanMessage(content=query)]}, 
            config=config
        )
        messages = final_state.get("messages", [])
        
        # Search for the supervisor's final answer or the last AI response
        # Typically the supervisor finishes and outputs a message with no name (indicating supervisor/orchestrator)
        for msg in reversed(messages):
            if msg.type == "ai" and getattr(msg, "name", None) is None:
                return msg.content
                
        for msg in reversed(messages):
            if msg.type == "ai":
                return msg.content
                
        return "Task processed successfully."
    except Exception as e:
        print(f"Error in LangGraph chat: {e}. Falling back to Rule-based engine.")
        return rule_based_chat(query)

def get_chat_response(query: str) -> str:
    if settings.USE_MOCK_LLM:
        return rule_based_chat(query)
    else:
        return llm_chat(query)
