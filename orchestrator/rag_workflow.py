import os
from typing import Annotated, List, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_postgres.vectorstores import PGVector
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from orchestrator.llm_client import get_llm
from langchain_ollama import OllamaEmbeddings
import operator
from dotenv import load_dotenv

load_dotenv()

# State definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    rewritten_query: str
    context: List[str]
    sources: List[str]
    answer: str

# Config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")

# Prioritize DATABASE_URL if in Docker
CONNECTION_STRING = os.getenv("DATABASE_URL")
if not CONNECTION_STRING:
    CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

COLLECTION_NAME = "industrial_docs"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest",
    base_url=OLLAMA_URL
)

llm = get_llm()

# Node 1: Query Rewriter
async def rewrite_query(state: AgentState):
    print("---REWRITING QUERY---")
    query = state["query"]
    
    # Simple rewrite prompt
    prompt = ChatPromptTemplate.from_template(
        "Rewrite the following user query to be more descriptive and suitable for a vector search. "
        "User query: {query}"
    )
    chain = prompt | llm
    response = await chain.ainvoke({"query": query})
    
    return {"rewritten_query": response.content}

# Node 2: Retriever
async def retrieve(state: AgentState):
    print("---RETRIEVING DOCUMENTS---")
    query = state["query"]
    
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )
    
    docs = vector_store.similarity_search(query, k=5)
    # Store both content and source metadata
    context = [doc.page_content for doc in docs]
    sources = [doc.metadata.get("source", "Unknown") for doc in docs]
    
    return {"context": context, "sources": sources}

# Node 3: Answer Generator
async def generate_answer(state: AgentState):
    print("---GENERATING ANSWER---")
    query = state["query"]
    context = "\n\n".join(state["context"])
    
    prompt = ChatPromptTemplate.from_template(
        "You are an industrial assistant. Use the following context to answer the user query accurately. "
        "If the context doesn't contain the answer, say you don't know based on the provided documents. "
        "\n\nContext: {context}\n\nUser Query: {query}"
    )
    chain = prompt | llm
    response = await chain.ainvoke({"context": context, "query": query})
    
    return {"answer": response.content}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("retrieve", retrieve)
builder.add_node("generate_answer", generate_answer)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate_answer")
builder.add_edge("generate_answer", END)

rag_workflow = builder.compile()
