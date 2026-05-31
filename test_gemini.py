import asyncio
import os
from backend.services.llm_engine import get_llm_engine
from backend.config import get_settings

async def main():
    settings = get_settings()
    print(f"Key exists: {bool(settings.gemini_api_key)}")
    engine = get_llm_engine()
    try:
        res = await engine.generate("Say 'Hello, World!'")
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
