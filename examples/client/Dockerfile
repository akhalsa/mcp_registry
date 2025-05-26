# Use an official, lightweight Python image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install dependencies including dotenv
COPY ./examples/client/app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the actual FastAPI app code
COPY ./examples/client/app /app
COPY ./.env /app/.env 
COPY examples/server/app /app
COPY models /app/models

# Expose port 80
EXPOSE 80

# Start the client app
CMD ["python", "client.py"]

