from fastapi import FastAPI, HTTPException
from models.server_meta_data import ServerMetadata
from uuid import uuid4
from datetime import datetime
import json

def register_server_routes(app: FastAPI, servers_table):
    @app.post("/register_server")
    async def register_server(server: ServerMetadata):
        """Register a new MCP server and store it in DynamoDB."""
        try:
            server_id = server.id or str(uuid4())
            now = datetime.now(datetime.UTC).isoformat()

            server_record = server.copy(update={
                "id": server_id,
                "created_at": now,
                "last_heartbeat": now
            })

            servers_table.put_item(Item=json.loads(server_record.json()))
            return {"server_id": server_id, "status": "registered"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/heartbeat")
    async def heartbeat(server_id: str):
        """Update last_heartbeat for an existing server."""
        try:
            now = datetime.now(datetime.UTC).isoformat()

            servers_table.update_item(
                Key={"id": server_id},
                UpdateExpression="SET last_heartbeat = :now",
                ExpressionAttributeValues={":now": now}
            )

            return {"server_id": server_id, "status": "heartbeat updated"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
