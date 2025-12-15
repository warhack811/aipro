import httpx
import asyncio

async def test_persona_endpoint():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # First login to get session
        # Then test persona endpoint
        
        # Test if endpoint exists (OPTIONS-like behavior)
        response = await client.post(
            "/api/v1/user/personas/select",
            json={"persona": "romantic"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_persona_endpoint())
