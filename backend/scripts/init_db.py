import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Parse database URL to get connection parameters
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/ovra_ai")
# Remove the dialect prefix for asyncpg
ASYNCPG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "")


async def drop_create_database():
    # Parse connection details
    parts = ASYNCPG_URL.split("/")
    db_name = parts[-1]
    server_url = "/".join(parts[:-1])
    
    # Connect to postgres database to manage other databases
    conn = await asyncpg.connect(f"{server_url}/postgres")
    
    try:
        # Drop existing database if it exists
        await conn.execute(f"""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
        """)
        
        await conn.execute(f"DROP DATABASE IF EXISTS {db_name}")
        print(f"Dropped database: {db_name}")
        
        # Create new database
        await conn.execute(f"CREATE DATABASE {db_name}")
        print(f"Created database: {db_name}")
        
    finally:
        await conn.close()
    
    # Create tables
    from app.core.database import engine, Base
    from app.models import user  # Import models to register them
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables")


if __name__ == "__main__":
    asyncio.run(drop_create_database())