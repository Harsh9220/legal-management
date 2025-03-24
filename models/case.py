from sqlalchemy import Column,Integer,String,DateTime,func, Boolean,Enum,Date,ForeignKey,Table
from sqlalchemy.orm import relationship
from database import Base

case_staff = Table("case_staff",Base.metadata,
    Column("case_id", Integer, ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("staff_id",Integer,ForeignKey("users.id", ondelete="CASCADE"),primary_key=True,)
)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(255), nullable=False, unique=True)
    case_name = Column(String(255), nullable=False)
    case_category = Column(Enum("theft", "fraud", "divorce", name="case_category"), nullable=False)
    case_stage = Column(Enum("appeal", "first degree", name="case_stage"), nullable=False)
    case_status = Column(Enum("open", "closed", name="case_status"), nullable=False, default="open")
    issue_date = Column(Date, server_default=func.current_date())
    city_name = Column(String(255))
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    remarks = Column(String)
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    staff_members = relationship("User", secondary=case_staff, back_populates="assigned_cases", cascade="save-update,delete")
    
    tasks = relationship("Task", backref="case", cascade="save-update,delete")
    sessions = relationship("Session", backref="case", cascade="save-update,delete")
    documents = relationship("Document", backref="case", cascade="save-update,delete")
