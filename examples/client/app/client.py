import asyncio
import os
from typing import Optional
from contextlib import AsyncExitStack
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import TextContent
from dotenv import load_dotenv
import openai
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
load_dotenv()  # Load environment variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_SERVER_URL = "http://Exampl-Examp-GTQEZ6l1f3w0-988708398.us-east-2.elb.amazonaws.com"
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
    
class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.mcp_url = (MCP_LOCAL_URL if RUN_LOCAL else MCP_SERVER_URL) + "/sse"
        print(f"RUN_LOCAL: {RUN_LOCAL}")
        print(f"MCP URL: {self.mcp_url}")
        self.llm_client = LLMClient(OPENAI_API_KEY)
        self.messages: list[ChatCompletionMessageParam] = [] 
        self.available_tools: list[ChatCompletionToolParam] = []

        

    async def connect_to_server(self):
        """Connect to a remote MCP server via SSE."""
        read, write = await self.exit_stack.enter_async_context(sse_client(self.mcp_url))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to remote MCP server with tools:", [tool.name for tool in tools])
 
        self.available_tools: list[ChatCompletionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        **tool.inputSchema,
                        "additionalProperties": False  # ✅ Required by OpenAI
                    },
                },
            }
            for tool in tools
        ]
        print(self.available_tools) 

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available MCP tools."""
        if not self.session:
            raise RuntimeError("MCP session not initialized")

        # Step 1: Start conversation
        self.messages.append({"role": "user", "content": query})
         

        # Step 3: First call to OpenAI (with tool use enabled)
        ai_message = self.llm_client.get_ai_response(self.messages, self.available_tools, use_tools=True)

        # Step 4: If the LLM wants to use a tool...
        if ai_message.tool_calls:
            print(f"Will Call Tool: {ai_message.tool_calls[0].function.name}")
            tool_call = ai_message.tool_calls[0]  # Assume one tool for now
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Step 5: Execute the tool via MCP
            tool_result = await self.session.call_tool(tool_name, tool_args)
            # Extract actual content (works if you know it’s always TextContent)
            if tool_result.content and isinstance(tool_result.content[0], TextContent):
                tool_result_content = tool_result.content[0].text
            else:
                tool_result_content = json.dumps({"result": "unknown"}) 
            # Step 6: Add tool call + result to conversation
            self.messages.append({
                "role": "assistant",
                "tool_calls": [tool_call.model_dump()]  # Required OpenAI format
            })
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result_content
            })
            print(f"Going back to LLM with:{self.messages}")

            # Step 7: Second call to LLM to interpret the tool result
            final_response = self.llm_client.get_ai_response(self.messages, self.available_tools, use_tools=False)
            return final_response.content

        # Step 8: No tool call — return LLM’s original reply
        return ai_message.content

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

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    client = MCPClient()
    try:
        await client.connect_to_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())