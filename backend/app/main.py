from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import get_db
from app.auth import get_password_hash
from app.routes import auth, candidates, jobs, scheduler, emails, chat

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins in local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(candidates.router, prefix=f"{settings.API_V1_STR}/candidates", tags=["candidates"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])
app.include_router(scheduler.router, prefix=f"{settings.API_V1_STR}/scheduler", tags=["scheduler"])
app.include_router(emails.router, prefix=f"{settings.API_V1_STR}/emails", tags=["emails"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

@app.on_event("startup")
def seed_database():
    db = get_db()
    
    # 1. Seed Recruiter Account if empty
    users_coll = db["users"]
    if users_coll.count_documents({"email": "recruiter@hiregenie.ai"}) == 0:
        hashed_pwd = get_password_hash("password123")
        users_coll.insert_one({
            "name": "HR Recruiter",
            "email": "recruiter@hiregenie.ai",
            "hashed_password": hashed_pwd,
            "role": "Recruiter"
        })
        print("Database seeded with default recruiter: recruiter@hiregenie.ai / password123")
        
    # 2. Seed Job Descriptions if empty
    jobs_coll = db["job_descriptions"]
    if jobs_coll.count_documents({}) == 0:
        # Seed Python Job
        jobs_coll.insert_one({
            "_id": "job_python_developer",
            "title": "Senior Python Developer",
            "description": "We are seeking a talented Senior Python Developer to join our core backend engineering team. You will build high-performance APIs and orchestrate background processing engines.",
            "requirements": "Python, SQL, PostgreSQL, Docker, AWS, FastAPI",
            "experience_years": 4,
            "education_requirements": "Bachelor's Degree in Computer Science or equivalent experience",
            "created_at": "2026-07-01T00:00:00"
        })
        
        # Seed React Job
        jobs_coll.insert_one({
            "_id": "job_react_engineer",
            "title": "React Frontend Engineer",
            "description": "Looking for a React developer to build state-of-the-art Web Application workspaces. You will optimize UI rendering, handle global state Management, and design sleek components.",
            "requirements": "React, TypeScript, JavaScript, CSS, HTML, Tailwind CSS",
            "experience_years": 3,
            "education_requirements": "Bachelor's Degree in Computer Science or equivalent",
            "created_at": "2026-07-01T00:00:00"
        })
        print("Database seeded with sample Job Descriptions!")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "llm_mode": "Mock LLM" if settings.USE_MOCK_LLM else "OpenAI GPT-4",
        "message": "Welcome to HireGenie AI API Backend."
    }
