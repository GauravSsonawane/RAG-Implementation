from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from storage.database import get_db
from storage.models import DocumentMetadata
import os
import shutil

router = APIRouter()

class UploadResponse(BaseModel):
    document_id: str
    message: str = "File uploaded successfully"

@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
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
    
    # For now, we return success and processing status. 
    # In a production app, we'd trigger a background task (e.g. Celery) 
    # for ingestion/embedding. 
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

