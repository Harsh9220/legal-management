from fastapi import APIRouter,Depends,HTTPException
from database import SessionLocal
from models.invoice import Invoice
from models.client import Client
from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from sqlalchemy.orm import Session
from starlette import status
from datetime import date, datetime
from .auth import get_current_user,require_role

class CreateInvoiceRequest(BaseModel):
    invoice_number:int = Field(gt=0)
    client_id:int
    amount:int = Field(gt=0)
    due_on_date : Optional[date]
    
class UpdateInvoiceRequest(BaseModel):
    client_id:Optional[int] = Field(None)
    amount:Optional[int] = Field(None,gt=0)
    due_on_date: Optional[date] = Field(None)
    
    
router=APIRouter(
    prefix="/invoice",
    tags=["invoice"]
)
class CreatorResponse(BaseModel):
    id:int
    name:str
    
    class Config:
        from_attributes = True

class ClientResponse(BaseModel):
    id:int
    name:str
    
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id:int
    invoice_number:int
    amount:int
    due_on_date:Optional[date]=None
    updated_at:datetime
    created_at:datetime
    client:ClientResponse
    creator:CreatorResponse
    
    class Config:
        from_attributes = True
    

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post("/create-invoice",status_code=status.HTTP_201_CREATED)
async def create_invoice(invoice_data:CreateInvoiceRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    client=db.query(Client).filter(Client.id==invoice_data.client_id,Client.is_deleted==False).first()
    
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Client not found or deleted.")
    
    invoice=db.query(Invoice).filter(Invoice.invoice_number==invoice_data.invoice_number).first()
    if invoice:
        raise HTTPException(status_code=400,detail="Invoice number is already exists")
    
    due_date=invoice_data.due_on_date or date.today()
    
    new_invoice=Invoice(
        invoice_number=invoice_data.invoice_number,
        client_id=invoice_data.client_id,
        created_by=current_user.get("id"),
        amount=invoice_data.amount,
        due_on_date=due_date
    )
    
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    return {"message":"Invoice created successfully"}

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[InvoiceResponse])
async def get_all_invoice(current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    invoices=db.query(Invoice).all()
    
    return invoices

@router.get("/{invoice_id}",status_code=status.HTTP_200_OK,response_model=InvoiceResponse)
async def get_invoice(invoice_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    invoice = db.query(Invoice).filter(Invoice.id==invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invoice not found.")
    
    return invoice

@router.put("/update-invoice/{invoice_id}",status_code=status.HTTP_200_OK)
async def update_invoice(update_data:UpdateInvoiceRequest,invoice_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    invoice = db.query(Invoice).filter(Invoice.id==invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invoice not found.")
    
    if update_data.client_id is not None:
        new_client = db.query(Client).filter(Client.id == update_data.client_id, Client.is_deleted == False).first()
        if not new_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New client not found or deleted")
        invoice.client_id = update_data.client_id

    if update_data.amount is not None:
        invoice.amount=update_data.amount
    if update_data.due_on_date is not None:
        invoice.due_on_date=update_data.due_on_date
    
    db.commit()
    db.refresh(invoice)
    return {"message": "Invoice updated successfully"}

@router.delete("/delete-invoice/{invoice_id}",status_code=status.HTTP_200_OK)
async def delete_invoice(invoice_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    invoice = db.query(Invoice).filter(Invoice.id==invoice_id).first()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Invoice not found.")
    
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice  deleted successfully"}