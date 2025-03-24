from sqlalchemy import Column, Integer, String, DateTime, func, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    result = Column(String(100), nullable=False)
    session_date = Column(Date, server_default=func.current_date())
    court_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
