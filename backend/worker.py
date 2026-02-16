import os
import logging
from celery import Celery
from dotenv import load_dotenv
from job_fetcher import fetch_jobs_from_web
from database import add_job

# Load env vars
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Optional: Celery Config
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="scrape_task")
def scrape_task(search_term: str, location: str, is_remote: bool = False, job_type: str = "fulltime", results_wanted: int = 15):
    """
    Background Task: Fetch jobs and save to DB.
    """
    logger.info(f"🚀 [Celery] Starting scrape for: {search_term} in {location} (Limit: {results_wanted})")
    
    try:
        # Fetch jobs (Synchronous call to scraper, but running in worker process)
        jobs = fetch_jobs_from_web(search_term, location, is_remote=is_remote, job_type=job_type, results_wanted=results_wanted)
        
        count = 0
        for job in jobs:
            add_job(job)
            count += 1
            
        logger.info(f"✅ [Celery] Finished. Saved {count} jobs.")
        return {"status": "success", "jobs_found": count}
        
    except Exception as e:
        logger.error(f"❌ [Celery] Error: {e}")
        return {"status": "error", "error": str(e)}
