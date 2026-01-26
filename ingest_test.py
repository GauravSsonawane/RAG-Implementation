import os
from langchain_core.documents import Document
from langchain_postgres.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")

CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
COLLECTION_NAME = "test_collection"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest",
    base_url=OLLAMA_URL
)

def test_ingest():
    print("Testing minimal ingest...")
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )
    
    doc = Document(page_content="This is a test document about meter application.", metadata={"source": "test.pdf"})
    print("Adding document...")
    vector_store.add_documents([doc])
    print("Done adding. Now searching...")
    
    results = vector_store.similarity_search("meter application", k=1)
    print(f"Results: {len(results)}")
    if len(results) > 0:
        print(f"Content: {results[0].page_content}")

if __name__ == "__main__":
    test_ingest()
