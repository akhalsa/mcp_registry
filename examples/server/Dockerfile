# Use an official, lightweight Python image
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install dependencies
COPY ./examples/server/app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt


# Copy the actual FastAPI app code
COPY ./examples/server/app /app

# Expose port 80
EXPOSE 80

CMD ["mcp", "run", "main.py"]

