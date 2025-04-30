from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db.session import Base

class QueryCache(Base):
    __tablename__ = "query_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    table = Column(String, nullable=False)
    query = Column(Text)
    path = Column(String)