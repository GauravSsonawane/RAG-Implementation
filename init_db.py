import asyncio
from storage.database import engine, Base
from storage.models import Session, ChatMessage, DocumentMetadata

async def init_db():
    print("🚀 Creating database tables...")
    async with engine.begin() as conn:
        # Import all models before calling run_sync to ensure they are registered with Base metadata
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
