FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK CMD curl --fail http://localhost:80/_stcore/health

# Run Streamlit app
ENTRYPOINT ["streamlit", "run", "streamlit_cloudtrail_chatbot.py", "--server.port=80", "--server.address=0.0.0.0"]
