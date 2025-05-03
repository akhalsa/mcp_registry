from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ToolMetadata(BaseModel):
    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="Brief description of what the tool does")
    input_schema: Dict = Field(..., alias="inputSchema", description="Tool input schema")
    class Config:
        allow_population_by_field_name = True  # Allow using input_schema internally

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
    
    tools: List[ToolMetadata] = Field(default_factory=list, description="List of tools served by this server")
    resources: List[ResourceMetadata] = Field(default_factory=list, description="List of resources served by this server")
    prompts: List[PromptMetadata] = Field(default_factory=list, description="List of prompts provided by this server")
    
    created_at: Optional[datetime] = Field(None, description="Timestamp when server was registered")
    last_heartbeat: Optional[datetime] = Field(None, description="Last time server sent a heartbeat")
    
    list_tools_endpoint: Optional[str] = Field(
        default="/list_tools",
        description="Path to fetch list of tools"
    )
    call_tool_endpoint: Optional[str] = Field(
        default="/call_tool",
        description="Path to invoke a tool by name"
    )
    call_endpoint_method: Optional[str] = Field(
        default="POST",
        description="HTTP method to use with the call endpoint"
    )
    list_tools_endpoint_method: Optional[str] = Field(
        default="POST",
        description="HTTP method to use for with the list tools endpoint"
    )
