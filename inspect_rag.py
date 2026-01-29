import asyncio
import os
from orchestrator.rag_workflow import rag_workflow

async def inspect():
    query = "Check the 'Equipment_Inventory' Excel file. For the item marked as 'Needs Service,' what are the 'Emergency Response Protocols' we must follow if it fails during a power outage, and who should we contact according to the 'Financial Assistance Contact Directory' if the repair costs exceed our quarterly budget?"
    inputs = {"query": query, "messages": []}
    
    print("Running workflow...")
    result = await rag_workflow.ainvoke(inputs, config={"configurable": {"thread_id": "inspect_sess"}})
    
    print("\n--- REWRITTEN QUERIES ---")
    for q in result.get("rewritten_queries", []):
        print(f"- {q}")
        
    print("\n--- CONTEXT CHUNKS ---")
    for i, chunk in enumerate(result.get("context", [])):
        print(f"\n[CHUNK {i}] (Source: Unknown)")
        print(chunk)
        
    print("\n--- FINAL ANSWER ---")
    print(result.get("answer"))

if __name__ == "__main__":
    asyncio.run(inspect())
