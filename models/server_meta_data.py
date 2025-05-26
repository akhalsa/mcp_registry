from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from mcp.types import Tool


class ResourceMetadata(BaseModel):
    name: str = Field(..., description="Name of the resource")
    description: str = Field(..., description="Description of what data or asset the resource provides")

class PromptMetadata(BaseModel):
    name: str = Field(..., description="Name of the prompt or strategy")
    description: str = Field(..., description="Description of the prompt's purpose or behavior")

class ServerMetadata(BaseModel):
    id: Optional[str] = Field(None, description="Unique server ID (assigned by registry)")
    name: str = Field(..., description="Human-readable server name")
    description: str = Field(..., description="What capabilities this server offers")
    tags: List[str] = Field(..., description="Keyword tags for filtering and search")
    url: str = Field(..., description="Base URL of the MCP server")
    
    tools: List[Tool] = Field(default_factory=list, description="List of tools served by this server")
    resources: List[ResourceMetadata] = Field(default_factory=list, description="List of resources served by this server")
    prompts: List[PromptMetadata] = Field(default_factory=list, description="List of prompts provided by this server")
    
    created_at: Optional[datetime] = Field(None, description="Timestamp when server was registered")
    last_heartbeat: Optional[datetime] = Field(None, description="Last time server sent a heartbeat")