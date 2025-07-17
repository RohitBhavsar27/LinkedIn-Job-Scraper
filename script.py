
import time
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import argparse

def scrape_linkedin_jobs(job_title, location):
    # Configure Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    # Initialize Chrome WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    # Construct the LinkedIn job search URL
    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
    
    # Open the URL
    driver.get(linkedin_url)
    
    # Allow time for the page to load
    time.sleep(5)
    
    # Scroll down to load more jobs
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Find all job listings
    jobs = soup.find_all("div", class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card")
    
    job_data = []
    
    for job in jobs:
        # Extract job details
        title = job.find("h3", class_="base-search-card__title").text.strip()
        company = job.find("h4", class_="base-search-card__subtitle").text.strip()
        location = job.find("span", class_="job-search-card__location").text.strip()
        link = job.find("a", class_="base-card__full-link")["href"]
        
        job_data.append({
            "Title": title,
            "Company": company,
            "Location": location,
            "Link": link
        })
    
    # Close the WebDriver
    driver.quit()
    
    return job_data

if __name__ == "__main__":
    job_title = input("Enter the job title: ")
    location = input("Enter the location: ")
    
    # Scrape job data
    scraped_data = scrape_linkedin_jobs(job_title, location)
    
    # Create a DataFrame and save to CSV
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        df.to_csv("linkedin_jobs.csv", index=False)
        print(f"Scraped {len(scraped_data)} jobs and saved to linkedin_jobs.csv")
    else:
        print("No jobs found.")
