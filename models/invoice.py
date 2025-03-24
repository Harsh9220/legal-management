from sqlalchemy import Column, Integer, String, DateTime, func, Date,Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Invoice(Base):
    __tablename__='invoices'
    
    id= Column(Integer, primary_key=True, index=True)
    invoice_number= Column(Integer,nullable=False,unique=True)
    client_id=Column(Integer,ForeignKey("clients.id"),nullable=False)
    amount=Column(Integer,nullable=False)
    due_on_date=Column(Date,server_default=func.current_date())
    created_by=Column(Integer,ForeignKey("users.id"),nullable=False)
    updated_at= Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at= Column(DateTime, server_default=func.now())