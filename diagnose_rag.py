import asyncio
import os
from orchestrator.rag_workflow import rag_workflow
from langchain_core.messages import HumanMessage

async def diagnose():
    query = "Check the 'Equipment_Inventory' Excel file. For the item marked as 'Needs Service,' what are the 'Emergency Response Protocols' we must follow if it fails during a power outage, and who should we contact according to the 'Financial Assistance Contact Directory' if the repair costs exceed our quarterly budget?"
    inputs = {"query": query, "messages": []}
    config = {"configurable": {"thread_id": "diag_test"}}
    
    # Run the workflow and capture state
    result = await rag_workflow.ainvoke(inputs, config=config)
    
    print("\n=== DIAGNOSTIC RESULTS ===")
    print(f"Generated Queries: {result.get('rewritten_queries')}")
    print(f"Retrieved Sources: {result.get('sources')}")
    print(f"Answer Sample: {result.get('answer')[:200]}...")

if __name__ == "__main__":
    asyncio.run(diagnose())
