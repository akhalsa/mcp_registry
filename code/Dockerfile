# Use an official, lightweight Python image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        g++ \
        git \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY code/app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY code/app /app
COPY models /app/models
ENV PYTHONPATH="/app:$PYTHONPATH"
COPY .env /app/.env 

# Launch FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]