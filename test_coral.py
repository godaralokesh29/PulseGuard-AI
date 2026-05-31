import asyncio
from backend.services.coral_client import query_coral

async def main():
    print("Testing Coral Integration...")
    try:
        # Query coral's internal tables to verify it's working
        results = await query_coral("SELECT table_name, schema_name FROM coral.tables LIMIT 5")
        print(f"Success! Retrieved {len(results)} tables from Coral:")
        for r in results:
            print(f" - {r.get('schema_name')}.{r.get('table_name')}")
    except Exception as e:
        print(f"Failed to query Coral: {e}")

if __name__ == "__main__":
    asyncio.run(main())
