from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

class CalculateSumArguments(BaseModel):
    a: float
    b: float

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/tools/list")
async def list_tools():
    calculate_sum_input_schema = CalculateSumArguments.model_json_schema()
    return {
        "tools": [
            {
                "name": "calculate_sum",
                "description": "Add two numbers together",
                "inputSchema": calculate_sum_input_schema
            }
        ]
    }

@app.post("/tools/call")
async def call_tool(request: dict):
    tool_name = request.get("name")
    args = request.get("arguments", {})

    if tool_name == "calculate_sum":
        tool_args = CalculateSumArguments(**args)
        result = tool_args.a + tool_args.b
        return {"result": result}
    else:
        return {"error": "Tool not found"}
