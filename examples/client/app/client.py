import httpx
import asyncio
import time
from dotenv import load_dotenv

load_dotenv()

# Define the MCP server URL (replace with the actual URL of the MCP server)
MCP_SERVER_URL = "http://Exampl-Examp-GTQEZ6l1f3w0-988708398.us-east-2.elb.amazonaws.com"

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

# Function to fetch the list of tools via HTTP GET request
async def get_tools():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MCP_SERVER_URL}/tools/list")
        
        if response.status_code == 200:
            print(f"Tools response: {response.json()}")
        else:
            print(f"Failed to fetch tools. Status Code: {response.status_code}")

# Test Google URL to check if Docker can make external requests
async def test_google_connection():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.google.com")
        
        if response.status_code == 200:
            print("Successfully reached google.com!")
        else:
            print(f"Failed to reach google.com. Status Code: {response.status_code}")


# Main entry point to run the client and make requests periodically
async def main():
    while True:
        print("getting tools..")
        await call_tool()
        time.sleep(5)  # Call the tool every 5 seconds
        #print("Testing google connection...")
        #await test_google_connection()
        #time.sleep(5)  # Call the tool every 5 seconds

# Run the client
if __name__ == "__main__":
    asyncio.run(main())
