import asyncio
import json
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client
import logging
import os 
from dotenv import load_dotenv
# Load env vars
load_dotenv()

# --- Setup constants ---
MCP_SERVER_URL = "http://Exampl-Examp-GTQEZ6l1f3w0-988708398.us-east-2.elb.amazonaws.com"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def main():
    async with AsyncExitStack() as stack:
        # Establish SSE connection
        transport = await stack.enter_async_context(sse_client(MCP_SERVER_URL))
        read, write = transport

        # Initialize client session
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        # List available tools
        tools = await session.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        # Call a tool (replace 'tool_name' and 'args' with actual values)
        tool_name = "example_tool"
        args = {"param1": "value1"}
        result = await session.call_tool(tool_name, args)
        print(f"Result from {tool_name}: {result}")

if __name__ == "__main__":
    asyncio.run(main())


async def main():
    # Setup connection to MCP server
    params = HTTPServerParameters(url=MCP_SERVER_URL)
    async with http_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            if not tools:
                logging.warning("No tools found on the server.")
                return

            # Show available tools
            for tool in tools:
                logging.info(f"Tool: {tool.name} — {tool.description}")

            # Pick the first tool
            tool = tools[0]
            input_schema = tool.inputSchema
            logging.info(f"Calling tool: {tool.name} with schema: {input_schema}")

            # Generate dummy arguments based on schema
            dummy_args = {}
            for field, spec in input_schema.get("properties", {}).items():
                if spec["type"] == "string":
                    dummy_args[field] = "example"
                elif spec["type"] == "integer":
                    dummy_args[field] = 42
                elif spec["type"] == "number":
                    dummy_args[field] = 3.14
                elif spec["type"] == "boolean":
                    dummy_args[field] = True
                elif spec["type"] == "array":
                    dummy_args[field] = []
                elif spec["type"] == "object":
                    dummy_args[field] = {}
                else:
                    dummy_args[field] = None

            result = await session.call_tool(tool.name, arguments=dummy_args)
            logging.info(f"Tool response: {result}")

if __name__ == "__main__":
    asyncio.run(main())
