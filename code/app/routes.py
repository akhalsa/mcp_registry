from fastapi import FastAPI, HTTPException
from models.server_meta_data import ServerMetadata, ToolMetadata
from uuid import uuid4
from datetime import datetime, timezone
import json
import httpx

def register_server_routes(app: FastAPI, servers_table):
    
    @app.post("/register_server")
    async def register_server(server: ServerMetadata):
        """Register a new MCP server and store it in DynamoDB."""
        try:
            server_id = server.id or str(uuid4())
            now = datetime.now(timezone.utc).isoformat()
            server_url = server.url.rstrip("/")
            list_tools_url = f"{server_url}/{server.list_tools_endpoint.lstrip('/')}"
            call_tool_url = f"{server_url}/{server.call_tool_endpoint.lstrip('/')}"

            list_tools_method = "POST"
            call_tool_method = "POST"

            # Try POST, fallback to GET if needed
            tool_data = None
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    response = await client.post(list_tools_url)
                    response.raise_for_status()
                    tool_data = response.json()
                except httpx.HTTPStatusError as post_err:
                    if post_err.response.status_code in {404, 405}:
                        try:
                            print(f"POST failed, retrying with GET: {list_tools_url}")
                            list_tools_method = "GET"
                            response = await client.get(list_tools_url)
                            response.raise_for_status()
                            tool_data = response.json()
                        except Exception as get_err:
                            raise HTTPException(status_code=400, detail=f"Both POST and GET failed for {list_tools_url}: {get_err}")
                    else:
                        raise HTTPException(status_code=400, detail=f"POST failed for {list_tools_url}: {post_err}")
                except Exception as err:
                    raise HTTPException(status_code=400, detail=f"Error connecting to {list_tools_url}: {err}")

            # Extract tool list from JSON
            try:
                # Try treating tool_data directly as a list
                parsed_tools = [ToolMetadata.model_validate(tool, from_attributes=False) for tool in raw_tools]
            except Exception:
                # Fallback: check if it's a dict with a 'tools' key
                raw_tools = tool_data.get("tools")
                if not isinstance(raw_tools, list):
                    raise HTTPException(status_code=422, detail="Expected 'tools' to be a list in response")
                try:
                    parsed_tools = [ToolMetadata.model_validate(tool, from_attributes=False) for tool in raw_tools]
                except Exception as parse_err:
                    raise HTTPException(status_code=422, detail=f"Tool data validation failed: {parse_err}")
                


            # Build server record
            server_record = server.copy(update={
                "id": server_id,
                "created_at": now,
                "last_heartbeat": now,
                "tools": parsed_tools,
                "list_tools_endpoint_method": list_tools_method,
                "call_tool_endpoint_method": call_tool_method,
                "list_tools_endpoint": server.list_tools_endpoint,
                "call_tool_endpoint": server.call_tool_endpoint
            })

            servers_table.put_item(Item=json.loads(server_record.json()))
            return {
                "server_id": server_id,
                "status": "registered",
                "tool_count": len(parsed_tools)
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
