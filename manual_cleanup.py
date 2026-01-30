import asyncio
from storage.database import get_db
from sqlalchemy import text, delete, select
from storage.models import DocumentMetadata
import os

async def cleanup_file(filename):
    print(f"Cleaning up {filename}...")
    async for db in get_db():
        # 1. Remove from PGVector
        try:
            delete_stmt = text(f"""
                DELETE FROM langchain_pg_embedding 
                WHERE cmetadata->>'source' = :filename
            """)
            result = await db.execute(delete_stmt, {"filename": filename})
            print(f"Deleted {result.rowcount} vectors.")
        except Exception as e:
            print(f"Vector delete error: {e}")

        # 2. Remove from Metadata
        try:
            stmt = select(DocumentMetadata).where(DocumentMetadata.filename == filename)
            result = await db.execute(stmt)
            doc = result.scalar_one_or_none()
            if doc:
                await db.delete(doc)
                print("Deleted metadata record.")
            else:
                print("No metadata found.")
        except Exception as e:
            print(f"Metadata delete error: {e}")
            
        await db.commit()

    # 3. Remove physical file
    try:
        path = f"knowledge_base/documents/{filename}"
        if os.path.exists(path):
            os.remove(path)
            print("Physical file removed.")
        else:
            print("Physical file not found.")
    except Exception as e:
        print(f"File remove error: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup_file("DeepSeek_V3.pdf"))
