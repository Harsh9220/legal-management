from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, func 
from sqlalchemy.orm import relationship
from database import Base
from models.case import Case
from models.task import Task
from models.document import Document
from models.invoice import Invoice

class User(Base):
    __tablename__='users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    name= Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    mobile = Column(String(20))
    address = Column(String(255))
    role = Column(Enum("lawyer", "staff", "admin", "client", name="user_roles"), nullable=False)  
    is_blocked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False) 

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    cases=relationship("Case",backref="lawyer",cascade="save-update,delete",foreign_keys="[Case.lawyer_id]")
    assign_tasks=relationship("Task", backref="assign_staff", cascade="save-update,delete", foreign_keys="[Task.assign_to_staff]")
    created_task=relationship("Task", backref="creator", cascade="save-update,delete", foreign_keys="[Task.created_by]")
    invoices=relationship("Invoice", backref="creator", cascade="save-update,delete", foreign_keys="[Invoice.created_by]")
    documents=relationship("Document",backref="uploader",cascade="save-update,delete", foreign_keys="[Document.uploader_id]")
    assigned_cases = relationship("Case", secondary="case_staff", back_populates="staff_members")