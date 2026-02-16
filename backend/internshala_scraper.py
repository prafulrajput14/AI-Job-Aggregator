import requests
from bs4 import BeautifulSoup
import time
import random

class InternshalaScraper:
    def __init__(self):
        self.base_url = "https://internshala.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_jobs(self, keywords="python"):
        url = f"{self.base_url}/internships/keywords-{keywords}"
        try:
            print(f"Fetching: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Internshala job cards usually have ID starting with 'individual_internship_'
            rows = soup.find_all(id=lambda x: x and x.startswith('individual_internship_'))
            
            for row in rows:
                try:
                    title_elem = row.find('h3', class_='job-title') or row.find('h3', class_='internship_heading') or row.find('div', class_='heading_4_5')
                    company_elem = row.find('div', class_='company_name') or row.find('a', class_='link_display_like_text')
                    location_elem = row.find('a', class_='location_link') or row.find('div', id='location_names')
                    
                    # Extract URL
                    link_container = title_elem.find('a') if title_elem else None
                    if not link_container:
                         # fallback to finding any link in the card
                         link_container = row.find('a', class_='view_detail_button')
                    
                    job_url = self.base_url + link_container['href'] if link_container and link_container.get('href') else "N/A"
                    
                    title = title_elem.text.strip() if title_elem else "Unknown Role"
                    company = company_elem.text.strip() if company_elem else "Unknown Company"
                    location = location_elem.text.strip() if location_elem else "Remote/India"
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": f"Real opportunity at {company}. Apply via link.",
                        "url": job_url,
                        "date_posted": "Recently"
                    })
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
                    
            return jobs
            
        except Exception as e:
            print(f"Error fetching Internshala: {e}")
            return []

if __name__ == "__main__":
    scraper = InternshalaScraper()
    jobs = scraper.fetch_jobs("python")
    print(f"Found {len(jobs)} jobs")
    for job in jobs[:3]:
        print(job)
