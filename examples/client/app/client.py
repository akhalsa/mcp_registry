import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import create_model
import httpx
import asyncio

# Load env vars
load_dotenv()

# --- Setup constants ---
MCP_SERVER_URL = "http://Exampl-Examp-GTQEZ6l1f3w0-988708398.us-east-2.elb.amazonaws.com"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Setup model ---
model = ChatOpenAI(model="gpt-4o", temperature=0)

# --- Setup memory ---
memory = MemorySaver()

# --- Field type mapping (missing in your code) ---
def field_type_mapping(type_str: str):
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return mapping.get(type_str, str)

# --- MCP Dynamic tool fetch ---
async def fetch_mcp_tools():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MCP_SERVER_URL}/tools/list")
        response.raise_for_status()
        return response.json()["tools"]

# --- Call a single MCP tool ---
async def call_mcp_tool(tool_name: str, arguments: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_SERVER_URL}/tools/call",
            json={"name": tool_name, "arguments": arguments}
        )
        response.raise_for_status()
        return response.json()
from pydantic import Field

def create_mcp_tool(tool_metadata):
    input_schema = tool_metadata["inputSchema"]
    properties = input_schema.get("properties", {})

    DynamicArguments = create_model(
        f"{tool_metadata['name']}Input",
        **{
            field_name: (
                field_type_mapping(field_props["type"]),
                Field(
                    default=...,
                    description=field_props.get("description", "")
                )
            )
            for field_name, field_props in properties.items()
        }
    )

    @tool(tool_metadata["name"], args_schema=DynamicArguments, description=tool_metadata.get("description", "MCP tool"))
    def _tool(**kwargs):
        with httpx.Client() as client:
            response = client.post(
                f"{MCP_SERVER_URL}/tools/call",
                json={"name": tool_metadata["name"], "arguments": kwargs}
            )
            response.raise_for_status()
            return response.json()

    return _tool

# --- Create the graph once ---
async def build_graph_once():
    tool_metadata_list = await fetch_mcp_tools()
    tools = [create_mcp_tool(meta) for meta in tool_metadata_list]
    print(f"tools: {tools}")
    graph = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=memory,
    )
    return graph

# --- main driver ---
async def main():
    graph = await build_graph_once()

    thread_id = "user1"

    messages = [
        "Please add 2 and 2 together.",
        "Now add 7 and 5.",
        "and if you add 5 more to that?",
    ]

    
    for i, msg in enumerate(messages):
        print(f"\n\n=== 📨 Human Message {i+1}: {msg}")

        input_data = {"messages": [HumanMessage(content=msg)]}
        config = {"configurable": {"thread_id": thread_id}}

        result = graph.invoke(input_data, config=config)

        for m in result["messages"]:
            if isinstance(m, AIMessage):
                # Check if AI is making tool calls
                tool_calls = m.additional_kwargs.get("tool_calls", [])
                if tool_calls:
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("function", {}).get("name")
                        tool_args = tool_call.get("function", {}).get("arguments")
                        print(f"\n🛠️  Tool Call → {tool_name}({tool_args})")
                else:
                    # Normal model text output
                    print(f"\n🤖 AI Response: {m.content}")
            elif isinstance(m, ToolMessage):
                # This is the result of a tool call
                print(f"\n📦 Tool Response: {m.content}")
            else:
                print(f"\n⚡ Other Message Type: {m}")
if __name__ == "__main__":
    asyncio.run(main())
