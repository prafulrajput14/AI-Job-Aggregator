import json
import os
from database import init_db, add_job
from ai_engine import AIEngine

def seed():
    # Initialize DB
    init_db()
    
    # Initialize AI
    ai = AIEngine()
    
    # Load dummy data
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'jobs.json')
    try:
        with open(file_path, 'r') as f:
            jobs = json.load(f)
            
        for job in jobs:
            # Enrich with AI
            job['skills'] = ", ".join(ai.extract_skills(job.get('description', '')))
            
            job_type = ai.classify_job_type(job['title'], job.get('description', ''))
            job['is_internship'] = 1 if job_type == "Internship" else 0
            
            add_job(job)
            
        print("Database seeded and AI-enriched successfully!")
    except FileNotFoundError:
        print("Dummy data file not found.")

if __name__ == "__main__":
    seed()
