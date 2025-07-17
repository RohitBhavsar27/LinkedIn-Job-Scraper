# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system-level dependencies required for Chromium
# This is the crucial step that failed on Streamlit Cloud
RUN apt-get update && apt-get install -y \
    chromium \
    # Clean up the cache to keep the image size down
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's source code from your computer to the container
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# Define the command to run your app when the container starts
# This also sets the headless flag needed for the server environment
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
