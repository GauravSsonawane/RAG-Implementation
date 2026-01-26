import asyncio
from storage.database import AsyncSessionLocal
from storage.models import DocumentMetadata
from sqlalchemy import select

async def check_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DocumentMetadata))
        docs = result.scalars().all()
        
        print(f"📊 Total Documents in DB: {len(docs)}")
        for doc in docs:
            print(f"- {doc.filename} (Status: {doc.status})")

if __name__ == "__main__":
    asyncio.run(check_db())
