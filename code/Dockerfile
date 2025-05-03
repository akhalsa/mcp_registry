# Use an official, lightweight Python image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install dependencies
COPY ./code/app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the actual FastAPI app code
COPY ./code/app /app
COPY ./models /usr/local/lib/python3.13/models
# Expose port 80
EXPOSE 80

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
