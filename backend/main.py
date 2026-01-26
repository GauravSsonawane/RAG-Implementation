from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chat, upload, session
from sqlalchemy.ext.asyncio import AsyncSession
from storage.database import get_db

app = FastAPI(title="Industrial RAG Backend")

# Allow frontend (React) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(session.router, prefix="/session", tags=["Session"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/verify")
async def verify_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """Verify system files and citation generation.
    Returns JSON indicating whether system docs are present and a test query yields a citation.
    """
    # Step 1: Check system files
    from sqlalchemy import select
    from storage.models import DocumentMetadata
    
    SYSTEM_DOCS = [
        "01_Customer_FAQ_Guide.pdf",
        "02_New_Meter_Application_Process.pdf",
        "03_Billing_Dispute_Resolution_Procedure.pdf",
        "04_Emergency_Response_Protocol.pdf",
        "05_Payment_Plans_Financial_Assistance.pdf"
    ]
    
    result = await db.execute(select(DocumentMetadata))
    docs = result.scalars().all()
    
    files = []
    for doc in docs:
        category = "system" if doc.filename in SYSTEM_DOCS else "session"
        files.append({
            "name": doc.filename,
            "status": doc.status,
            "id": doc.id,
            "category": category
        })
    
    system_files = [f for f in files if f.get("category") == "system"]
    files_ok = len(system_files) == 5
    
    # Step 2: Test RAG retrieval for citation
    citation_ok = False
    try:
        from langchain_postgres.vectorstores import PGVector
        from orchestrator.rag_workflow import embeddings, CONNECTION_STRING, COLLECTION_NAME
        
        # Initialize vector store directly
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=CONNECTION_STRING,
            use_jsonb=True,
        )
        
        # Search for a sample query
        docs = vector_store.similarity_search("What is the meter application process?", k=1)
        
        # If we find documents, the RAG retrieval is working!
        citation_ok = len(docs) > 0
    except Exception as e:
        print(f"Citation test (direct search) failed: {e}")
        citation_ok = False
        
    return {"files_ok": files_ok, "citation_ok": citation_ok, "system_files_count": len(system_files)}
