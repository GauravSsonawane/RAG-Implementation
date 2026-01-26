import os
import asyncio
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import select, update
from storage.database import AsyncSessionLocal, engine
from storage.models import DocumentMetadata
import uuid
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Point to the host port we mapped
CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5433/{POSTGRES_DB}"
COLLECTION_NAME = "industrial_docs"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest", 
    base_url="http://localhost:11434"
)

async def ingest_pdfs():
    doc_dir = "knowledge_base/documents"
    if not os.path.exists(doc_dir):
        print(f"Directory {doc_dir} not found.")
        return

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )

    pdf_files = [f for f in os.listdir(doc_dir) if f.endswith(".pdf")]
    
    for pdf_file in pdf_files:
        file_path = os.path.join(doc_dir, pdf_file)
        
        async with AsyncSessionLocal() as session:
            # Check if already processed
            stmt = select(DocumentMetadata).where(DocumentMetadata.filename == pdf_file)
            result = await session.execute(stmt)
            meta = result.scalar_one_or_none()
            
            if meta and meta.status == "processed":
                print(f"Skipping {pdf_file}, already processed.")
                continue
            
            if not meta:
                meta = DocumentMetadata(
                    filename=pdf_file,
                    file_path=file_path,
                    status="processing"
                )
                session.add(meta)
                await session.commit()
            
            print(f"Processing {pdf_file}...")
            
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)
                print(f"Created {len(splits)} splits for {pdf_file}")
                
                # Add to vector store (using synchronous method for reliability)
                vector_store.add_documents(splits)
                
                # Update status
                meta.status = "processed"
                await session.merge(meta) # Use merge to ensure it updates the session's object
                await session.commit()
                print(f"Successfully processed {pdf_file}")

                
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
                meta.status = "error"
                await session.commit()

if __name__ == "__main__":
    asyncio.run(ingest_pdfs())
