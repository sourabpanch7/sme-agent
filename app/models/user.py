from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from .base import Base


class UserSession(Base):
    __tablename__ = 'user_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    jwt_token = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta = Column(JSON, default={})
