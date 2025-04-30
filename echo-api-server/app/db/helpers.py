from app.models.QueryCache import QueryCache
from datetime import datetime
from app.db.session import AsyncSessionLocal
from sqlalchemy import select

async def log_cache_query(table_name: str, query: str, result_path: str, ip: str):
    async with AsyncSessionLocal() as session:
        log = QueryCache(
            table=table_name,
            query=query,
            path=result_path,
            ip_address=ip
        )
        session.add(log)
        await session.commit()

async def get_cached_query(sql: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(QueryCache).where(QueryCache.query == sql)
        )
        return result.scalars().first()