from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from starlette.routing import Mount
from typing import List, Annotated
from pydantic import Field, BaseModel
import math

# Create the MCP server
mcp = FastMCP("Calculator")

@mcp.tool(
    description="Add two numbers together.",
    annotations={"title": "Calculate Sum"}
)
def calculate_sum(
    a: Annotated[float, Field(description="First number to add")],
    b: Annotated[float, Field(description="Second number to add")]
) -> dict[str, float]: 
    return {"result": a + b}

@mcp.tool(
    description="Multiply a list of numbers.",
    annotations={"title": "Multiply List"}
)
def multiply(
    args: Annotated[List[float], Field(description="List of numbers to multiply")]
) -> float:
    return math.prod(args)

# Create a FastAPI app and mount the MCP app
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

mcp_app = mcp.sse_app()
print(f"got MCP app", mcp_app)
# Mount the MCP server at root or a subpath like `/mcp`
app.mount("/", mcp_app)

