import asyncio
import os
from dotenv import load_dotenv
from orchestrator.rag_workflow import rag_workflow
from langchain_core.messages import HumanMessage

load_dotenv()

async def test_retrieval():
    print("🔍 Testing RAG Retrieval...")
    inputs = {
        "query": "What documents are in the knowledge base?",
        "messages": []
    }
    config = {"configurable": {"thread_id": "test_session"}}
    
    try:
        result = await rag_workflow.ainvoke(inputs, config=config)
        print(f"✅ Answer: {result.get('answer')[:100]}...")
        print(f"✅ Sources: {result.get('sources')}")
        
        if not result.get('sources'):
            print("❌ No sources found!")
        else:
            print(f"🎉 Found {len(result['sources'])} sources.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
