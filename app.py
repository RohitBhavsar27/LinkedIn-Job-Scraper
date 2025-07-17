import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from urllib.parse import urlparse, urlencode
import re
from bs4 import BeautifulSoup

# This function checks if the app is running on Streamlit Cloud
def is_running_on_streamlit_cloud():
    """Returns True if the app is running on Streamlit Cloud, False otherwise."""
    return "STREAMLIT_SERVER_PORT" in os.environ

def scrape_linkedin(role, location, experience_levels):
    """
    Scrapes job listings from LinkedIn for a given role, location, and filters.
    """
    st.info(f"Setting up browser to search for '{role}' in {location}...")
    
    chrome_options = Options()
    
    # --- Selenium Setup for Streamlit Cloud ---
    # These options and the binary location are crucial for running on Streamlit Cloud
    if is_running_on_streamlit_cloud():
        st.write("Running on Streamlit Cloud, setting up headless Chrome...")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # The binary location for Chromium installed via apt-get in packages.txt
        chrome_options.binary_location = "/usr/bin/chromium"
    
    driver = None
    try:
        # --- Use Selenium Manager (built-in from Selenium 4.6.0+) ---
        # This will automatically detect the browser version and download the correct driver.
        # No need for webdriver-manager anymore.
        st.write("Initializing WebDriver with Selenium Manager...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # --- Build LinkedIn URL with Filters ---
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = {'keywords': role, 'location': location}
        
        if experience_levels:
            params['f_E'] = ",".join(experience_levels)

        search_url = base_url + urlencode(params)
        st.write(f"Navigating to: {search_url}")
        driver.get(search_url)

        time.sleep(10)

        # --- Scrolling to load all jobs ---
        st.write("Scrolling to load more job listings...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # --- Scraping with BeautifulSoup ---
        st.write("Parsing job data...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        job_listings = soup.find_all('div', class_='base-card')
        
        if not job_listings:
            st.warning(f"No job listings found for the specified criteria in '{location}'.")
            return pd.DataFrame()

        jobs_data = []
        for job in job_listings:
            title_tag = job.find('h3', class_='base-search-card__title')
            company_tag = job.find('h4', class_='base-search-card__subtitle')
            date_tag = job.find('time', class_='job-search-card__listdate')
            link_tag = job.find('a', class_='base-card__full-link')

            title = title_tag.text.strip() if title_tag else 'N/A'
            company = company_tag.text.strip() if company_tag else 'N/A'
            post_date = date_tag.text.strip() if date_tag else 'N/A'
            link = link_tag['href'] if link_tag else 'N/A'

            if link and link != 'N/A':
                clean_link = link.split('?')[0]
                if not clean_link.endswith('/'):
                    clean_link += '/'
                parsed_url = urlparse(clean_link)
                link = f"https://www.linkedin.com{parsed_url.path}"

            jobs_data.append({
                'Job Title': title,
                'Company': company,
                'Post Date': post_date,
                'Link': link,
                'Searched Location': location
            })
        
        return pd.DataFrame(jobs_data)

    except Exception as e:
        st.error(f"An error occurred while scraping {location}: {e}")
        return pd.DataFrame()
    finally:
        if driver:
            st.write("Closing WebDriver.")
            driver.quit()

def convert_post_date_to_days(post_date_str):
    """Converts 'X days/weeks/months ago' string to a number of days."""
    if not isinstance(post_date_str, str):
        return 999

    post_date_str = post_date_str.lower()
    
    if 'now' in post_date_str or 'minute' in post_date_str or 'hour' in post_date_str:
        return 0
    
    try:
        num = int(re.search(r'\d+', post_date_str).group())
        if 'day' in post_date_str:
            return num
        elif 'week' in post_date_str:
            return num * 7
        elif 'month' in post_date_str:
            return num * 30
        else:
            return 999
    except (AttributeError, ValueError):
        return 999

# --- Streamlit App UI ---
st.set_page_config(page_title="LinkedIn Job Scraper", layout="wide")
st.title("LinkedIn Job Scraper Bot 🤖")

st.markdown("""
This application scrapes job listings from LinkedIn with advanced filters. 
You can provide a list of locations, and the app will search them in order.
**Note:** This is for educational purposes. Please be mindful of LinkedIn's terms of service.
""")

if 'cleaned_df' not in st.session_state:
    st.session_state.cleaned_df = None
if 'jobs_df' not in st.session_state:
    st.session_state.jobs_df = None

EXPERIENCE_LEVELS = {
    "Internship": "1",
    "Entry level": "2",
    "Associate": "3",
    "Mid-Senior level": "4",
    "Director": "5",
    "Executive": "6"
}

with st.form("job_search_form"):
    role = st.text_input("Enter Job Role", "Data Scientist")
    locations_input = st.text_input("Enter Locations (comma-separated)", "Pune, Maharashtra, India")
    
    st.write("### Filters")
    
    exp_level_options = st.multiselect(
        "Experience Level",
        options=list(EXPERIENCE_LEVELS.keys()),
    )

    submitted = st.form_submit_button("Scrape Jobs")

if submitted:
    if not role or not locations_input:
        st.error("Please provide a job role and at least one location.")
    else:
        experience_codes = [EXPERIENCE_LEVELS[level] for level in exp_level_options]
        
        locations = [loc.strip() for loc in locations_input.split(',')]
        all_jobs_list = []
        
        with st.spinner(f"Scraping LinkedIn for '{role}' positions..."):
            for loc in locations:
                if loc:
                    scraped_data = scrape_linkedin(role, loc, experience_codes)
                    if not scraped_data.empty:
                        all_jobs_list.append(scraped_data)
        
        if all_jobs_list:
            st.session_state.jobs_df = pd.concat(all_jobs_list, ignore_index=True)
            st.session_state.cleaned_df = st.session_state.jobs_df.drop_duplicates(subset=['Job Title', 'Company', 'Link'])
            
            st.session_state.cleaned_df['Days Ago'] = st.session_state.cleaned_df['Post Date'].apply(convert_post_date_to_days)
            st.session_state.cleaned_df = st.session_state.cleaned_df.sort_values(by='Days Ago').drop(columns=['Days Ago'])
            
        else:
            st.session_state.jobs_df = None
            st.session_state.cleaned_df = None

if st.session_state.cleaned_df is not None:
    if not st.session_state.cleaned_df.empty:
        st.success(f"Scraping complete! Found {len(st.session_state.jobs_df)} total listings before cleaning.")
        st.info(f"After removing duplicates and sorting, {len(st.session_state.cleaned_df)} unique jobs were found.")
        
        st.subheader("Sorted Job Listings")
        st.dataframe(st.session_state.cleaned_df)

        st.subheader("Download Data")
        df_for_csv = st.session_state.cleaned_df.copy()
        df_for_csv['Link'] = df_for_csv['Link'].apply(
            lambda url: f'=HYPERLINK("{url}", "Apply Here")' if url != 'N/A' else 'N/A'
        )
        
        csv_role = role.replace(" ", "_")
        csv = df_for_csv.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'{csv_role}_jobs.csv',
            mime='text/csv',
        )

        st.subheader("Job Frequency by Company")
        company_counts = st.session_state.cleaned_df['Company'].value_counts().head(20)
        st.bar_chart(company_counts)

    else:
        st.error("Failed to scrape any job listings with the selected criteria. Please try again or broaden your search.")

st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, Selenium, and BeautifulSoup.")
