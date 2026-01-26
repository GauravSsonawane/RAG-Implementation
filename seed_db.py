import asyncio
import os
from storage.database import AsyncSessionLocal
from storage.models import DocumentMetadata
from sqlalchemy import select

SYSTEM_DOCS = [
    "01_Customer_FAQ_Guide.pdf",
    "02_New_Meter_Application_Process.pdf",
    "03_Billing_Dispute_Resolution_Procedure.pdf",
    "04_Emergency_Response_Protocol.pdf",
    "05_Payment_Plans_Financial_Assistance.pdf"
]

async def seed_db():
    print("🌱 Seeding System Docs into Metadata DB...")
    
    async with AsyncSessionLocal() as session:
        for filename in SYSTEM_DOCS:
            # Check exist
            result = await session.execute(select(DocumentMetadata).where(DocumentMetadata.filename == filename))
            existing = result.scalar_one_or_none()
            
            if not existing:
                print(f"Adding: {filename}")
                new_doc = DocumentMetadata(
                    filename=filename,
                    file_path=f"knowledge_base/documents/{filename}", # Placeholder path
                    status="processed"
                )
                session.add(new_doc)
            else:
                print(f"Skipping: {filename} (Already exists)")
                
        await session.commit()
        print("✅ Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed_db())
