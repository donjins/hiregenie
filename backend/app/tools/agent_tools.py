import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.tools import tool
from pypdf import PdfReader
import docx
import chromadb
from sentence_transformers import SentenceTransformer
from app.database import get_db

logger = logging.getLogger("hiregenie.tools")
logger.setLevel(logging.INFO)

# Directory configs
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
VECTOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_data")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

# Lazy Loaded Embedding Model
_embedding_model = None
def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Initializing SentenceTransformer model 'all-MiniLM-L6-v2'...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

# Persistent ChromaDB Client
try:
    chroma_path = os.path.join(VECTOR_DIR, "chromadb")
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    logger.info(f"Persistent ChromaDB client initialized at {chroma_path}")
except Exception as e:
    logger.warning(f"Failed to initialize persistent ChromaDB client: {e}. Falling back to In-Memory.")
    chroma_client = chromadb.Client()

# Get or create Chroma collections
candidates_collection = chroma_client.get_or_create_collection(name="candidates")
policies_collection = chroma_client.get_or_create_collection(name="policies")

# Seed initial policies in Chroma if empty
def seed_policies_chroma():
    try:
        if policies_collection.count() == 0:
            policies = [
                {"id": "policy_1", "text": "Equal Opportunity Hiring: HireGenie AI is committed to providing equal employment opportunities to all applicants."},
                {"id": "policy_2", "text": "Interview Travel Reimbursement: Candidates travelling more than 50 miles for onsite interviews are eligible for up to $200 travel reimbursement."},
                {"id": "policy_3", "text": "Background Checks: All employment offers are contingent on a successful criminal background check and education verification."},
                {"id": "policy_4", "text": "Referral Bonus: Employees who refer candidates that are hired and stay for 6 months receive a $1000 referral bonus."},
                {"id": "policy_5", "text": "Probation Period: New hires undergo a 90-day introductory performance review period."},
                {"id": "policy_6", "text": "Work Authorization: Candidates must be legally authorized to work in the country of application without sponsorship requirements, unless specified."}
            ]
            model = get_embedding_model()
            ids = [p["id"] for p in policies]
            texts = [p["text"] for p in policies]
            embeddings = model.encode(texts).tolist()
            
            policies_collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=[{"source": "company_handbook"} for _ in policies]
            )
            logger.info("Seeded policies collection in ChromaDB.")
    except Exception as e:
        logger.error(f"Error seeding policies in ChromaDB: {e}")

# Trigger seeding
seed_policies_chroma()

# --- 12 REQUIRED TOOLS IMPLEMENTATION ---

@tool
def pdf_reader_tool(pdf_path: str) -> str:
    """Extract raw text from a PDF file path.
    
    Args:
        pdf_path: The absolute file path to the PDF document.
    """
    if not os.path.exists(pdf_path):
        return f"Error: PDF file not found at {pdf_path}"
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip() if text else "Error: No text could be extracted from PDF."
    except Exception as e:
        return f"Error reading PDF {pdf_path}: {e}"

@tool
def docx_reader_tool(docx_path: str) -> str:
    """Extract raw text from a Word DOCX file path.
    
    Args:
        docx_path: The absolute file path to the DOCX document.
    """
    if not os.path.exists(docx_path):
        return f"Error: DOCX file not found at {docx_path}"
    try:
        doc = docx.Document(docx_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text).strip()
    except Exception as e:
        return f"Error reading DOCX {docx_path}: {e}"

@tool
def resume_parser_tool(resume_text: str) -> str:
    """Heuristically extracts key entities (email, phone, name, skills) from a resume text segment.
    
    Args:
        resume_text: Raw string text of the resume.
    """
    import re
    profile = {
        "name": "Candidate",
        "email": "",
        "phone": "",
        "skills": []
    }
    # Email extraction
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
    if email_match:
        profile["email"] = email_match.group(0)
        local_part = profile["email"].split('@')[0]
        profile["name"] = " ".join([p.capitalize() for p in re.split(r'[\._-]', local_part) if p.isalpha()])
    
    # Phone extraction
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
    if phone_match:
        profile["phone"] = phone_match.group(0)
    
    # Skills extraction
    known_skills = [
        "Python", "Java", "React", "Node.js", "SQL", "Machine Learning", "Cloud", "DevOps",
        "TypeScript", "JavaScript", "HTML", "CSS", "C++", "C#", "Go", "Docker", "Kubernetes",
        "AWS", "GCP", "Azure", "Git", "FastAPI", "Django", "Flask", "PostgreSQL", "MongoDB",
        "Redis", "Kafka", "PyTorch", "TensorFlow", "Scikit-Learn", "CI/CD", "Terraform"
    ]
    found_skills = []
    for skill in known_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            found_skills.append(skill)
    profile["skills"] = list(set(found_skills))
    
    return json.dumps(profile)

@tool
def ocr_tool(image_path: str) -> str:
    """Simulates OCR text extraction on scanned documents or images.
    
    Args:
        image_path: The file path to the image/scanned resume document.
    """
    # Simple simulated OCR output
    return f"[SIMULATED OCR EXTRACT FOR {os.path.basename(image_path)}]\nJohn Doe\njohn.doe@example.com\nSkills: Python, React, PostgreSQL\nExperience: Software Engineer at BigCorp (2023-present)."

@tool
def embedding_tool(text: str) -> List[float]:
    """Generate vector embedding coordinates for a given text.
    
    Args:
        text: Input string query or document content.
    """
    model = get_embedding_model()
    emb = model.encode(text).tolist()
    return emb

@tool
def chromadb_tool(action: str, collection_name: str, documents: List[str] = None, ids: List[str] = None, query_texts: List[str] = None, top_k: int = 2) -> str:
    """Query, store, or delete documents inside the ChromaDB vector database.
    
    Args:
        action: The action to perform ('add', 'query', 'delete').
        collection_name: Either 'candidates' or 'policies'.
        documents: List of documents to store (for 'add').
        ids: List of unique document identifiers.
        query_texts: Query texts to search (for 'query').
        top_k: Number of nearest matches to return.
    """
    collection = candidates_collection if collection_name == "candidates" else policies_collection
    
    try:
        if action == "add":
            if not documents or not ids:
                return "Error: Missing documents or ids parameter for add action."
            model = get_embedding_model()
            embeddings = model.encode(documents).tolist()
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings
            )
            return f"Successfully added {len(ids)} documents to ChromaDB collection: {collection_name}."
            
        elif action == "query":
            if not query_texts:
                return "Error: Missing query_texts parameter."
            model = get_embedding_model()
            query_embeddings = model.encode(query_texts).tolist()
            res = collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k
            )
            
            output_results = []
            if res and "documents" in res and res["documents"]:
                for idx, doc_list in enumerate(res["documents"]):
                    q_text = query_texts[idx] if idx < len(query_texts) else "query"
                    for match_idx, doc in enumerate(doc_list):
                        doc_id = res["ids"][idx][match_idx]
                        dist = res["distances"][idx][match_idx] if "distances" in res else 0.0
                        output_results.append({
                            "query": q_text,
                            "id": doc_id,
                            "document": doc,
                            "distance": float(dist)
                        })
            return json.dumps(output_results)
            
        elif action == "delete":
            if not ids:
                return "Error: Missing ids parameter for delete action."
            collection.delete(ids=ids)
            return f"Successfully deleted documents with ids: {ids} from collection: {collection_name}."
            
        else:
            return f"Error: Unknown ChromaDB action: {action}"
            
    except Exception as e:
        return f"ChromaDB tool exception: {e}"

@tool
def mongodb_tool(collection: str, action: str, query: str = "{}", document: str = "{}") -> str:
    """Perform queries and updates against the local recruiter database (MongoDB collections).
    
    Args:
        collection: The target collection ('candidates', 'job_descriptions', 'interviews', 'emails', 'activity_logs').
        action: The database operation ('find', 'find_one', 'insert_one', 'update_one', 'delete_one').
        query: JSON string representing the search filter (e.g. '{"job_id": "1"}').
        document: JSON string representing the data to insert or update (e.g. '{"$set": {"status": "Shortlisted"}}').
    """
    db = get_db()
    if collection not in ["candidates", "job_descriptions", "interviews", "emails", "activity_logs"]:
        return f"Error: Collection '{collection}' is not allowed."
        
    coll_obj = db[collection]
    
    try:
        q_dict = json.loads(query) if query else {}
        d_dict = json.loads(document) if document else {}
        
        if action == "find":
            results = list(coll_obj.find(q_dict))
            # Convert ObjectIds to strings
            for r in results:
                if "_id" in r:
                    r["id"] = str(r["_id"])
                    del r["_id"]
            return json.dumps(results)
            
        elif action == "find_one":
            res = coll_obj.find_one(q_dict)
            if res:
                if "_id" in res:
                    res["id"] = str(res["_id"])
                    del res["_id"]
                return json.dumps(res)
            return "null"
            
        elif action == "insert_one":
            res = coll_obj.insert_one(d_dict)
            inserted_id = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
            return json.dumps({"status": "success", "inserted_id": inserted_id})
            
        elif action == "update_one":
            res = coll_obj.update_one(q_dict, d_dict)
            return json.dumps({
                "status": "success", 
                "matched_count": getattr(res, "matched_count", 0), 
                "modified_count": getattr(res, "modified_count", 0)
            })
            
        elif action == "delete_one":
            res = coll_obj.delete_one(q_dict)
            return json.dumps({"status": "success", "deleted_count": getattr(res, "deleted_count", 0)})
            
        else:
            return f"Error: Unknown DB action '{action}'"
            
    except Exception as e:
        return f"Database error in mongodb_tool: {e}"

@tool
def ats_calculator_tool(candidate_profile_json: str, job_description_json: str) -> str:
    """Calculate the ATS compatibility match percentage and gather highlights.
    
    Args:
        candidate_profile_json: Candidate profile JSON string.
        job_description_json: Job Description JSON string.
    """
    try:
        cand = json.loads(candidate_profile_json)
        job = json.loads(job_description_json)
        
        # Calculate skills match
        job_req_skills = [s.strip().lower() for s in job.get("requirements", "").split(",") if s.strip()]
        cand_skills = [s.lower() for s in cand.get("skills", [])]
        
        matched_skills = [s for s in cand_skills if s in job_req_skills]
        missing_skills = [s for s in job_req_skills if s not in cand_skills]
        
        skill_score = (len(matched_skills) / len(job_req_skills) * 100) if job_req_skills else 100
        
        # Experience match
        cand_exp_yrs = 0.0
        for exp in cand.get("experience", []):
            dur = exp.get("duration", "")
            import re
            m = re.search(r'(\d+)\s*(year|yr)', dur, re.IGNORECASE)
            if m:
                cand_exp_yrs += float(m.group(1))
        if cand_exp_yrs == 0.0:
            cand_exp_yrs = len(cand.get("experience", [])) * 1.5
            
        req_exp_yrs = float(job.get("experience_years", 2.0))
        exp_score = 100.0 if cand_exp_yrs >= req_exp_yrs else (cand_exp_yrs / req_exp_yrs * 100.0)
        
        # Weighted aggregate
        ats_score = int((skill_score * 0.6) + (exp_score * 0.4))
        ats_score = min(max(ats_score, 10), 100)
        
        recommendation = "Reject"
        if ats_score >= 80:
            recommendation = "Hire"
        elif ats_score >= 50:
            recommendation = "Consider"
            
        result = {
            "match_percentage": ats_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "estimated_years_experience": cand_exp_yrs,
            "recommendation": recommendation,
            "summary": f"ATS compatibility score: {ats_score}%. Matched skills: {', '.join(matched_skills[:3])}. Missing requirements: {', '.join(missing_skills[:2])}."
        }
        return json.dumps(result)
    except Exception as e:
        return f"Error in ats_calculator_tool: {e}"

@tool
def candidate_ranking_tool(candidates_json: str) -> str:
    """Sort and rank a list of candidates by their ATS match percentages.
    
    Args:
        candidates_json: JSON string representing the array of candidate profiles.
    """
    try:
        candidates = json.loads(candidates_json)
        # Sort candidates
        ranked = sorted(candidates, key=lambda x: x.get("ats_score", 0), reverse=True)
        
        top_ranked = []
        for idx, c in enumerate(ranked, start=1):
            top_ranked.append({
                "rank": idx,
                "id": c.get("id"),
                "name": c.get("name"),
                "email": c.get("email"),
                "ats_score": c.get("ats_score", 0),
                "recommendation": c.get("match_details", {}).get("recommendation", "Consider")
            })
            
        # Selection confidence
        selection_confidence = 0
        if top_ranked:
            top_scores = [c["ats_score"] for c in top_ranked[:3]]
            selection_confidence = int(sum(top_scores) / len(top_scores))
            
        result = {
            "ranked_candidates": top_ranked,
            "selection_confidence_score": selection_confidence,
            "recruiter_recommendations": f"Candidate ranking completed. Lead applicant is {top_ranked[0]['name']} ({top_ranked[0]['ats_score']}%)." if top_ranked else "No candidates found."
        }
        return json.dumps(result)
    except Exception as e:
        return f"Error in candidate_ranking_tool: {e}"

@tool
def email_tool(candidate_name: str, recipient_email: str, job_title: str, template_type: str, details_json: str = "{}") -> str:
    """Simulates sending a recruitment email notification (invitation, shortlisted, rejection) and logs it.
    
    Args:
        candidate_name: The candidate's name.
        recipient_email: Candidate's target email address.
        job_title: Position role description.
        template_type: Must be 'invitation', 'shortlist', 'rejection', or 'offer'.
        details_json: JSON string of placeholders details (e.g. time_slot, meeting_link).
    """
    db = get_db()
    try:
        details = json.loads(details_json) if details_json else {}
        
        time_slot = details.get("time_slot", "Tomorrow at 2:00 PM")
        meeting_link = details.get("meeting_link", "https://meet.google.com/hgf-recr-tbd")
        
        subject = f"Application Status Update - {job_title}"
        body = f"Dear {candidate_name},\n\n"
        
        if template_type == "invitation":
            subject = f"Interview Invitation - HireGenie AI for {job_title}"
            body += f"Thank you for your application. We would like to invite you for an interview.\n\nTime: {time_slot}\nLink: {meeting_link}\n\nWarm regards,\nThe Hiring Team."
        elif template_type == "shortlist":
            subject = f"Application Shortlisted - {job_title}"
            body += f"Congratulations! Your profile has been shortlisted for the {job_title} role. We will reach out shortly with scheduling options."
        elif template_type == "rejection":
            subject = f"Application Update - {job_title}"
            body += f"Thank you for applying for the {job_title} role. Unfortunately, we have decided to pursue other applicants whose skills closer match our needs at this time."
        else:
            body += f"We are updating your status for {job_title}."
            
        email_record = {
            "candidate_name": candidate_name,
            "recipient_email": recipient_email,
            "job_title": job_title,
            "subject": subject,
            "body": body,
            "type": template_type,
            "status": "Sent",
            "sent_at": datetime.utcnow().isoformat()
        }
        
        # Save to DB
        res = db["emails"].insert_one(email_record)
        rec_id = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
        email_record["id"] = rec_id
        if "_id" in email_record:
            del email_record["_id"]
            
        # Log simulated activity
        db["activity_logs"].insert_one({
            "type": "email_sent",
            "description": f"Simulated {template_type} email sent to {candidate_name} ({recipient_email}).",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return json.dumps(email_record)
    except Exception as e:
        return f"Error in email_tool: {e}"

@tool
def calendar_tool(action: str, candidate_id: str, candidate_name: str, job_title: str, slot: str = "") -> str:
    """Fetch availability or book a meeting time slot on the recruitment schedule.
    
    Args:
        action: 'get_slots' or 'schedule'.
        candidate_id: ID of the applicant candidate.
        candidate_name: Candidate name.
        job_title: Position role title.
        slot: Target slot choice string (for 'schedule').
    """
    db = get_db()
    DEFAULT_SLOTS = [
        "Tomorrow at 10:00 AM",
        "Tomorrow at 2:00 PM",
        "Day after tomorrow at 11:00 AM",
        "Next Monday at 9:30 AM"
    ]
    
    try:
        if action == "get_slots":
            return json.dumps({"available_slots": DEFAULT_SLOTS})
            
        elif action == "schedule":
            if not slot:
                slot = DEFAULT_SLOTS[0]
            
            event = {
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "job_title": job_title,
                "time_slot": slot,
                "interviewer": "HR Team Leader",
                "interviewer_email": "hiring@hiregenie.ai",
                "status": "Scheduled",
                "meeting_link": f"https://meet.google.com/hgf-recr-{candidate_id[:4] if candidate_id else 'tbd'}",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save interview record
            res = db["interviews"].insert_one(event)
            event["id"] = str(res.inserted_id) if hasattr(res, "inserted_id") else res.inserted_id
            if "_id" in event:
                del event["_id"]
                
            # Update Candidate Status
            db["candidates"].update_one(
                {"_id": candidate_id},
                {"$set": {"status": "Shortlisted", "interview_scheduled": True, "interview_time": slot}}
            )
            
            # Log activity
            db["activity_logs"].insert_one({
                "type": "interview_scheduled",
                "description": f"Interview scheduled for {candidate_name} ({job_title}) at {slot}.",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return json.dumps(event)
        else:
            return f"Error: Unknown calendar action: {action}"
    except Exception as e:
        return f"Error in calendar_tool: {e}"

@tool
def company_policy_retriever_tool(query: str) -> str:
    """Retrieve company hiring policies, travel reimbursements, and drug check procedures.
    
    Args:
        query: Semantic search query regarding company rules/guidelines.
    """
    try:
        model = get_embedding_model()
        query_embeddings = model.encode([query]).tolist()
        
        res = policies_collection.query(
            query_embeddings=query_embeddings,
            n_results=2
        )
        
        matches = []
        if res and "documents" in res and res["documents"]:
            for doc_list in res["documents"]:
                matches.extend(doc_list)
        return json.dumps(matches if matches else ["No policies match the query."])
    except Exception as e:
        return f"Error in company_policy_retriever_tool: {e}"
