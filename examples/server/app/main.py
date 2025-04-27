from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/tools/list")
async def list_tools():
    return {
        "tools": [
            {
                "name": "calculate_sum",
                "description": "Add two numbers together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": { "type": "number" },
                        "b": { "type": "number" }
                    },
                    "required": ["a", "b"]
                }
            }
        ]
    }

@app.post("/tools/call")
async def call_tool(request: dict):
    tool_name = request.get("name")
    args = request.get("arguments", {})

    if tool_name == "calculate_sum":
        a = args.get("a")
        b = args.get("b")
        return {"result": a + b}
    else:
        return {"error": "Tool not found"}
