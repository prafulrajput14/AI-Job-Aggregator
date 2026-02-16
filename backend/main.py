from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_all_jobs, add_job, cleanup_old_jobs, create_user, get_user_by_email
from job_fetcher import fetch_jobs_from_web
from auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from celery.result import AsyncResult
from worker import celery_app

# ... 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery removed for local stability

@app.on_event("startup")
def startup_event():
    init_db()
    cleanup_old_jobs()

@app.get("/api")
def read_root():
    return {"message": "Job Aggregator API is running!"}

@app.get("/api/jobs")
def get_jobs(q: str = None, filter_type: str = "All", location: str = None):
    # Map frontend filter_type to backend logic if needed
    # for now pass straight to get_all_jobs
    return get_all_jobs(q, filter_type, location)

class User(BaseModel):
    email: str
    password: str
    full_name: str = None

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(user: User):
    try:
        hashed_password = get_password_hash(user.password)
        create_user(user.email, hashed_password, user.full_name)
        return {"message": "User registered successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Register Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/login")
def login(login_request: LoginRequest):
    user = get_user_by_email(login_request.email)
    
    if not user or not verify_password(login_request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_name": user['full_name']}

from worker import scrape_task

# ... 

# --- Task Management with FastAPI BackgroundTasks (FallBack for Local Dev) ---
tasks = {}

def run_scraper_task(task_id: str, search_term: str, location: str, job_type: str, results_wanted: int):
    tasks[task_id] = {"status": "PENDING", "result": None}
    try:
        print(f"🚀 [Scraper] Starting task {task_id} for {search_term}")
        # Call the synchronous scraper directly
        jobs = fetch_jobs_from_web(search_term, location, job_type=job_type, results_wanted=results_wanted)
        
        count = 0
        for job in jobs:
            try:
                add_job(job)
                count += 1
            except:
                pass

        tasks[task_id] = {"status": "SUCCESS", "result": {"jobs_found": count}}
        print(f"✅ [Scraper] Task {task_id} finished. Found {count} jobs.")
    except Exception as e:
        print(f"❌ [Scraper] Failed: {e}")
        tasks[task_id] = {"status": "FAILURE", "error": str(e)}

@app.post("/api/fetch_jobs")
def trigger_fetch_jobs(
    background_tasks: BackgroundTasks,
    search_term: str, 
    location: str, 
    is_remote: bool = False,
    job_type: str = "fulltime"
):
    import uuid
    task_id = str(uuid.uuid4())
    
    # Start background task locally (No Redis needed)
    background_tasks.add_task(run_scraper_task, task_id, search_term, location, job_type, 10)
    
    return {
        "message": f"Job fetch started for '{search_term}'", 
        "task_id": task_id,
        "status": "queued"
    }

@app.get("/api/tasks/{task_id}")
def get_task_status_local(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return {"status": "PENDING"} 
    return task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
# Server Reload Trigger: Fixed Location Filter Logic
