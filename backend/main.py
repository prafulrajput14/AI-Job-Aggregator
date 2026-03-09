from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_all_jobs, get_job_by_id, add_job, cleanup_old_jobs, create_user, get_user_by_email, save_job, unsave_job, get_saved_jobs_for_user, add_alert, remove_alert, get_user_alerts, create_password_reset_token, verify_reset_token, update_user_password
from auth import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from datetime import timedelta, datetime
from pydantic import BaseModel
import logging
import uuid
import secrets
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor
import uuid
from worker import celery_app

# ... 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://ai-job-aggregator-thzt.vercel.app"
    ],
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
def get_jobs(background_tasks: BackgroundTasks, q: str = None, filter_type: str = "All", location: str = None, sort_by: str = 'newest', date_posted_filter: str = 'any'):
    # Try fetching from DB cache first
    jobs = get_all_jobs(search_query=q, filter_type=filter_type, location_filter=location, sort_by=sort_by, date_posted_filter=date_posted_filter)
    
    # Live Fallback: If <15 jobs found, trigger async scrape to populate DB and return what we have
    if len(jobs) < 15 and q and location:
        logger.info(f"Only {len(jobs)} jobs found for {q} in {location}. Dispatching instant background scrape to fetch more...")
        
        def run_live_scrape(search_term, search_loc):
            try:
                from job_fetcher import fetch_jobs_from_web
                new_jobs = fetch_jobs_from_web(search_term=search_term, location=search_loc, results_wanted=50)
                if new_jobs:
                    for job in new_jobs:
                        try:
                            add_job(job)
                        except Exception:
                            pass
                    logger.info(f"Background scrape complete: Added jobs for {search_term} in {search_loc}")
            except Exception as e:
                logger.error(f"Background live fetch failed: {e}")
                
        background_tasks.add_task(run_live_scrape, q, location)
        
    return jobs

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

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


# --- PROTECTED ROUTES & DEPENDENCIES ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

@app.get("/api/user/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    # Remove sensitive info
    return {
        "email": current_user['email'], 
        "full_name": current_user['full_name'],
        "id": current_user['id']
    }

@app.post("/api/save_job/{job_id}")
def api_save_job(job_id: int, current_user: dict = Depends(get_current_user)):
    success = save_job(current_user['id'], job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not save job or already saved")
    return {"message": "Job saved successfully"}

@app.delete("/api/unsave_job/{job_id}")
def api_unsave_job(job_id: int, current_user: dict = Depends(get_current_user)):
    success = unsave_job(current_user['id'], job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not unsave job")
    return {"message": "Job removed from saved list"}

@app.get("/api/user/saved_jobs")
def api_get_saved_jobs(current_user: dict = Depends(get_current_user)):
    jobs = get_saved_jobs_for_user(current_user['id'])
    return jobs

class AlertCreateRequest(BaseModel):
    keyword: str
    location: str = ""

@app.get("/api/alerts")
def api_get_alerts(current_user: dict = Depends(get_current_user)):
    return get_user_alerts(current_user['id'])

@app.post("/api/alerts")
def api_create_alert(alert: AlertCreateRequest, current_user: dict = Depends(get_current_user)):
    success = add_alert(current_user['id'], alert.keyword, alert.location)
    if not success:
        raise HTTPException(status_code=400, detail="Could not create alert")
    return {"message": "Alert created successfully"}

@app.delete("/api/alerts/{alert_id}")
def api_delete_alert(alert_id: int, current_user: dict = Depends(get_current_user)):
    success = remove_alert(alert_id, current_user['id'])
    if not success:
        raise HTTPException(status_code=400, detail="Could not delete alert")
    return {"message": "Alert removed"}

from database import get_db_connection, get_cursor, release_connection

@app.get("/api/system/status")
def api_get_system_status():
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        c.execute("SELECT id FROM jobs ORDER BY id DESC LIMIT 1")
        latest = c.fetchone()
        
        # If no jobs, just return timestamp
        if not latest:
            return {"last_updated": datetime.utcnow().isoformat() + "Z", "jobs_count": 0}
            
        c.execute("SELECT COUNT(*) as count FROM jobs")
        count = c.fetchone()['count']
        
        # We don't have a created_at ingested column for jobs, but `scheduler.py` runs every 5 mins.
        # So we can just return a simulated "last checked recently" timestamp if we have jobs.
        return {"last_updated": datetime.utcnow().isoformat() + "Z", "jobs_count": count}
    except Exception as e:
        return {"last_updated": None, "jobs_count": 0}
    finally:
        release_connection(conn)

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

from emailer import send_password_reset_email

@app.post("/api/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    user = get_user_by_email(req.email)
    if not user:
        # Don't leak whether email exists
        return {"message": "If that email exists, a reset link has been sent."}
        
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    
    if create_password_reset_token(user['id'], token, expires_at):
        reset_link = f"http://localhost:5173/reset-password/{token}"
        send_password_reset_email(user['email'], user['full_name'], reset_link)
        
    return {"message": "If that email exists, a reset link has been sent."}

@app.post("/api/reset-password")
def reset_password(req: ResetPasswordRequest):
    user_id = verify_reset_token(req.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    try:
        hashed_password = get_password_hash(req.new_password)
        if update_user_password(user_id, hashed_password, req.token):
            return {"message": "Password updated successfully"}
        raise HTTPException(status_code=500, detail="Database error updating password")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

from worker import scrape_task

# ... 

# Scrapers have been moved to scheduler.py running as a background cache process.
# This prevents the server from getting IP-banned under heavy load.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
# Server Reload Trigger: Background Caching Enabled
