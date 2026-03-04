import logging
import random
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_jobs_from_web(search_term="software engineer", location="India", results_wanted=10, is_remote=False, job_type="fulltime"):
    """
    Fetches jobs from various sources.
    EMERGENCY MODE: Returns mock data to ensure site works for resume/demo immediately.
    This bypasses any potential scraping blocks or connection hangs.
    """
    logger.info(f"🕵️ [REAL] Scraping jobs for {search_term} in {location}...")
    
    try:
        from jobspy import scrape_jobs
        import pandas as pd
        
        # jobspy expects job type formatting
        jt = "fulltime"
        if "intern" in job_type.lower():
            jt = "internship"
        elif "contract" in job_type.lower():
            jt = "contract"

        # Determine sources based on what works best for India/Remote
        site_names = ["linkedin", "indeed", "glassdoor"]
        
        jobs_df = scrape_jobs(
            site_name=site_names,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            country_linkedin="in", # Defaulting to India as per previous logic
            is_remote=is_remote,
            job_type=jt
        )
        
        jobs = []
        if jobs_df.empty:
            logger.warning("⚠️ No jobs found by scraper.")
            return jobs
            
        # Convert NaN to None for JSON serialization and DB insertion
        jobs_df = jobs_df.where(pd.notnull(jobs_df), None)
        
        for index, row in jobs_df.iterrows():
            jobs.append({
                "title": str(row.get('title', 'Unknown Title')),
                "company": str(row.get('company', 'Unknown Company')),
                "location": str(row.get('location', location)),
                "url": str(row.get('job_url')) if pd.notna(row.get('job_url')) and str(row.get('job_url')).strip() else f"https://job-aggregator.local/{uuid.uuid4().hex}",
                "site": str(row.get('site', 'External')),
                "date_posted": str(row.get('date_posted', '')),
                "is_remote": row.get('is_remote', False) or is_remote,
                "job_type": str(row.get('job_type', job_type)),
                "description": str(row.get('description', '')),
                "salary": str(row.get('min_amount', '')) + (" - " + str(row.get('max_amount', '')) if row.get('max_amount') else ""),
                "currency": str(row.get('currency', ''))
            })
            
        logger.info(f"✅ [REAL] Successfully scraped {len(jobs)} jobs.")
        return jobs
        
    except Exception as e:
        logger.error(f"❌ [Scraper] Error during live scrape: {e}")
        return []

if __name__ == "__main__":
    # Test fetch
    results = fetch_jobs_from_web("Python", "Delhi")
    print(f"Fetched {len(results)} jobs.")
    print(results[0])
