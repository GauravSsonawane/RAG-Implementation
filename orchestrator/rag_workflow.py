import os
import asyncio
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
    rewritten_queries: List[str]
    context: List[str]
    sources: List[str]
    answer: str
    model_name: str
    model_name: str

# Config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5434")

# Prioritize DATABASE_URL if in Docker
CONNECTION_STRING = os.getenv("DATABASE_URL")
if not CONNECTION_STRING:
    CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

COLLECTION_NAME = "industrial_docs"

embeddings = OllamaEmbeddings(
    model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest"),
    base_url=OLLAMA_URL
)

# # llm = get_llm() # Moved to inside nodes for dynamic model selection
 # Moved to inside nodes for dynamic model selection

# Node 1: Query Rewriter
async def rewrite_query(state: AgentState):
    print("---DECOMPOSING QUERY INTO MULTIPLE SEARCHES---")
    query = state["query"]
    messages = state.get("messages", [])
    
    prompt = ChatPromptTemplate.from_template(
        "You are an expert search query generator. Decompose the user query into 1-3 **standalone** search queries. "
        "Each sub-query must focus on only **ONE** specific topic or document type mentioned. "
        "Do NOT combine topics in a single sub-query (e.g., do not combine 'equipment status' with 'billing policy'). "
        "Keep them simple and keyword-rich for a vector search. "
        "\n\nContext History (if any): {history}\n\nUser Query: {query}"
        "\n\nOutput ONLY a list of queries, one per line. No numbers, no extra text."
    )
    
    history_text = "\n".join([f"{m.type}: {m.content}" for m in messages[-3:]]) if messages else "No history"
    
    # Dynamic LLM
    model_name = state.get("model_name")
    local_llm = get_llm(model_name)
    
    chain = prompt | local_llm
    response = await chain.ainvoke({"history": history_text, "query": query})
    
    # Simple splitting by newline or comma
    raw_queries = response.content.split("\n")
    queries = [q.strip().strip(",").strip('"') for q in raw_queries if q.strip()]
    
    # Fallback to original query if something goes wrong
    if not queries:
        queries = [query]
    
    print(f"Generated {len(queries)} sub-queries: {queries}")
    return {"rewritten_queries": queries}

# Node 2: Retriever
async def retrieve(state: AgentState):
    print("---RETRIEVING DOCUMENTS (MULTI-QUERY DUAL RETRIEVAL)---")
    queries = state.get("rewritten_queries", [state["query"]])
    
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )
    
    SYSTEM_DOCS = [
        "01_Customer_FAQ_Guide.pdf",
        "02_New_Meter_Application_Process.pdf",
        "03_Billing_Dispute_Resolution_Procedure.pdf",
        "04_Emergency_Response_Protocol.pdf",
        "05_Payment_Plans_Financial_Assistance.pdf"
    ]
    
    all_query_results = []
    
    # Run searches for each sub-query
    for q in queries:
        print(f"Searching for sub-query: {q}")
        # Search KB - Use k=5 per query for better coverage
        system_filter = {"source": {"$in": SYSTEM_DOCS}}
        docs_system = await asyncio.to_thread(vector_store.similarity_search, q, k=5, filter=system_filter)
        
        # Search Session - Use k=5 per query
        session_filter = {"source": {"$nin": SYSTEM_DOCS}}
        docs_session = await asyncio.to_thread(vector_store.similarity_search, q, k=5, filter=session_filter)
        
        all_query_results.append(docs_system + docs_session)
    
    # FAIR MERGE: Interleave results from each query so all topics are represented early
    merged_docs = []
    max_results = max(len(res) for res in all_query_results) if all_query_results else 0
    for i in range(max_results):
        for query_res in all_query_results:
            if i < len(query_res):
                merged_docs.append(query_res[i])
    
    # Deduplicate by content to avoid redundancy
    unique_docs = []
    seen_content = set()
    for doc in merged_docs:
        if doc.page_content not in seen_content:
            unique_docs.append(doc)
            seen_content.add(doc.page_content)
    
    # FINAL CAP: Ensure we don't overwhelm the 3B model (limit to top 12 chunks total)
    final_docs = unique_docs[:12]
    
    context = [doc.page_content for doc in final_docs]
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in final_docs]))
    
    print(f"Retrieved {len(final_docs)} unique chunks from {len(sources)} sources across {len(queries)} queries.")
    return {"context": context, "sources": sources}

# Node 3: Answer Generator
async def generate_answer(state: AgentState):
    print("---GENERATING ANSWER---")
    query = state["query"]
    context = "\n\n".join(state["context"])
    messages = state.get("messages", [])
    
    # History-aware prompt
    if messages:
        prompt = ChatPromptTemplate.from_template(
            "You are an intelligent industrial assistant. You have been provided with RELEVANT CONTEXT from the company's knowledge base and user-uploaded files. "
            "The Context below contains the actual CONTENT of the files the user is asking about. "
            "INSTRUCTIONS:\n"
            "1. Answer strictly based on the provided Context.\n"
            "2. **Format your answer using clear Markdown**: Use **Bold** for key terms, `Code` for specific values, and **Lists** for steps.\n"
            "3. Use **Tables** only when comparing complex data; otherwise prefer bullet points for readability.\n"
            "4. If the user asks about a specific file, confirm you found it in the context.\n"
            "5. Maintain conversational continuity.\n"
            "\n\nChat History: {history}\n\nContext: {context}\n\nUser Query: {query}"
        )
        history_text = "\n".join([f"{m.type}: {m.content}" for m in messages[-10:]]) # Last 10 messages for context
        
        # Dynamic LLM
        model_name = state.get("model_name")
        local_llm = get_llm(model_name)
        
        chain = prompt | local_llm
        response = await chain.ainvoke({"history": history_text, "context": context, "query": query})
    else:
        prompt = ChatPromptTemplate.from_template(
            "You are an intelligent industrial assistant. You have been provided with RELEVANT CONTEXT from the company's knowledge base and user-uploaded files. "
            "The Context below contains the actual CONTENT of the files the user is asking about. "
            "INSTRUCTIONS:\n"
            "1. Answer strictly based on the provided Context.\n"
            "2. **Format your answer using clear Markdown**: Use **Bold** for key terms, `Code` for specific values, and **Lists** for steps.\n"
            "3. Use **Tables** only when comparing complex data; otherwise prefer bullet points for readability.\n"
            "4. If the user asks about a specific file, confirm you found it in the context.\n"
            "\n\nContext: {context}\n\nUser Query: {query}"
        )
        # Dynamic LLM
        model_name = state.get("model_name")
        local_llm = get_llm(model_name)
        
        chain = prompt | local_llm
        response = await chain.ainvoke({"context": context, "query": query})
    
    return {"answer": response.content}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("rewrite_query", rewrite_query)
builder.add_node("retrieve", retrieve)
builder.add_node("generate_answer", generate_answer)

builder.add_edge(START, "rewrite_query")
builder.add_edge("rewrite_query", "retrieve")
builder.add_edge("retrieve", "generate_answer")
builder.add_edge("generate_answer", END)

rag_workflow = builder.compile()


