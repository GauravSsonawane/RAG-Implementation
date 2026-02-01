import asyncio
import os
from sqlalchemy import select, delete, text
from storage.database import get_db, engine
from storage.models import Session, DocumentMetadata
from knowledge_base.ingest import COLLECTION_NAME

async def reset_demo():
    print("--- STARTING DEMO RESET ---")
    async for db in get_db():
        try:
            # 1. CLEANUP SESSION DOCUMENTS
            print("\n1. Cleaning up Session Documents...")
            stmt = select(DocumentMetadata).where(DocumentMetadata.session_id.isnot(None))
            result = await db.execute(stmt)
            session_docs = result.scalars().all()
            
            if not session_docs:
                print("   No session documents found.")
            
            for doc in session_docs:
                print(f"   Deleting {doc.filename} (Session: {doc.session_id})...")
                
                # Delete Vectors
                try:
                    delete_stmt = text(f"""
                        DELETE FROM langchain_pg_embedding 
                        WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = :coll LIMIT 1)
                        AND cmetadata->>'session_id' = :session_id
                    """)
                    await db.execute(delete_stmt, {"coll": COLLECTION_NAME, "session_id": doc.session_id})
                except Exception as e:
                    print(f"   [Warning] Vector delete failed: {e}")

                # Delete Physical File
                try:
                    if doc.file_path and os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                        print(f"   Removed file: {doc.file_path}")
                except Exception as e:
                    print(f"   [Warning] File remove failed: {e}")
                
                # Delete Metadata
                await db.delete(doc)
            
            # 2. DELETE ALL SESSIONS (Cascades to ChatMessages)
            print("\n2. Wiping Chat History (Sessions)...")
            await db.execute(delete(Session))
            
            await db.commit()
            print("\n--- RESET COMPLETE: System is clean for demo! ---")
            
        except Exception as e:
            print(f"ERROR: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_demo())
