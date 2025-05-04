from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
import json
import openai
from chromadb.config import Settings
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from routes import register_server
from models.server_meta_data import ServerMetadata
# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Setup FastAPI
app = FastAPI(
    title="MCP Registry",
    description="Service to register, update, and discover MCP tool servers.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup DynamoDB
if os.environ.get("RUN_LOCAL") == "True":
    print("⚠️ MOCKING DYNAMODB")
    from unittest.mock import MagicMock
    servers_table = MagicMock()
else:
    region = os.environ.get("AWS_REGION", "us-east-2")
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb", region_name=region)
    servers_table = dynamodb.Table(table_name)

# Setup Chroma
chroma_client = chromadb.Client(Settings(persist_directory="./chroma_index"))
embedding_function = OpenAIEmbeddingFunction(api_key=OPENAI_API_KEY)
tools_collection = chroma_client.get_or_create_collection("tools", embedding_function=embedding_function)

# Load all tools into Chroma
def sync_chroma_from_dynamodb():
    response = servers_table.scan()
    servers = response.get("Items", [])
    print(f"🔄 Syncing {len(servers)} servers into Chroma")

    documents, ids, metadatas = [], [], []

    for server in servers:
        for tool in server.get("tools", []):
            tool_id = f"{server['id']}:{tool['name']}"
            text = f"[{server.name} - {server.description or ''}] - {tool.name} - {tool.description or ''}"
            metadata = {
                "server_id": server["id"],
                "server_name": server["name"],
                "tool_name": tool["name"],
                "tool_description": tool.get("description", "")
            }
            documents.append(text)
            ids.append(tool_id)
            metadatas.append(metadata)

    if documents:
        tools_collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"✅ Indexed {len(documents)} tools in Chroma.")

# Startup logic
@app.on_event("startup")
async def startup_event():
    sync_chroma_from_dynamodb()

# === Models ===
class ToolSearchRequest(BaseModel):
    query: str

# === Routes ===

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/register_server")
async def register_server_endpoint(server_metadata: dict):
    server = ServerMetadata.model_validate(server_metadata)
    return await register_server(server, servers_table, tools_collection)

@app.post("/search_tools")
async def search_tools_endpoint(request: ToolSearchRequest):
    try:
        result = tools_collection.query(query_texts=[request.query], n_results=5)
        return result["metadatas"][0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {e}")
