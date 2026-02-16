import schedule
import time
import random
from internshala_scraper import InternshalaScraper
from ai_engine import AIEngine
from database import add_job, init_db

def job_pipeline():
    print("--- Starting Scheduled Job Update ---")
    scraper = InternshalaScraper()
    ai = AIEngine()
    
    # 1. Scrape Real Jobs from Internshala
    # We randomize keywords to get variety
    keywords = random.choice(["python", "react", "java", "data science", "web development"])
    jobs = scraper.fetch_jobs(keywords)
    
    if not jobs:
        print("No jobs found this run.")
        return

    # 2. Process and Save
    for job in jobs:
        # AI Enrichment
        job['skills'] = ", ".join(ai.extract_skills(job.get('title', '') + " " + job.get('description', '')))
        job_type = ai.classify_job_type(job['title'], job.get('description', ''))
        job['is_internship'] = 1  # Internshala is mostly internships
        
        # Save to DB
        add_job(job)
    
    print(f"--- Update Complete. Added/Checked {len(jobs)} jobs. ---")

def start_scheduler():
    init_db()
    
    # Schedule every 10 seconds for DEMO purposes (normally would be daily)
    schedule.every(10).seconds.do(job_pipeline)
    
    print("Scheduler running... (Check terminal for updates)")
    
    # Run once immediately
    job_pipeline()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_scheduler()
