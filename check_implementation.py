#!/usr/bin/env python
"""
Quick verification that all code changes are in place
"""
import os
import sys

def check_file_contains(filepath, search_string, description):
    """Check if a file contains a specific string"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - NOT FOUND")
                return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    print("\nVerifying Implementation...\n")
    
    checks = [
        (
            r"c:\RAG Implementation\orchestrator\rag_workflow.py",
            "sources: List[str]",
            "RAG Workflow - sources field in AgentState"
        ),
        (
            r"c:\RAG Implementation\orchestrator\rag_workflow.py",
            'sources = [doc.metadata.get("source"',
            "RAG Workflow - source extraction from documents"
        ),
        (
            r"c:\RAG Implementation\backend\routers\chat.py",
            'sources = result.get("sources"',
            "Chat API - returns sources from workflow"
        ),
        (
            r"c:\RAG Implementation\frontend\src\components\ChatInterface.jsx",
            "sources: data.sources",
            "Frontend - captures sources from API"
        ),
        (
            r"c:\RAG Implementation\frontend\src\components\ChatInterface.jsx",
            "msg.sources && msg.sources.length > 0",
            "Frontend - renders citation badges"
        ),
        (
            r"c:\RAG Implementation\backend\main.py",
            "@app.get(\"/verify\")",
            "Backend - /verify endpoint exists"
        ),
        (
            r"c:\RAG Implementation\frontend\verify.js",
            "fetch('http://localhost:8002/verify')",
            "Frontend - verify.js script"
        ),
        (
            r"c:\RAG Implementation\frontend\package.json",
            '"verify": "node verify.js"',
            "Frontend - npm verify command"
        )
    ]
    
    passed = 0
    for filepath, search_string, description in checks:
        if check_file_contains(filepath, search_string, description):
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(checks)} checks passed\n")
    
    if passed == len(checks):
        print("✅ All implementation checks PASSED!")
        print("\n📋 Next Steps:")
        print("1. Restart backend: Ctrl+C then run:")
        print("   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload")
        print("\n2. Test verification:")
        print("   cd frontend && npm run verify")
        print("\n3. Test citations in UI:")
        print("   Open http://localhost:5173 and ask a question")
        return 0
    else:
        print("❌ Some checks failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
