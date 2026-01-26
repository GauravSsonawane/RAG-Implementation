import asyncio
from sqlalchemy import text
from storage.database import engine

async def count():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding"))
        print(f"📊 Total Embeddings in Vector Store: {res.scalar()}")

if __name__ == "__main__":
    asyncio.run(count())
