from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from storage.database import get_db
from storage.models import Session as SessionModel
from typing import List, Optional

router = APIRouter()

class SessionInfo(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/create", response_model=SessionInfo)
async def create_session(info: SessionInfo, db: AsyncSession = Depends(get_db)):
    new_session = SessionModel(
        id=info.session_id,
        user_id=info.user_id,
        metadata_json=info.metadata
    )
    db.add(new_session)
    await db.commit()
    return info

@router.get("/list", response_model=List[SessionInfo])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    stmt = select(SessionModel)
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        SessionInfo(
            session_id=s.id,
            user_id=s.user_id,
            metadata=s.metadata_json
        ) for s in sessions
    ]

