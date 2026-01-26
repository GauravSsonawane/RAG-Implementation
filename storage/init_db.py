from .database import engine, Base
import asyncio
from .models import Session, ChatMessage, DocumentMetadata

async def init_db():
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with Base
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created.")

if __name__ == "__main__":
    asyncio.run(init_db())
