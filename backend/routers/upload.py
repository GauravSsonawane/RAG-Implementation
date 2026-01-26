from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from storage.database import get_db
from storage.models import DocumentMetadata
from knowledge_base.ingest import process_document
import os
import shutil

router = APIRouter()

class UploadResponse(BaseModel):
    document_id: str
    message: str = "File uploaded successfully"

@router.post("/", response_model=UploadResponse)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    upload_dir = "knowledge_base/documents"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create metadata entry
    new_doc = DocumentMetadata(
        filename=file.filename,
        file_path=file_path,
        status="processing"
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Queue background ingestion
    background_tasks.add_task(process_document, file.filename, file_path)
    
    return UploadResponse(document_id=new_doc.id, message=f"File {file.filename} uploaded and queued for processing.")

@router.get("/list")
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
        
    return files

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
        
    # 3. Remove from DB
    await db.execute(delete(DocumentMetadata).where(DocumentMetadata.id == doc.id))
    await db.commit()
    
    return {"message": f"File {filename} deleted successfully", "status": "success"}

