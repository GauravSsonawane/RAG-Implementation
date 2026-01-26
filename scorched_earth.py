import asyncio
from storage.database import engine
from sqlalchemy import text

async def scorched_earth():
    async with engine.connect() as conn:
        print("Fetching all collections...")
        res = await conn.execute(text("SELECT name, uuid FROM langchain_pg_collection"))
        collections = res.all()
        
        for name, uuid in collections:
            print(f"Collection: {name} (UUID: {uuid})")
            # Count embeddings
            count_res = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding WHERE collection_id = :id"), {"id": uuid})
            count = count_res.scalar()
            print(f"  Count: {count}")
            
            # Sample sources
            source_res = await conn.execute(text("SELECT DISTINCT cmetadata->>'source' FROM langchain_pg_embedding WHERE collection_id = :id"), {"id": uuid})
            sources = [r[0] for r in source_res.all()]
            print(f"  Sources: {sources}")
            
            # DELETE ALL EMBEDDINGS IN THIS COLLECTION
            print(f"  Deleting all embeddings in {name}...")
            await conn.execute(text("DELETE FROM langchain_pg_embedding WHERE collection_id = :id"), {"id": uuid})
        
        await conn.commit()
        print("\nAll embeddings purged from all collections.")

if __name__ == "__main__":
    asyncio.run(scorched_earth())
