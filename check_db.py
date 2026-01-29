import asyncio
from storage.database import AsyncSessionLocal
from storage.models import DocumentMetadata
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(DocumentMetadata))
        docs = res.scalars().all()
        for d in docs:
            print(f"{d.filename}: {d.status}")

if __name__ == "__main__":
    asyncio.run(check())
