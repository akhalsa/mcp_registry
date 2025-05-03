from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os

from routes import register_server_routes

# Instantiate FastAPI app
app = FastAPI(
    title="MCP Registry",
    description="Service to register, update, and discover MCP tool servers.",
    version="0.1.0",
)

# Enable CORS (optional but useful for frontend dev/testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up shared DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")  # Make region dynamic if needed
table_name = os.environ["DYNAMODB_TABLE_NAME"]
servers_table = dynamodb.Table(table_name)

# Register route handlers, injecting the table dependency
register_server_routes(app, servers_table)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
