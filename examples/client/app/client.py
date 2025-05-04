import asyncio
import os
from typing import Optional
from contextlib import AsyncExitStack
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import TextContent
from dotenv import load_dotenv
from models.server_meta_data import ServerMetadata
import openai
import httpx
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
load_dotenv()  # Load environment variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_REGISTRY_URL = "http://McpReg-McpRe-ZMg9vwW4XWZI-1842878941.us-east-2.elb.amazonaws.com"
MCP_LOCAL_URL = "http://host.docker.internal:8000"
RUN_LOCAL = os.getenv("RUN_LOCAL", "False").lower() == "true"

class LLMClient:
    """Manages communication with the LLM provider."""

    def __init__(self, api_key: str) -> None:
        self.api_key: str = api_key
        self.openai_client = openai.OpenAI(api_key=api_key)

    def get_ai_response(
        self,
        message_array: list[ChatCompletionMessageParam],
        available_tools: list[ChatCompletionToolParam],
        use_tools: bool = True,
    ):
        tool_use_setting = "auto" if use_tools else "none"

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=message_array,
            tools=available_tools,
            tool_choice=tool_use_setting,
        )

        return response.choices[0].message 
    
class ChatSession:
    def __init__(self, api_key: str) -> None:
        self.llm_client = LLMClient(api_key)
        self.messages: list[ChatCompletionMessageParam] = []
        self.mcp_clients: list[MCPClient] = []
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
    
    async def chat_loop(self):
        print("\nMCP SSE Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def process_query(self, query: str) -> str:
        self.messages.append({"role": "user", "content": query})

        # 🔍 Step 1: Search for best-matching server
        server: ServerMetadata = await find_best_server_for_query(query)

        # 🔌 Step 2: Connect to the selected MCP server
        mcp = MCPClient(server.url, server.id)
        await mcp.setup()  # Ensure tools are loaded and session is connected

        # Store session and tools
        self.session = mcp.session
        self.available_tools = mcp.available_tools

        # 🧠 Step 3: Let OpenAI decide if it wants to call a tool
        ai_message = self.llm_client.get_ai_response(self.messages, self.available_tools, use_tools=True)

        # 🛠 Step 4: Tool call handling
        if ai_message.tool_calls:
            tool_call = ai_message.tool_calls[0]  # Assume one tool for now
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"Will Call Tool: {tool_name}")

            # 🔧 Step 5: Actually call the tool via MCP
            tool_result = await self.session.call_tool(tool_name, tool_args)

            if tool_result.content and isinstance(tool_result.content[0], TextContent):
                tool_result_content = tool_result.content[0].text
            else:
                tool_result_content = json.dumps({"result": "unknown"})

            # 🧾 Step 6: Add result to chat history
            self.messages.append({
                "role": "assistant",
                "tool_calls": [tool_call.model_dump()]
            })
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result_content
            })

            # 💬 Step 7: Get final LLM response
            final_response = self.llm_client.get_ai_response(self.messages, self.available_tools, use_tools=False)
            await mcp.cleanup()
            return final_response.content
        await mcp.cleanup()
        # 💡 Step 8: No tool used
        return ai_message.content
    
class MCPClient:
    def __init__(self, url: str, id: str):
        self.url = url
        self.id = id
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools: list[ChatCompletionToolParam] = []

    async def setup(self):
        """Connect to MCP server and list tools."""
        sse_url = self.url.rstrip("/") + "/sse"
        read, write = await self.exit_stack.enter_async_context(sse_client(sse_url))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print(f"Connected to server {self.url} with tools:", [t.name for t in tools])
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        **tool.inputSchema,
                        "additionalProperties": False
                    },
                },
            }
            for tool in tools
        ] 

    async def cleanup(self):
        await self.exit_stack.aclose()

    
async def find_best_server_for_query(query: str) -> ServerMetadata:
    """Query the MCP registry and return the best matching server metadata."""
    registry_url = MCP_LOCAL_URL if RUN_LOCAL else MCP_REGISTRY_URL
    search_url = f"{registry_url}/search_tools"

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(search_url, json={"query": query})
        resp.raise_for_status()
        matches = resp.json()

        if not matches:
            raise ValueError("No matching MCP servers found for query")

        best_match = matches[0]
        
        # Query the registry for full server metadata
        full_metadata_url = f"{registry_url}/get_server?id={best_match['server_id']}"
        resp = await client.get(full_metadata_url)
        resp.raise_for_status()
        server_dict = resp.json()

        return ServerMetadata.model_validate(server_dict)
    
async def main():
    chat = ChatSession(OPENAI_API_KEY)
    await chat.chat_loop()


if __name__ == "__main__":
    asyncio.run(main())