from mcp.server.fastmcp import FastMCP

from pydantic import BaseModel
from typing import List
import math

# Create the MCP server
mcp = FastMCP("Calculator")

# Register tool: calculate_sum
@mcp.tool()
def calculate_sum(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b

# Register tool: multiply
@mcp.tool()
def multiply(args: List[float]) -> float:
    """Multiply a list of numbers together"""
    return math.prod(args)

# Run with: python server.py
if __name__ == "__main__":
    mcp.run()
