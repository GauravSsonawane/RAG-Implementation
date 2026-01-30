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
    print(f"DEBUG: Received chat request for session {request.session_id}")
    # 1. Ensure Session exists (Lazy initialization)
    from sqlalchemy import select
    from storage.models import Session as SessionModel
    
    stmt = select(SessionModel).where(SessionModel.id == request.session_id)
    print("DEBUG: Executing session check query")
    result = await db.execute(stmt)
    session_exists = result.scalar_one_or_none()
    print(f"DEBUG: Session exists: {session_exists is not None}")
    
    if not session_exists:
        new_session = SessionModel(id=request.session_id)
        db.add(new_session)
        await db.flush() # Flush to ensure ID is available for FK without committing the whole transaction yet
    
    # 2. Fetch Chat History from DB for context
    stmt = select(MessageModel).where(MessageModel.session_id == request.session_id).order_by(MessageModel.created_at.asc())
    print("DEBUG: Fetching chat history")
    history_result = await db.execute(stmt)
    print("DEBUG: History fetched")
    history_messages = history_result.scalars().all()
    
    # Convert DB messages to LangChain format (limit to last 10 for context window)
    langchain_history = []
    for m in history_messages[-10:]:
        if m.role == "user":
            langchain_history.append(HumanMessage(content=m.content))
        else:
            langchain_history.append(AIMessage(content=m.content))
    
    # 3. Prepare latest query
    last_user_message = request.messages[-1].content
    
    # 4. Run LangGraph workflow with history
    try:
        inputs = {
            "query": last_user_message, 
            "messages": langchain_history
        }
        config = {"configurable": {"thread_id": request.session_id}}
        
        print(f"Workflow Start Session: {request.session_id}")
        result = await rag_workflow.ainvoke(inputs, config=config)
        print("Workflow End")
        
        answer = result.get("answer", "I'm sorry, I couldn't generate an answer.")
        sources = result.get("sources", [])
        
        # 5. Store new messages in DB
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

@router.get("/{session_id}/history", response_model=List[ChatMessage])
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(MessageModel).where(MessageModel.session_id == session_id).order_by(MessageModel.created_at.asc())
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return [ChatMessage(role=m.role, content=m.content) for m in messages]

