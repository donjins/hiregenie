import requests
import sys

def test_create_job():
    print("="*60)
    print("        HIREGENIE AI - JOB CREATION DIAGNOSTIC        ")
    print("="*60)
    
    BASE_URL = "http://127.0.0.1:8000/api/v1"
    
    # 1. Login to get token
    print("1. Attempting to log in as default recruiter...")
    login_payload = {
        "username": "recruiter@hiregenie.ai",
        "password": "password123"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
        if r.status_code != 200:
            print(f"❌ Login failed with status code {r.status_code}")
            print(f"Response: {r.text}")
            return
            
        token = r.json().get("access_token")
        print("✅ Login successful! Token retrieved.")
    except Exception as e:
        print(f"❌ Connection to backend failed: {e}")
        print("Please make sure your FastAPI server is active and running on http://127.0.0.1:8000")
        return
        
    # 2. Attempt to post a job
    print("\n2. Attempting to post a sample job position...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    job_payload = {
        "title": "System Diagnostic Test Role",
        "description": "This is a diagnostic job role created by the test script.",
        "requirements": "Python, Diagnostic, SQL",
        "experience_years": 2,
        "education_requirements": "Bachelor's Degree"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/jobs/", json=job_payload, headers=headers)
        print(f"Response Status Code: {r.status_code}")
        print(f"Response Body: {r.text}")
        
        if r.status_code == 201:
            print("\n✅ SUCCESS: Job position was successfully written to the database!")
        else:
            print("\n❌ FAILURE: Backend refused to write the job description.")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_create_job()
