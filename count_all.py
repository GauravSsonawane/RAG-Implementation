import asyncio
import os
from sqlalchemy import text
from storage.database import engine
from dotenv import load_dotenv

load_dotenv()

async def check():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT name, uuid FROM langchain_pg_collection;"))
        collections = res.all()
        for name, uuid in collections:
            count_res = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding WHERE collection_id = :id"), {"id": uuid})
            count = count_res.scalar()
            print(f"Collection: {name} | Embeddings: {count}")

if __name__ == "__main__":
    asyncio.run(check())
