import asyncio
from storage.database import AsyncSessionLocal
from storage.models import DocumentMetadata
from sqlalchemy import update

async def reset():
    print("🔄 Resetting DocumentMetadata statuses...")
    async with AsyncSessionLocal() as session:
        await session.execute(update(DocumentMetadata).values(status="reset"))
        await session.commit()
    print("✅ Done.")

if __name__ == "__main__":
    asyncio.run(reset())
