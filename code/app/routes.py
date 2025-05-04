from fastapi import FastAPI, HTTPException
from mcp import ClientSession
from mcp.types import Tool
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
from uuid import uuid4
from datetime import datetime, timezone
import json
from models.server_meta_data import ServerMetadata
from fastapi import Query
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def embed_text(text: str) -> list[float]:
    response = await openai.AsyncOpenAI(api_key=OPENAI_API_KEY).embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


async def register_server(server: ServerMetadata, servers_table, tools_collection):
    """Register a new MCP server and store it in DynamoDB."""
    server_id = server.id or str(uuid4())
    now = datetime.now(timezone.utc)

    # Normalize URL and extract /sse endpoint
    server_url = server.url.rstrip("/")
    if server_url.endswith("/sse"):
        server_url_sse = server_url
        server_url = server_url[:-4]  # remove '/sse'
    else:
        server_url_sse = f"{server_url}/sse"

    print(f"Server URL: {server_url}")
    print(f"Server URL SSE: {server_url_sse}")

    # Use MCP SDK to open an SSE connection and list tools
    async with AsyncExitStack() as exit_stack:
        read, write = await exit_stack.enter_async_context(sse_client(server_url_sse))
        session = await exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        response = await session.list_tools()
        tools = response.tools  # already list[Tool]
        print("Connected to remote MCP server with tools:", [tool.name for tool in tools])

        # Validate tool list
        parsed_tools = [Tool.model_validate(tool) for tool in tools]

        # Save server record
        server_record = server.copy(update={
            "id": server_id,
            "created_at": now,
            "last_heartbeat": now,
            "tools": parsed_tools,
            "url": server_url,  # clean base URL
        })

        servers_table.put_item(Item=server_record.model_dump(mode="json"))
        
        documents, ids, metadatas = [], [], []
        for tool in parsed_tools:
            doc_id = f"{server_id}:{tool.name}"
            text = f"[{server.name} - {server.description or ''}] - {tool.name} - {tool.description or ''}"
            metadata = {
                "server_id": server_id,
                "server_name": server.name,
                "tool_name": tool.name,
                "tool_description": tool.description or ""
            }
            documents.append(text)
            ids.append(doc_id)
            metadatas.append(metadata)

        if documents:
            tools_collection.add(documents=documents, ids=ids, metadatas=metadatas)
            print(f"✅ Added {len(documents)} tools to Chroma.")
        
        return {
            "server_id": server_id,
            "status": "registered",
            "tool_count": len(parsed_tools)
        }
            

class ToolSearchRequest(BaseModel):
    query: str

