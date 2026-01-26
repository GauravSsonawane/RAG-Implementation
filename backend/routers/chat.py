from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from storage.database import get_db
from storage.models import ChatMessage as MessageModel
from orchestrator.rag_workflow import rag_workflow
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 1. Ensure Session exists (Lazy initialization)
    from sqlalchemy import select
    from storage.models import Session as SessionModel
    
    stmt = select(SessionModel).where(SessionModel.id == request.session_id)
    result = await db.execute(stmt)
    session_exists = result.scalar_one_or_none()
    
    if not session_exists:
        new_session = SessionModel(id=request.session_id)
        db.add(new_session)
        await db.flush() # Flush to ensure ID is available for FK without committing the whole transaction yet
    
    # 2. Prepare history for LangGraph if needed (or just use the last message)
    last_user_message = request.messages[-1].content
    
    # 3. Run LangGraph workflow
    try:
        inputs = {"query": last_user_message, "messages": []}
        config = {"configurable": {"thread_id": request.session_id}}
        
        result = await rag_workflow.ainvoke(inputs, config=config)
        
        answer = result.get("answer", "I'm sorry, I couldn't generate an answer.")
        sources = result.get("sources", [])  # Get actual sources from workflow
        
        # 4. Store messages in DB
        user_msg = MessageModel(session_id=request.session_id, role="user", content=last_user_message)
        ai_msg = MessageModel(session_id=request.session_id, role="assistant", content=answer)
        
        db.add(user_msg)
        db.add(ai_msg)
        await db.commit()
        
        return ChatResponse(answer=answer, sources=sources)
        
    except Exception as e:
        print(f"Error in chat workflow: {e}")
        await db.rollback() # Rollback on error
        raise HTTPException(status_code=500, detail=str(e))

