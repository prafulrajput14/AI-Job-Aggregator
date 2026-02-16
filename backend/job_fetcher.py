import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_jobs_from_web(search_term="software engineer", location="India", results_wanted=10, is_remote=False, job_type="fulltime"):
    """
    Fetches jobs from various sources.
    EMERGENCY MODE: Returns mock data to ensure site works for resume/demo immediately.
    This bypasses any potential scraping blocks or connection hangs.
    """
    logger.info(f"🕵️ [MOCK] Fetching jobs for {search_term} in {location}...")
    
    # --- MOCK DATA FOR DEMO/RESUME STABILITY ---
    mock_titles = [
        f"Senior {search_term.title()} Developer",
        f"{search_term.title()} Engineer",
        f"Junior {search_term.title()}",
        f"Lead {search_term.title()}",
        f"{search_term.title()} Intern",
        f"Principal {search_term.title()} Architect",
        f"{search_term.title()} Consultant",
        f"Remote {search_term.title()} Role"
    ]
    
    mock_companies = ["Tech Giants Inc.", "Startup Hub", "Creative Solutions", "Global Systems", "Future Tech", "InnovateX", "DataCorp"]
    mock_sites = ["LinkedIn", "Glassdoor", "Indeed", "Naukri", "Instahyre"]
    
    jobs = []
    # Ensure we return at least 'results_wanted' jobs, minimum 15 for good UX
    for _ in range(max(results_wanted, 15)):
        base_title = random.choice(mock_titles)
        base_company = random.choice(mock_companies)
        base_site = random.choice(mock_sites)
        
        # Randomize location slightly if generic
        loc = location.title() if location else "Remote"
        if is_remote and random.random() > 0.3:
            loc = "Remote"
            
        # Dynamic Link Generation for Realism
        # Search for the ROLE + LOCATION only (Removing company to ensure results found)
        query = f"{base_title}".replace(" ", "%20")
        encoded_loc = location.replace(" ", "%20")
        
        jobs.append({
            "title": base_title,
            "company": base_company,
            "location": loc,
            # Point to broadly relevant search results
            "url": f"https://www.linkedin.com/jobs/search?keywords={query}&location={encoded_loc}", 
            "site": base_site,
            "date_posted": "Just now",
            "is_remote": is_remote or (loc == "Remote"),
            "job_type": job_type or "Full-time",
            "description": f"Exciting opportunity for a {search_term} developer... Join our team at {base_company}!",
            "salary": f"₹{random.randint(6, 30)},00,000",
            "currency": "INR"
        })
    
    logger.info(f"✅ [MOCK] Returning {len(jobs)} guaranteed results.")
    return jobs

if __name__ == "__main__":
    # Test fetch
    results = fetch_jobs_from_web("Python", "Delhi")
    print(f"Fetched {len(results)} jobs.")
    print(results[0])
