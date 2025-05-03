# main.py

from fastapi import FastAPI
from routes import register_server_routes

# Instantiate FastAPI app
app = FastAPI(
    title="MCP Registry",
    description="Service to register, update, and discover MCP tool servers.",
    version="0.1.0",
)

# Register all route groups
register_server_routes(app)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
