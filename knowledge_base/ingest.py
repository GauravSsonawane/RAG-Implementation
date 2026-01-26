import os
import asyncio
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader, 
    CSVLoader,
    UnstructuredExcelLoader
)
from langchain_core.documents import Document
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

def get_loader(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    print(f"Selecting loader for extension: {ext} ({file_path})")
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext in [".docx", ".doc"]:
        return Docx2txtLoader(file_path)
    elif ext in [".csv", ".xlsx", ".xls"]:
        import pandas as pd
        class PandasLoader:
            def __init__(self, path):
                self.path = path
            def load(self):
                try:
                    if self.path.endswith(".csv"):
                        df = pd.read_csv(self.path)
                    else:
                        # Explicitly use openpyxl for xlsx to avoid dependency issues
                        engine = 'openpyxl' if self.path.endswith(".xlsx") else None
                        df = pd.read_excel(self.path, engine=engine)
                    
                    df = df.fillna("") # Handle missing values gracefully
                    
                    documents = []
                    current_chunk = []
                    current_length = 0
                    
                    for _, row in df.iterrows():
                        # Format row as column-value pairs for better semantic meaning
                        row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                        
                        # Add to current chunk if it fits, else start a new one
                        if current_length + len(row_text) > 800 and current_chunk:
                            documents.append(Document(
                                page_content="\n".join(current_chunk),
                                metadata={"source": os.path.basename(self.path)}
                            ))
                            current_chunk = [row_text]
                            current_length = len(row_text)
                        else:
                            current_chunk.append(row_text)
                            current_length += len(row_text)
                    
                    if current_chunk:
                        documents.append(Document(
                            page_content="\n".join(current_chunk),
                            metadata={"source": os.path.basename(self.path)}
                        ))
                        
                    print(f"Tabular loader created {len(documents)} document objects for {self.path}")
                    return documents
                except Exception as e:
                    print(f"Error in PandasLoader for {self.path}: {e}")
                    raise e
        return PandasLoader(file_path)
    elif ext in [".txt", ".md"]:
        class RobustTextLoader:
            def __init__(self, path):
                self.path = path
            def load(self):
                encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
                for enc in encodings:
                    try:
                        loader = TextLoader(self.path, encoding=enc)
                        return loader.load()
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Could not decode {self.path} with common encodings.")
        return RobustTextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

async def process_document(pdf_file: str, file_path: str):
    """Processes a single document: splits text, embeds, and saves to PGVector."""
    print(f"Starting process_document for: {pdf_file}")
    async with AsyncSessionLocal() as session:
        # Check if already processed
        stmt = select(DocumentMetadata).where(DocumentMetadata.filename == pdf_file)
        result = await session.execute(stmt)
        meta = result.scalar_one_or_none()
        
        if meta and meta.status == "processed":
            print(f"Skipping {pdf_file}, already processed.")
            return

        if not meta:
            print(f"Creating new metadata for {pdf_file}")
            meta = DocumentMetadata(
                filename=pdf_file,
                file_path=file_path,
                status="processing"
            )
            session.add(meta)
            await session.commit()
        
        print(f"Processing {pdf_file}...")
        
        try:
            loader = get_loader(file_path)
            print(f"Loading document with {loader.__class__.__name__}...")
            docs = await asyncio.to_thread(loader.load)
            print(f"Loaded {len(docs)} document objects.")
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = await asyncio.to_thread(text_splitter.split_documents, docs)
            
            # Ensure consistent metadata for deletion and search
            for split in splits:
                split.metadata["source"] = pdf_file
                # Prepend source filename to content to aid retrieval
                split.page_content = f"--- Document: {pdf_file} ---\n{split.page_content}"
                
            print(f"Created {len(splits)} splits for {pdf_file}")
            
            def add_to_vectorstore():
                print(f"Connecting to vector store for {pdf_file}...")
                vector_store = PGVector(
                    embeddings=embeddings,
                    collection_name=COLLECTION_NAME,
                    connection=CONNECTION_STRING,
                    use_jsonb=True,
                )
                
                # Add to vector store in batches to avoid overwhelming the system
                batch_size = 50
                for i in range(0, len(splits), batch_size):
                    batch = splits[i:i+batch_size]
                    print(f"Adding batch {i//batch_size + 1}/{(len(splits)-1)//batch_size + 1} ({len(batch)} splits) for {pdf_file}...")
                    vector_store.add_documents(batch)
                
            print(f"Starting vector store ingestion for {pdf_file}...")
            await asyncio.to_thread(add_to_vectorstore)
            print(f"Successfully added {pdf_file} to vector store.")
            
            # Update status
            meta.status = "processed"
            await session.merge(meta)
            await session.commit()
            print(f"Successfully updated status for {pdf_file}")
            
        except Exception as e:
            print(f"!!! Error processing {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
            meta.status = "error"
            await session.merge(meta)
            await session.commit()

async def ingest_pdfs():
    doc_dir = "knowledge_base/documents"
    if not os.path.exists(doc_dir):
        print(f"Directory {doc_dir} not found.")
        return

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".xls"}
    pdf_files = [f for f in os.listdir(doc_dir) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
    
    for pdf_file in pdf_files:
        file_path = os.path.join(doc_dir, pdf_file)
        await process_document(pdf_file, file_path)

if __name__ == "__main__":
    asyncio.run(ingest_pdfs())
