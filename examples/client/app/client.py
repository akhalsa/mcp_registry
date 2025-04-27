import httpx
import asyncio
import time
from dotenv import load_dotenv
    
load_dotenv()

# Define the MCP server URL (replace with the actual URL of the MCP server)
MCP_SERVER_URL = "http://exampl-examp-pjmkdsumyhfp-1907375994.us-east-2.elb.amazonaws.com"

# Request body to call the "calculate_sum" tool
payload = {
    "name": "calculate_sum",
    "arguments": {
        "a": 5,
        "b": 3
    }
}

# Function to call the tool via HTTP POST request
async def call_tool():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MCP_SERVER_URL}/tools/call", json=payload)
        
        if response.status_code == 200:
            print(f"Tool response: {response.json()}")
        else:
            print(f"Failed to call tool. Status Code: {response.status_code}")

# Main entry point to run the client and make requests periodically
async def main():
    while True:
        print("Calling tool...")
        await call_tool()
        time.sleep(5)  # Call the tool every 5 seconds

# Run the client
if __name__ == "__main__":
    asyncio.run(main())
