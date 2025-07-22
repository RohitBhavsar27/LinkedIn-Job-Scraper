# Easy Hunt - LinkedIn Job Scraper Bot
An intelligent web scraping application designed to automate the process of finding job listings on LinkedIn. This tool provides a user-friendly interface to search for jobs based on role and location, apply advanced filters, and visualize the results. The project is containerized with Docker for reliable and consistent deployment.

## Overview
Manually searching for jobs on LinkedIn can be a repetitive and time-consuming task. This project was built to streamline that process by providing a simple web interface to scrape job data programmatically. The application uses Selenium to control a web browser, navigates to LinkedIn, performs the specified search, and parses the results into a clean, usable format.

The entire application is wrapped in a Streamlit UI and containerized using Docker, which solves common deployment challenges related to browser and driver compatibility in cloud environments.

## Features
- Dynamic Job Search: Scrape jobs based on any job role and comma-separated locations.

- Experience Level Filtering: Narrow down the search results by selecting one or more experience levels (e.g., "Entry level", "Mid-Senior level").

- Data Cleaning: Automatically removes duplicate job listings based on the job title, company, and application link.

- Sorted Results: The final list of jobs is sorted by post date, showing the most recent listings first.

- Data Visualization: Includes a bar chart showing the top 20 companies with the most job openings for the searched role.

- CSV Export: Download the cleaned and sorted job data as a CSV file for offline analysis.

- Containerized Deployment: Uses a Dockerfile to ensure the application and all its dependencies (including the correct browser version) run consistently anywhere.

## Tech Stack

| Layer | Technology |
| ------------- |:-------------:|
| Backend & Web Framework | Python, Streamlit |
| Web Scraping | Selenium, BeautifulSoup4 |
| Data Manipulation | Pandas |
| Containerization | Docker |
| Deployment | Render  |

## Demo
🔗 [Try the Live app](https://linkedin-job-scraper-u88y.onrender.com/)

📂 [View the source code](https://github.com/RohitBhavsar27/LinkedIn-Job-Scraper)

## Local Setup and Installation
To run this project on your local machine, follow these steps:

1. Clone the repository:
```
git clone https://github.com/RohitBhavsar27/LinkedIn-Job-Scraper.git
cd LinkedIn-Job-Scraper
```

2. Create a virtual environment:
```
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Run the Streamlit application:
```
streamlit run app.py
```

The application should now be running and accessible in your web browser.

## Deployment on Render
1. This application is configured for easy deployment on platforms that support Docker, like Render.

2. Push to GitHub: Ensure your repository contains the app.py, requirements.txt, and Dockerfile.

3. Create a Render Account: Sign up at render.com.

4. New Web Service: From the dashboard, create a new "Web Service" and connect your GitHub repository.

5. Configuration:

    - Environment: Select Docker. Render will automatically detect and use your Dockerfile.

    - Instance Type: The Free tier is sufficient.

5. Deploy: Click "Create Web Service". Render will build the Docker image and deploy your application. The first build may take several minutes.

## Team & Credits
This project was built by Rohit Bhavsar as part of the Elevate Labs Virtual Internship Program (2025). Special thanks to the mentors and the Elevate community for their support and feedback.