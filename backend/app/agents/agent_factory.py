import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.middleware import dynamic_model_selection
from app.tools.agent_tools import (
    pdf_reader_tool,
    docx_reader_tool,
    resume_parser_tool,
    ocr_tool,
    embedding_tool,
    chromadb_tool,
    mongodb_tool,
    ats_calculator_tool,
    candidate_ranking_tool,
    email_tool,
    calendar_tool,
    company_policy_retriever_tool
)

logger = logging.getLogger("hiregenie.agents")
logger.setLevel(logging.INFO)

# --- 1. SCHEMAS FOR STRUCTURED OUTPUT ---

class ProjectItem(BaseModel):
    title: str = Field(description="Title of the project")
    description: str = Field(description="Description of what was done in the project")

class ExperienceItem(BaseModel):
    role: str = Field(description="Job title/role")
    duration: str = Field(description="Duration or dates of employment (e.g. 2 years)")
    description: str = Field(description="Bullet points or summary of job description")

class EducationItem(BaseModel):
    degree: str = Field(description="Degree obtained e.g. B.S. in Computer Science")
    institution: str = Field(description="University or school name")

class ResumeParsingOutput(BaseModel):
    name: str = Field(description="Candidate's full name")
    email: str = Field(description="Candidate's email address")
    phone: str = Field(description="Candidate's phone number")
    skills: List[str] = Field(description="List of technical and soft skills extracted")
    experience: List[ExperienceItem] = Field(description="Work experience items")
    education: List[EducationItem] = Field(description="Education items")
    certifications: List[str] = Field(description="Certifications or courses completed")
    projects: List[ProjectItem] = Field(description="Personal or professional projects")
    languages: List[str] = Field(description="Languages spoken")

class ATSMatchingOutput(BaseModel):
    match_percentage: int = Field(description="ATS compatibility score from 10 to 100")
    strengths: List[str] = Field(description="List of candidate's matching strengths for the job")
    weaknesses: List[str] = Field(description="List of candidate gaps or weaknesses for the job")
    missing_skills: List[str] = Field(description="List of skills required by job description but missing from profile")
    recommendation: str = Field(description="Recommendation. Must be one of: 'Hire', 'Consider', or 'Reject'")
    summary: str = Field(description="Concise explanation of why the match score was assigned")

class RankedCandidateItem(BaseModel):
    rank: int = Field(description="Rank position (1-based)")
    id: str = Field(description="Candidate database ID")
    name: str = Field(description="Candidate name")
    email: str = Field(description="Candidate email")
    match_percentage: int = Field(description="Compatibility score percentage")
    recommendation: str = Field(description="Hiring status recommendation")
    key_skills: List[str] = Field(description="Primary candidate skills")

class CandidateRankingOutput(BaseModel):
    ranked_candidates: List[RankedCandidateItem] = Field(description="Top candidates sorted by compatibility score")
    selection_confidence_score: int = Field(description="Confidence rating of overall candidate pool (0-100)")
    recruiter_recommendations: str = Field(description="Summary of recommendations and key hiring strategy highlights")

class LearningResource(BaseModel):
    skill: str = Field(description="Name of the missing skill")
    resource_name: str = Field(description="Title of course, book, or tutorial")
    url: str = Field(description="Search URL or direct resource URL")

class SkillGapOutput(BaseModel):
    missing_skills: List[str] = Field(description="Core technologies required but missing in candidate")
    gap_analysis: str = Field(description="Detailed overview of technical deficiencies")
    proposed_learning_resources: List[LearningResource] = Field(description="Suggested custom online courses or documents")

class HRQuestion(BaseModel):
    question: str = Field(description="Tailored HR behavioral question text")
    intent: str = Field(description="Core attribute evaluated by this question")

class TechQuestion(BaseModel):
    question: str = Field(description="Technical tier question")
    answer: str = Field(description="Ideal response outline expected")

class TechnicalQuestionsMap(BaseModel):
    Beginner: List[TechQuestion] = Field(description="Beginner level technical questions")
    Intermediate: List[TechQuestion] = Field(description="Intermediate level technical questions")
    Advanced: List[TechQuestion] = Field(description="Advanced level technical questions")

class InterviewQuestionOutput(BaseModel):
    hr_questions: List[HRQuestion] = Field(description="Behavioral or personality interview questions")
    technical_questions: TechnicalQuestionsMap = Field(description="Technical interview questions by level")

class RecruiterSummaryOutput(BaseModel):
    candidate_name: str = Field(description="Candidate name")
    ats_score: int = Field(description="ATS Match percentage")
    key_skills: List[str] = Field(description="Key technical skills")
    recruiter_notes: str = Field(description="Professional highlights, summaries, or recruiter review notes")
    strengths: List[str] = Field(description="Candidate's primary strengths")
    recommendation: str = Field(description="One of: 'Hire', 'Consider', or 'Reject'")
    next_steps: str = Field(description="Recommended next actions (e.g. schedule interview)")

class EmailOutput(BaseModel):
    candidate_name: str = Field(description="Name of candidate recipient")
    recipient_email: str = Field(description="Candidate's target email address")
    job_title: str = Field(description="Position role description")
    subject: str = Field(description="Formatted email subject line")
    body: str = Field(description="Formatted email text body")
    template_type: str = Field(description="'invitation', 'shortlist', 'rejection', or 'offer'")
    status: str = Field(description="Status of email action (e.g. 'Sent')")

class CalendarSchedulingOutput(BaseModel):
    candidate_name: str = Field(description="Candidate name")
    job_title: str = Field(description="Position role description")
    time_slot: str = Field(description="Time slot of scheduled interview")
    interviewer: str = Field(description="Interviewer name")
    status: str = Field(description="Current status (e.g. 'Scheduled')")
    meeting_link: str = Field(description="Google Meet or video link")

class CompanyPolicyRAGOutput(BaseModel):
    answer: str = Field(description="Final query response to user's policy questions")
    policy_source_snippets: List[str] = Field(description="List of matched company policy handbook text snippets")

class SemanticSearchResultItem(BaseModel):
    candidate_id: str = Field(description="Candidate ID")
    name: str = Field(description="Candidate name")
    score: float = Field(description="FAISS similarity distance (lower is better)")
    match_summary: str = Field(description="Brief candidate details matching query")

class SemanticSearchOutput(BaseModel):
    candidate_results: List[SemanticSearchResultItem] = Field(description="Matched candidates list")

class SupervisorOutput(BaseModel):
    next_agent: str = Field(
        description="Name of the next agent to execute. Must be EXACTLY one of: "
                    "'resume_parsing_agent', 'ats_matching_agent', 'candidate_ranking_agent', "
                    "'skill_gap_agent', 'interview_question_agent', 'recruiter_summary_agent', "
                    "'email_agent', 'calendar_scheduling_agent', 'policy_rag_agent', "
                    "'semantic_search_agent', or 'FINISH'."
    )
    instructions: str = Field(description="Contextual instructions, files, query prompts, or JSON payloads for the next agent.")

# --- 2. AGENTS CONSTRUCTOR HELPER ---

def _create_classic_agent(system_prompt: str, tools: List[Any], response_format: Any, name: str):
    """Creates a LangChain classic agent with Middleware hooks."""
    api_key = settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else ""
    if not api_key:
        api_key = "mock-key-for-local-testing"
        
    base_model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=api_key
    )
    
    return create_agent(
        model=base_model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[dynamic_model_selection],
        response_format=response_format,
        name=name
    )

# --- 3. 11 REQUIRED AGENTS INITIALIZATION ---

resume_parsing_agent = _create_classic_agent(
    name="resume_parsing_agent",
    system_prompt="You are a professional Resume Parsing Agent. "
                  "Extract structured candidate contact details, skills, education, experience, "
                  "certifications, and project items from candidate text. "
                  "Call pdf_reader_tool, docx_reader_tool, or ocr_tool as necessary to read file inputs. "
                  "Output candidate properties using the ResumeParsingOutput format.",
    tools=[pdf_reader_tool, docx_reader_tool, ocr_tool, resume_parser_tool],
    response_format=ResumeParsingOutput
)

ats_matching_agent = _create_classic_agent(
    name="ats_matching_agent",
    system_prompt="You are an ATS Matching Agent. "
                  "Evaluate a candidate's profile against a target job description description and requirements. "
                  "Calculate compatible score, strengths, and weaknesses. "
                  "Use the ats_calculator_tool to perform the standard compatibility calculations. "
                  "Output structured matching result matching the ATSMatchingOutput schema.",
    tools=[ats_calculator_tool, mongodb_tool],
    response_format=ATSMatchingOutput
)

candidate_ranking_agent = _create_classic_agent(
    name="candidate_ranking_agent",
    system_prompt="You are a Candidate Ranking Agent. "
                  "Analyze a list of candidate profiles associated with a job ID, "
                  "and rank them. Use the candidate_ranking_tool and mongodb_tool "
                  "to fetch applicants and sort them. "
                  "Provide recruiter recommendations matching the CandidateRankingOutput schema.",
    tools=[candidate_ranking_tool, mongodb_tool],
    response_format=CandidateRankingOutput
)

skill_gap_agent = _create_classic_agent(
    name="skill_gap_agent",
    system_prompt="You are a Skill Gap Agent. "
                  "Deeply evaluate missing skills from a candidate's profile compared to a job description. "
                  "Determine appropriate training courses, books, and references. "
                  "Output detailed gaps and proposed learning resources matching the SkillGapOutput schema.",
    tools=[ats_calculator_tool, mongodb_tool],
    response_format=SkillGapOutput
)

interview_question_agent = _create_classic_agent(
    name="interview_question_agent",
    system_prompt="You are an Interview Question Agent. "
                  "Generate tailored behavioral and technical interview questions based on "
                  "the candidate's profile skills and the target job description requirements. "
                  "Return standard HR and technical questions (Beginner/Intermediate/Advanced) "
                  "matching the InterviewQuestionOutput schema.",
    tools=[mongodb_tool],
    response_format=InterviewQuestionOutput
)

recruiter_summary_agent = _create_classic_agent(
    name="recruiter_summary_agent",
    system_prompt="You are a Recruiter Summary Agent. "
                  "Synthesize candidate details, ATS score, matching metrics, and skill gap profiles "
                  "into a concise professional review summary matching the RecruiterSummaryOutput schema.",
    tools=[mongodb_tool],
    response_format=RecruiterSummaryOutput
)

email_agent = _create_classic_agent(
    name="email_agent",
    system_prompt="You are a recruitment Email Agent. "
                  "Draft high-quality candidate communications (interview invitations, shortlists, rejections, or job offers) "
                  "and simulate their dispatch using the email_tool. "
                  "Save sent entries and return structured EmailOutput.",
    tools=[email_tool, mongodb_tool],
    response_format=EmailOutput
)

calendar_scheduling_agent = _create_classic_agent(
    name="calendar_scheduling_agent",
    system_prompt="You are a Calendar Scheduling Agent. "
                  "Query interviewer schedule slots and book interview appointments for candidates. "
                  "Use calendar_tool to book slots and return calendar scheduling outcomes "
                  "matching the CalendarSchedulingOutput schema.",
    tools=[calendar_tool, mongodb_tool],
    response_format=CalendarSchedulingOutput
)

policy_rag_agent = _create_classic_agent(
    name="policy_rag_agent",
    system_prompt="You are a Company Policy RAG Agent. "
                  "Answer HR, onboarding, reimbursement, and background check queries. "
                  "Use company_policy_retriever_tool to fetch matching guidelines from the policy index "
                  "and compile the response in the CompanyPolicyRAGOutput schema.",
    tools=[company_policy_retriever_tool],
    response_format=CompanyPolicyRAGOutput
)

semantic_search_agent = _create_classic_agent(
    name="semantic_search_agent",
    system_prompt="You are a Semantic Search Agent. "
                  "Perform search queries over indexed candidates using chromadb_tool and mongodb_tool. "
                  "Formulate a structured candidate list and matching scores matching the SemanticSearchOutput schema.",
    tools=[chromadb_tool, mongodb_tool],
    response_format=SemanticSearchOutput
)

supervisor_agent = _create_classic_agent(
    name="supervisor_agent",
    system_prompt="You are the recruitment Supervisor Agent. "
                  "You orchestrate the hiring assistant team. "
                  "Determine which specialist agent should execute next based on the conversation history. "
                  "If the task is resolved or you are just chatting, set next_agent to 'FINISH'. "
                  "Valid options for next_agent: "
                  "'resume_parsing_agent', 'ats_matching_agent', 'candidate_ranking_agent', "
                  "'skill_gap_agent', 'interview_question_agent', 'recruiter_summary_agent', "
                  "'email_agent', 'calendar_scheduling_agent', 'policy_rag_agent', "
                  "'semantic_search_agent', 'FINISH'. "
                  "Supply clear, contextual instruction prompts for the routed specialist.",
    tools=[mongodb_tool, chromadb_tool],
    response_format=SupervisorOutput
)

# Specialist agent map
agents_map = {
    "resume_parsing_agent": resume_parsing_agent,
    "ats_matching_agent": ats_matching_agent,
    "candidate_ranking_agent": candidate_ranking_agent,
    "skill_gap_agent": skill_gap_agent,
    "interview_question_agent": interview_question_agent,
    "recruiter_summary_agent": recruiter_summary_agent,
    "email_agent": email_agent,
    "calendar_scheduling_agent": calendar_scheduling_agent,
    "policy_rag_agent": policy_rag_agent,
    "semantic_search_agent": semantic_search_agent
}
