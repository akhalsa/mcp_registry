# Use an official, lightweight Python image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Copy application code
COPY code/app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY code/app /app
COPY models /app/models
ENV PYTHONPATH="/app:$PYTHONPATH"

# Launch FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]