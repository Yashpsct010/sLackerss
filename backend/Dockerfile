FROM python:3.11-slim

WORKDIR /app

# Install system dependencies that might be needed for pandas/xgboost
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port
EXPOSE 8000

# Command to run the FastAPI server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
