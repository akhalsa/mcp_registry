from fastapi import FastAPI, HTTPException
from mcp import ClientSession
from mcp.types import Tool
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
from uuid import uuid4
from datetime import datetime, timezone
import json
from models.server_meta_data import ServerMetadata

def register_server_routes(app: FastAPI, servers_table):
    
    @app.post("/register_server")
    async def register_server(server: ServerMetadata):
        """Register a new MCP server and store it in DynamoDB."""
        try:
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

                servers_table.put_item(Item=json.loads(server_record.model_dump_json()))
                return {
                    "server_id": server_id,
                    "status": "registered",
                    "tool_count": len(parsed_tools)
                }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
