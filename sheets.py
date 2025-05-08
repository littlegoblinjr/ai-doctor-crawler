import asyncio
import json
import time
from typing import Dict, List
import gspread
from google.oauth2.service_account import Credentials
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from concurrent.futures import ThreadPoolExecutor

import lmstudio as lms
# Configuration
SHEET_ID = "16wgmEU6DmE8FT-Zun17Nm2ZoFOzl5Dlc-E992C0K6CM"
WORKSHEET_NAME = "Sheet1"
CREDS_FILE = "credentials.json"
OUTPUT_JSON = "scraped_data.json"
SLEEP_BETWEEN_REQUESTS = 5  # seconds to wait between scrapes to avoid rate limits
model = lms.llm("gemma-2-2b-it")

# Specialties mappings (unchanged from your code)
practo_mapping = {
    "ophthalmology": "ophthalmologist",
    "dermatology": "dermatologist",
    "cardiology": "cardiologist",
    "psychiatry": "psychiatrist",
    "gastroenterology": "gastroenterologist",
    "ent": "ear-nose-throat-ent-specialist",
    "obstetrics & gynaecology": "gynecologist-obstetrician",
    "neurology": "neurologist",
    "urology": "urologist",
    "psychology": "psychologist",
    "dentist": "dentist",
}

doctor_specialties = {
    "general-physician-internal-medicine", "dermatology", "obstetrics-and-gynaecology", "orthopaedics", "ent", "neurology",
    "cardiology", "urology", "gastroenterology-gi-medicine", "psychiatry", "paediatrics", "pulmonology-respiratory-medicine",
    "endocrinology", "nephrology", "neurosurgery", "rheumatology", "ophthalmology", "surgical-gastroenterology",
    "infectious-disease", "general-and-laparoscopic-surgeon", "psychology", "medical-oncology", "diabetology", "dentist"
}

fitness_mapping = {
    "fitness-and-nutrition", "strength-conditioning", "yoga", "zumba", "calisthenics",
    "strength-yoga", "injury-rehab", "personal-training-nutrition", "pre-post-natal-training",
    "diabetes-lifestyle-management"
}




class DataScraper:
    def __init__(self):
        # Initialize Google Sheets client
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
        self.client = gspread.authorize(creds)
        self.workbook = self.client.open_by_key(SHEET_ID)
        self.sheet = self.workbook.worksheet(WORKSHEET_NAME)
        
        # Initialize scraping tools
        self.browser_config = BrowserConfig(headless=True)
        self.run_config = CrawlerRunConfig()

    def build_practo_url(self, specialist: str, city: str = "Pune") -> str:
        """Generate Practo URL for a given specialist."""
        title = practo_mapping.get(specialist.lower())
        if not title:
            return None
        return f"https://www.practo.com/{city}/{title}"

    async def scrape_specialist(self, specialist: str) -> Dict:
        """Scrape data for a single specialist from all sources."""
        scraped_data = {"specialist": specialist, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            if specialist.lower() in doctor_specialties:
                # Scrape Apollo
                apollo_url = f"https://www.apollo247.com/specialties/{specialist}"
                try:
                    apollo_result = await crawler.arun(url=apollo_url, config=self.run_config)
                    scraped_data["apollo"] = apollo_result.markdown
                except Exception as e:
                    scraped_data["apollo_error"] = str(e)

                # Scrape Practo
                practo_url = self.build_practo_url(specialist)
                if practo_url:
                    try:
                        practo_result = await crawler.arun(url=practo_url, config=self.run_config)
                        scraped_data["practo"] = practo_result.markdown
                    except Exception as e:
                        scraped_data["practo_error"] = str(e)
                else:
                    scraped_data["practo"] = "No Practo mapping available."

            elif specialist.lower() in fitness_mapping:
                # Scrape Fittr
                fittr_url = f"https://www.fittr.com/coaching/{specialist}"
                try:
                    fittr_result = await crawler.arun(url=fittr_url, config=self.run_config)
                    scraped_data["fittr"] = fittr_result.markdown
                except Exception as e:
                    scraped_data["fittr_error"] = str(e)
            else:
                scraped_data["error"] = "Unknown specialist category"

        return scraped_data
    def chunk_text(self, text_list, chunk_size=5000):
        return [text_list[i:i + chunk_size] for i in range(0, len(text_list), chunk_size)]
    
    
    async def extract_doctor_info(self, text):
        response = None
        doctors = []
        if not text:
            print("Warning: Empty input text")
            return doctors

        chunks = self.chunk_text(text, 3000)
        print(f"Processing {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks, 1):
           
            try:
                print(f"Processing chunk {i}/{len(chunks)} (size: {len(chunk)} chars)")
                
                # Clean the chunk text
                
                
                response = model.respond(f"""
You are an intelligent extraction engine. From the following unstructured text, extract all relevant doctor or coach details, If you see fitness trainer information you need to consider that too, you cant skip that and its not necessary there has to be a Dr in front of the name, So please make sure you dont skip any fitness trainer information .

📝 Instructions:
Return ONLY a valid **JSON array** of objects. Each object must include **all** of these exact fields:

- name (string)
- specialty (string)
- location (string)
- clinic (string)
- fees (string)
- availability (string)
- profile_link (string)
- site (string)


If a field is not present in the text, leave its value as an empty string dont just write null keep it in quotes and it will stay valid and if you dont find any doctor just return nothing and move on please dont miss profile link if you find doctor details there will be profile link, And please do make sure that it stays in VALID JSON FORMAT"".

📦 Example of valid output:
[
    {{
        "name": "Dr. John Smith",
        "specialty": "ENT Specialist",
        "location": "Bengaluru",
        "clinic": "ABC Clinic",
        "fees": "₹500",
        "availability": "Available in 10 mins",
        "profile_link": "https://example.com/doctor1",
        "site": "Apollo"
                                         
        
    }},
    {{
        "name": "Jane Doe",
        "specialty": "Fitness Coach",
        "location": "Mumbai",
        "clinic": "FitZone",
        "fees": "₹800",
        "availability": "Available",
        "profile_link": "https://example.com/coach1",
        "site": "Fittr"
        
    }}
]

📄 Text to extract from:
\"\"\"
{chunk}
\"\"\"
""")

            
                
                

                data = None
                try:
                    parser = JsonOutputParser()
                    data = parser.parse(response.content)
                except json.JSONDecodeError:
                    print("Parsing Error")
                    
                
                # Add timeout and rate limiting
                
                
                
                if isinstance(data, dict):
                    doctors.append(data)
                elif isinstance(data, list):
                    doctors.extend(data)

                print(doctors)
                print(f"Chunk {i} processed successfully. Found {len(data) if data else 0} doctors")
                if i < len(chunks):
                    print(f"Waiting 3 mins before next chunk...")
                    await asyncio.sleep(1)  # Rate limiting
                    
                
                
            except asyncio.TimeoutError:
                print(f"Timeout processing chunk {i}")
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                continue
            
        print(f"Total doctors extracted: {len(doctors)}")
        return doctors
        
    async def scrape_all(self):
        """Scrape data for all specialists."""
        all_data = []
        
        # Combine all categories to scrape
        all_specialists = list(doctor_specialties.union(fitness_mapping))
        
        for specialist in all_specialists:
            print(f"Scraping data for: {specialist}")
            data = await self.scrape_specialist(specialist)
            all_data.append(data)
            
            # Save progress after each scrape
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=4)
            
            # Respect rate limits
            await asyncio.sleep(SLEEP_BETWEEN_REQUESTS)
        
        return all_data
    
    async def handle_specialist_recommendation(self):
        doctors = []
        try:
            
            
            with open(OUTPUT_JSON, "r", encoding = "utf-8") as f:
                scraped_data = json.load(f)

            combined_text = []
            for item in scraped_data:
                if 'apollo' in item:
                    combined_text.append(item['apollo'])
                if 'practo' in item:
                    combined_text.append(item['practo'])
                if 'fittr' in item:
                    combined_text.append(item['fittr'])

            processed_text = "\n".join(combined_text)
            

            return await self.extract_doctor_info(processed_text)

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return []  # Always return a list


        

    

    def update_sheets(self, data: List[Dict]):
        """Update Google Sheets with scraped data."""
        # Prepare data for Google Sheets (modify based on your sheet structure)
        rows = []

        headers = [
            "Specialist", 
            "Doctor Name",
            "Clinic",
            "Location",
            "Fees",
            "Availability",
            "Profile Link",
            "Site Name",
            "Timestamp"
        ]
        if data:
            for doctor in data:
                rows.append([
                    doctor.get("specialty", ""),
                    doctor.get("name", ""),
                    doctor.get("clinic", ""),
                    doctor.get("location", ""),
                    doctor.get("fees", ""),
                    doctor.get("availability", ""),
                    doctor.get("profile_link", ""),
                    doctor.get("site", ""),
                   
                    time.strftime("%Y-%m-%d %H:%M:%S")
                ])
        
        # Clear existing data and update with new data
        try:
        # Clear and update with modern API
            self.sheet.clear()
            self.sheet.update(values=[headers], range_name="A1")
            if rows:
                self.sheet.update(values=rows, range_name="A2")
            print(f"Successfully updated {len(rows)} records")
        except Exception as e:
            print(f"Failed to update Google Sheets: {str(e)}")

    async def run(self):
        """Main execution method."""
        print("Starting scraping process...")
        scraped_data = await self.scrape_all()
        specialist_update = await self.handle_specialist_recommendation()
        print("Scraping complete. Updating Google Sheets...")
        self.update_sheets(specialist_update)
        print("Update complete!")

# Schedule the scraper to run daily
async def scheduled_scraper():
    while True:
        scraper = DataScraper()
        await scraper.run()
        
        # Wait 24 hours before running again
        await asyncio.sleep(24 * 60 * 60)

if __name__ == "__main__":
    # Run once immediately
    asyncio.run(DataScraper().run())
    
    # Uncomment to run on a schedule:
    # asyncio.run(scheduled_scraper())