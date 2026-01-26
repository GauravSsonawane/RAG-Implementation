import os
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
COLLECTION_NAME = "industrial_docs"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest",
    base_url=OLLAMA_URL
)

def test_search():
    print(f"Connecting to: {CONNECTION_STRING}")
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )
    
    query = "What is the meter application process?"
    print(f"Searching for: {query}")
    docs = vector_store.similarity_search(query, k=1)
    
    print(f"Found {len(docs)} documents.")
    for doc in docs:
        print(f"Content: {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}")

if __name__ == "__main__":
    test_search()
