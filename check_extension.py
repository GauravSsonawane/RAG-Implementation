import asyncio
import os
from sqlalchemy import text
from storage.database import engine
from dotenv import load_dotenv

load_dotenv()

async def check_ext():
    async with engine.connect() as conn:
        print("Checking extensions...")
        res = await conn.execute(text("SELECT extname FROM pg_extension;"))
        exts = res.scalars().all()
        print(f"Extensions: {exts}")
        if "vector" not in exts:
            print("❌ 'vector' extension is NOT enabled.")
        else:
            print("✅ 'vector' extension is enabled.")

if __name__ == "__main__":
    asyncio.run(check_ext())
