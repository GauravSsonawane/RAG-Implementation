from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from storage.database import get_db
from storage.models import DocumentMetadata
from knowledge_base.ingest import process_document, embeddings, CONNECTION_STRING, COLLECTION_NAME
from langchain_postgres.vectorstores import PGVector
import os
import shutil

router = APIRouter()

class UploadResponse(BaseModel):
    document_id: str
    message: str = "File uploaded successfully"

class FileInfo(BaseModel):
    name: str
    status: str
    id: str
    category: str

@router.post("/", response_model=UploadResponse)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), session_id: str = Form(None), db: AsyncSession = Depends(get_db)):
    upload_dir = "knowledge_base/documents"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Check if duplicate exists (for this session if provided, or global)
    from sqlalchemy import select
    stmt = select(DocumentMetadata).where(DocumentMetadata.filename == file.filename)
    # Note: We technically allow same filename in different sessions now, but keeping simple for now
    result = await db.execute(stmt)
    existing_doc = result.scalar_one_or_none()
    
    if existing_doc:
        existing_doc.status = "processing"
        existing_doc.file_path = file_path
        existing_doc.session_id = session_id # Update session ID
        doc_id = existing_doc.id
    else:
        # Create metadata entry
        new_doc = DocumentMetadata(
            filename=file.filename,
            file_path=file_path,
            status="processing",
            session_id=session_id
        )
        db.add(new_doc)
        await db.flush() # Get ID
        doc_id = new_doc.id
    
    await db.commit()
    
    # Queue background ingestion
    background_tasks.add_task(process_document, file.filename, file_path, session_id)
    
    return UploadResponse(document_id=doc_id, message=f"File {file.filename} uploaded and queued for processing.")

@router.get("/list", response_model=List[FileInfo])
async def get_files(db: AsyncSession = Depends(get_db)):
    """Get all files with category split"""
    from sqlalchemy import select
    result = await db.execute(select(DocumentMetadata))
    docs = result.scalars().all()
    
    SYSTEM_DOCS = [
        "01_Customer_FAQ_Guide.pdf",
        "02_New_Meter_Application_Process.pdf",
        "03_Billing_Dispute_Resolution_Procedure.pdf",
        "04_Emergency_Response_Protocol.pdf",
        "05_Payment_Plans_Financial_Assistance.pdf"
    ]
    
    files = []
    for doc in docs:
        category = "system" if doc.filename in SYSTEM_DOCS else "session"
        files.append({
            "name": doc.filename,
            "status": doc.status,
            "id": doc.id,
            "category": category
        })
        
    return [FileInfo(**f) for f in files]

@router.delete("/{filename}")
async def delete_file(filename: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, delete
    
    # 1. Find the file in DB
    stmt = select(DocumentMetadata).where(DocumentMetadata.filename == filename)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    
    if not doc:
        return {"message": "File not found in database", "status": "error"}
        
    # 2. Try to remove the physical file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        print(f"Error removing physical file: {e}")
        # Continue to remove from DB even if file is already gone
        
    # 3. Clean up associated vectors in PGVector
    print(f"Purging vectors for: {filename} in collection: {COLLECTION_NAME}")
    try:
        from sqlalchemy import text
        # Using the existing session 'db' to perform the delete.
        # This ensures it's part of the same transaction as the metadata delete.
        delete_stmt = text(f"""
            DELETE FROM langchain_pg_embedding 
            WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = :coll LIMIT 1)
            AND cmetadata->>'source' = :filename
        """)
        res = await db.execute(delete_stmt, {"coll": COLLECTION_NAME, "filename": filename})
        print(f"Successfully deleted {res.rowcount} vectors for {filename}")
    except Exception as e:
        print(f"Error deleting vectors from PGVector: {e}")
        import traceback
        traceback.print_exc()

    # 4. Remove from Metadata DB
    await db.execute(delete(DocumentMetadata).where(DocumentMetadata.id == doc.id))
    await db.commit()
    print(f"Committed deletion for {filename}")
    
    return {"message": f"File {filename} deleted successfully", "status": "success"}

@router.delete("/session/{session_id}/files")
async def delete_session_files(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete all files and vectors associated with a session."""
    from sqlalchemy import select, delete
    
    # 1. Find all files for this session
    stmt = select(DocumentMetadata).where(DocumentMetadata.session_id == session_id)
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    if not docs:
        return {"message": "No files found for this session", "count": 0}
        
    deleted_count = 0
    for doc in docs:
        # 2. Try to remove physical file
        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception as e:
            print(f"Error removing physical file {doc.filename}: {e}")
            
        # 3. Clean up associated vectors in PGVector
        try:
            from sqlalchemy import text
            # Delete vectors where session_id matches
            # Note: ingested metadata stores session_id
            delete_stmt = text(f"""
                DELETE FROM langchain_pg_embedding 
                WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = :coll LIMIT 1)
                AND cmetadata->>'session_id' = :session_id
            """)
            await db.execute(delete_stmt, {"coll": COLLECTION_NAME, "session_id": session_id})
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            
        deleted_count += 1
        
    # 4. Remove from Metadata DB (Bulk delete)
    await db.execute(delete(DocumentMetadata).where(DocumentMetadata.session_id == session_id))
    await db.commit()
    
    return {"message": f"Deleted {deleted_count} files for session {session_id}", "count": deleted_count}

