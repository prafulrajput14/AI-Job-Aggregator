import schedule
import time
import random
from internshala_scraper import InternshalaScraper
from ai_engine import AIEngine
from database import add_job, init_db, get_all_active_alerts, get_all_jobs
from emailer import send_job_alert_email
def job_pipeline():
    print("--- Starting Scheduled Job Caching ---")
    
    # 1. Define caching targets
    keywords = ["Software Engineer", "Data Scientist", "Frontend Developer", "Backend Developer", "Product Manager"]
    locations = ["Delhi", "Bangalore", "Mumbai", "Pune", "Remote"]
    
    word = random.choice(keywords)
    loc = random.choice(locations)
    
    print(f"🕵️ Caching background jobs for: {word} in {loc}...")
    
    # Use the robust job fetcher, requesting a decent batch size
    from job_fetcher import fetch_jobs_from_web
    try:
        jobs = fetch_jobs_from_web(search_term=word, location=loc, results_wanted=50)
        
        if not jobs:
            print("No jobs found this run. Maybe blocked? Waiting for next cycle.")
            return

        # 2. Process and Save
        success_count = 0
        from database import add_job
        for job in jobs:
            try:
                add_job(job)
                success_count += 1
            except Exception as e:
                print(f"DB Insert Error: {e}")
        
        print(f"--- Cache Update Complete. Added/Checked {success_count} real jobs. ---")
        
    except Exception as e:
         print(f"--- Cache Scraper Error: {e} ---")

def email_alert_pipeline():
    print("--- Starting Email Alert Dispatch ---")
    active_alerts = get_all_active_alerts()
    print(f"Found {len(active_alerts)} active alerts.")
    
    for alert in active_alerts:
        keyword = alert['keyword']
        location = alert['location']
        user_email = alert['email']
        user_name = alert['full_name']
        
        matched_jobs = get_all_jobs(search_query=keyword, location_filter=location, date_posted_filter='past_24h')
        
        if matched_jobs:
            print(f"Dispatching alert to {user_email} via SMTP - Found {len(matched_jobs)} related jobs.")
            send_job_alert_email(user_email, user_name, keyword, location, matched_jobs)
        else:
            print(f"No new jobs found today for {user_email}'s alert '{keyword}'.")

def start_scheduler():
    init_db()
    
    # Schedule every 5 minutes (Real scraping needs delays to avoid instant IP bans)
    schedule.every(5).minutes.do(job_pipeline)
    
    # Schedule emails every 24 hours
    schedule.every(24).hours.do(email_alert_pipeline)
    
    print("Background Cacher running... (Will ping job boards every 5 minutes, send emails daily)")
    
    # Run once immediately
    job_pipeline()
    email_alert_pipeline()
    
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    start_scheduler()
