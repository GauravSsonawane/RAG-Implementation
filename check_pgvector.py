import asyncio
import os
from sqlalchemy import text
from storage.database import engine
from dotenv import load_dotenv

load_dotenv()

async def check_pgvector():
    async with engine.connect() as conn:
        print("Checking PGVector tables...")
        
        # Check collections
        res = await conn.execute(text("SELECT name FROM langchain_pg_collection;"))
        collections = res.scalars().all()
        print(f"Collections: {collections}")
        
        # Check embeddings count
        res = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding;"))
        count = res.scalar()
        print(f"Total Embeddings: {count}")
        
        # Check embeddings per collection
        for col in collections:
            res = await conn.execute(text("""
                SELECT count(*) FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = :name
            """), {"name": col})
            col_count = res.scalar()
            print(f"Embeddings in '{col}': {col_count}")

if __name__ == "__main__":
    asyncio.run(check_pgvector())
