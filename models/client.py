from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    mobile_number = Column(String, nullable=False)
    vat_percentage = Column(String(100))
    vat_number = Column(String(100))
    CR_number = Column(String(100))
    address = Column(String(255))
    name = Column(String(255), nullable=False)
    is_blocked = Column(Boolean, nullable=False, server_default="false")
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    invoices = relationship("Invoice", backref="client", cascade="save-update,delete")
    cases = relationship("Case", backref="client", cascade="save-update,delete")
