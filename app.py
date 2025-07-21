import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
from urllib.parse import urlparse, urlencode
import re
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# This function checks if the app is running in a containerized cloud environment
def is_running_in_cloud():
    """
    Returns True if the app is running in a cloud environment (like Render or Streamlit Cloud),
    False otherwise. It checks for a common environment variable.
    """
    return "PORT" in os.environ or "STREAMLIT_SERVER_PORT" in os.environ


def scrape_linkedin(role, location, experience_levels):
    """
    Scrapes job listings from LinkedIn for a given role, location, and filters.
    """
    chrome_options = Options()

    # --- Selenium Setup for Cloud Environment ---
    if is_running_in_cloud():
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.binary_location = "/usr/bin/chromium"

    driver = None
    try:
        # --- Use Selenium Manager ---
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # --- Build LinkedIn URL with Filters ---
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = {"keywords": role, "location": location}

        if experience_levels:
            params["f_E"] = ",".join(experience_levels)

        search_url = base_url + urlencode(params)
        driver.get(search_url)

        # --- Wait for job listings to load ---
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "base-card")))

        # --- Scrolling to load all jobs ---
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(5):  # Increased scroll attempts for longer pages
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Shorter sleep, but still necessary for dynamic loading
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # --- Scraping with BeautifulSoup ---
        soup = BeautifulSoup(driver.page_source, "html.parser")

        job_listings = soup.find_all("div", class_="base-card")

        if not job_listings:
            st.sidebar.warning(f"No listings found in '{location}'.")
            return pd.DataFrame()

        jobs_data = []
        for job in job_listings:
            title_tag = job.find("h3", class_="base-search-card__title")
            company_tag = job.find("h4", class_="base-search-card__subtitle")
            date_tag = job.find("time", class_="job-search-card__listdate")
            link_tag = job.find("a", class_="base-card__full-link")

            title = title_tag.text.strip() if title_tag else "N/A"
            company = company_tag.text.strip() if company_tag else "N/A"
            post_date = date_tag.text.strip() if date_tag else "N/A"
            link = link_tag["href"] if link_tag else "N/A"

            if link and link != "N/A":
                clean_link = link.split("?")[0]
                if not clean_link.endswith("/"):
                    clean_link += "/"
                parsed_url = urlparse(clean_link)
                link = f"https://www.linkedin.com{parsed_url.path}"

            jobs_data.append(
                {
                    "Job Title": title,
                    "Company": company,
                    "Post Date": post_date,
                    "Link": link,
                    "Searched Location": location,
                }
            )

        return pd.DataFrame(jobs_data)

    except Exception as e:
        st.sidebar.error(f"Error scraping {location}: {e}")
        return pd.DataFrame()
    finally:
        if driver:
            driver.quit()


def convert_post_date_to_days(post_date_str):
    """Converts 'X days/weeks/months ago' string to a number of days."""
    if not isinstance(post_date_str, str):
        return 999

    post_date_str = post_date_str.lower()

    if "now" in post_date_str or "minute" in post_date_str or "hour" in post_date_str:
        return 0

    try:
        num = int(re.search(r"\d+", post_date_str).group())
        if "day" in post_date_str:
            return num
        elif "week" in post_date_str:
            return num * 7
        elif "month" in post_date_str:
            return num * 30
        else:
            return 999
    except (AttributeError, ValueError):
        return 999


# --- Streamlit App UI ---
st.set_page_config(page_title="Easy Hunt | LinkedIn Job Scraper", layout="wide")

# --- UI Enhancements ---
st.markdown(
    """
    <style>
    h1 {
        text-align: center;
        color: #1E90FF;
    }
    .spacer {
        margin-top: 50px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 12px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    .stMultiSelect, .stTextInput {
        border-radius: 8px;
    }
    div[data-testid="stTextInput"], div[data-testid="stMultiSelect"] {
        margin-bottom: 15px;
    }
    th {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Easy Hunt Bot 🤖")

st.info(
    """
    **Welcome to the Easy Hunt Bot!**
    This tool helps you find relevant job listings from LinkedIn based on your criteria.
    - Enter a job role and comma-separated locations.
    - Apply filters like experience level for more accurate results.
    - The app will scrape the data, clean it, and display it in an interactive table.
    """
)

# --- Session State Initialization ---
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None
if "jobs_df" not in st.session_state:
    st.session_state.jobs_df = None
if "search_triggered" not in st.session_state:
    st.session_state.search_triggered = False

# --- Experience Level Mapping ---
EXPERIENCE_LEVELS = {
    "Internship": "1",
    "Entry level": "2",
    "Associate": "3",
    "Mid-Senior level": "4",
    "Director": "5",
    "Executive": "6",
}

# --- Sidebar for User Input ---
with st.sidebar:
    st.header("🔍 Search Filters")
    with st.form("job_search_form"):
        role = st.text_input("Enter Job Role", "Software Developer")
        locations_input = st.text_input(
            "Enter Locations (comma-separated)", "Pune, Maharashtra, India"
        )
        exp_level_options = st.multiselect(
            "Experience Level",
            options=list(EXPERIENCE_LEVELS.keys()),
            default=st.session_state.get("exp_level_options", []),
        )
        submitted = st.form_submit_button("Search Jobs")

    if submitted:
        if not role or not locations_input:
            st.error("Please provide a job role and at least one location.")
        else:
            st.session_state.search_triggered = True
            st.session_state.exp_level_options = exp_level_options

            experience_codes = [EXPERIENCE_LEVELS[level] for level in exp_level_options]
            locations = [loc.strip() for loc in locations_input.split(",")]
            all_jobs_list = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, loc in enumerate(locations):
                if loc:
                    with st.spinner(f"Searching for '{role}' in {loc}..."):
                        scraped_data = scrape_linkedin(role, loc, experience_codes)
                        if not scraped_data.empty:
                            all_jobs_list.append(scraped_data)
                    progress_bar.progress((i + 1) / len(locations))

            status_text.success("Search Complete!")

            if all_jobs_list:
                st.session_state.jobs_df = pd.concat(all_jobs_list, ignore_index=True)
                st.session_state.cleaned_df = st.session_state.jobs_df.drop_duplicates(
                    subset=["Job Title", "Company", "Link"]
                )
                st.session_state.cleaned_df["Days Ago"] = st.session_state.cleaned_df[
                    "Post Date"
                ].apply(convert_post_date_to_days)
                st.session_state.cleaned_df = st.session_state.cleaned_df.sort_values(
                    by="Days Ago"
                ).drop(columns=["Days Ago"])
            else:
                st.session_state.jobs_df = None
                st.session_state.cleaned_df = None

# --- Main Content Area ---
if st.session_state.search_triggered:
    if (
        st.session_state.cleaned_df is not None
        and not st.session_state.cleaned_df.empty
    ):
        st.success(
            f"Found {len(st.session_state.jobs_df)} total listings. After cleaning, {len(st.session_state.cleaned_df)} unique jobs were found."
        )

        # --- Interactive DataFrame ---
        st.subheader("Interactive Job Listings")
        df_display = st.session_state.cleaned_df.copy()
        df_display["Link"] = df_display["Link"].apply(
            lambda url: (
                f'<a href="{url}" target="_blank">Apply</a>' if url != "N/A" else "N/A"
            )
        )
        st.markdown(
            df_display.to_html(escape=False, index=False), unsafe_allow_html=True
        )

        # --- Download Button ---
        st.subheader("Download Data")
        csv_role = role.replace(" ", "_")
        csv = st.session_state.cleaned_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"{csv_role}_jobs.csv",
            mime="text/csv",
        )

        # --- Visualizations ---
        st.subheader("Job Market Insights")
        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Job Frequency by Company")
            company_counts = (
                st.session_state.cleaned_df["Company"].value_counts().head(10)
            )
            st.bar_chart(company_counts)

        with col2:
            st.write("#### Job Distribution by Location")
            location_counts = st.session_state.cleaned_df[
                "Searched Location"
            ].value_counts()
            st.line_chart(location_counts)

    else:
        st.error(
            "No job listings found with the selected criteria. Please try again or broaden your search."
        )

    if st.button("Clear Results"):
        st.session_state.search_triggered = False
        st.session_state.cleaned_df = None
        st.session_state.jobs_df = None
        st.rerun()

else:
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px;">
            <h3>Ready to start your job search?</h3>
            <p>Use the filters on the left to begin.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown(
    "<p style='text-align: center;'>Easy Hunt Bot — Your smart assistant for automated job discovery.</p>",
    unsafe_allow_html=True,
)
