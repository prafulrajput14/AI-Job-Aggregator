from database import get_all_jobs, add_job
import logging

logging.basicConfig(level=logging.INFO)

def test_expansion():
    print("🧪 Testing Acronym Expansion in DB Retrieval...")
    
    # 1. Ensure we have a test job
    job = {
        "title": "Software Engineer",
        "company": "Test Co",
        "location": "Delhi, India",
        "url": "http://test.com/sde1",
        "site": "indeed"
    }
    try:
        add_job(job)
        print("✅ Added test job: 'Software Engineer'")
    except:
        pass # Might already exist

    # 2. Search for "sde"
    print("🔍 Searching DB for 'sde'...")
    results = get_all_jobs(search_query="sde")
    
    found = False
    for job in results:
        if "Software Engineer" in job['title']:
            found = True
            print(f"✅ Found job: {job['title']} (matched via expansion!)")
            break
            
    if not found:
        print(f"❌ Failed! Found {len(results)} jobs, but none matched 'Software Engineer'.")
        for j in results:
            print(f" - {j['title']}")

if __name__ == "__main__":
    test_expansion()
