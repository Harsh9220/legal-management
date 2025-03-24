from sqlalchemy import Column, Integer, String, DateTime, func, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    due_date = Column(Date, server_default=func.current_date())
    priority = Column(Enum("high", "medium", "low", name="priority"), nullable=False)
    assign_to_staff = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum("complete", "need review", "incomplete", name="status"), nullable=False, default="incomplete")
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
