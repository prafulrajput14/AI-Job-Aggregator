import re

class AIEngine:
    def __init__(self):
        self.skills_db = [
            "Python", "Java", "C++", "React", "Node.js", "SQL", "NoSQL", 
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Machine Learning", 
            "Deep Learning", "Data Analysis", "Communication", "Teamwork"
        ]
    
    def extract_skills(self, text):
        """
        Extracts known skills from the job description using regex.
        """
        found_skills = []
        if not text:
            return found_skills
            
        text_lower = text.lower()
        for skill in self.skills_db:
            # \b ensures whole word matches (e.g., avoid matching "Java" in "Javascript" if we only wanted Java)
            # escape skill to handle special chars like C++
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        return list(set(found_skills))

    def classify_job_type(self, title, description):
        """
        Determines if a job is an Internship or Full-time text.
        """
        text = (title + " " + description).lower()
        
        intern_keywords = ["intern", "internship", "trainee", "student", "university"]
        
        for keyword in intern_keywords:
            if keyword in text:
                return "Internship"
        
        return "Full-time"

    def is_duplicate(self, new_job_url, existing_urls):
        """
        Checks if the job URL already exists in our database.
        """
        return new_job_url in existing_urls

if __name__ == "__main__":
    ai = AIEngine()
    desc = "We are looking for a Python Intern who knows SQL and React."
    print(f"Skills: {ai.extract_skills(desc)}")
    print(f"Type: {ai.classify_job_type('Software Developer', desc)}")
