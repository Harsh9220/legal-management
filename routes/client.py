from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from models.client import Client
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from starlette import status
from datetime import datetime
from .auth import get_current_user,require_role


router=APIRouter(
    prefix="/clients",
    tags=["clients"]
)

class CreateClientRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    name: str = Field(min_length=3, max_length=255)
    mobile_number: str = Field(min_length=7, max_length=20)
    vat_percentage: Optional[str] 
    vat_number : Optional[str]
    CR_number : Optional[str]
    address: Optional[str] = Field(None,min_length=3, max_length=255)
    
class UpdateClientRequest(BaseModel):
    email: Optional[EmailStr] = Field(None)
    name: Optional[str] = Field(None,min_length=3, max_length=255)
    mobile_number: Optional[str] = Field(None,min_length=7, max_length=20)
    vat_percentage: Optional[str] = Field(None)
    vat_number : Optional[str] = Field(None)
    CR_number : Optional[str] = Field(None)
    address: Optional[str] = Field(None,min_length=3, max_length=255)
    
class ClientResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    name: str
    mobile_number: str
    address: Optional[str] = None
    vat_percentage: Optional[str] = None
    vat_number: Optional[str] = None
    CR_number: Optional[str] = None
    is_blocked: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

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

@router.post("/create-client",status_code=status.HTTP_201_CREATED)
async def lawyer_create_client(client_data:CreateClientRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    if db.query(Client).filter(Client.username == client_data.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username already exists")
    
    if db.query(Client).filter(Client.email == client_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="email already exists")
    
    
    new_client=Client(
        username=client_data.username,
        email=client_data.email,
        name=client_data.name,
        address=client_data.address,
        mobile_number=client_data.mobile_number,
        vat_percentage=client_data.vat_percentage,
        vat_number=client_data.vat_number,
        CR_number=client_data.CR_number
    )
    
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return {"message": "Client created successfully"}

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[ClientResponse])
async def get_all_clients(current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    clients=db.query(Client).filter(Client.is_deleted==False).all()
    
    if not clients:
        return []
    
    return clients
    
@router.get("/client/{client_id}",status_code=status.HTTP_200_OK,response_model=ClientResponse)
async def get_client(client_id:int,current_user:user_dependency,db:db_dependency):
    
    await require_role(["lawyer","staff","admin"],current_user)
    
    client=db.query(Client).filter(Client.id==client_id, Client.is_deleted==False).first()
    
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    
    return client

@router.put("/update-client/{client_id}",status_code=status.HTTP_200_OK)
async def update_client(client_id:int, update_data:UpdateClientRequest,current_user:user_dependency,db:db_dependency):
    
    await require_role(["lawyer","admin"],current_user)
    client=db.query(Client).filter(Client.id==client_id,Client.is_deleted==False).first()
    
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Client not found")
    
    if update_data.email is not None:
        if db.query(Client).filter(Client.email == update_data.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="email already exists")
        client.email=update_data.email
    if update_data.name is not None:
        client.name=update_data.name
    if update_data.mobile_number is not None:
        client.mobile_number=update_data.mobile_number
    if update_data.vat_percentage is not None:
        client.vat_percentage=update_data.vat_percentage
    if update_data.vat_number is not None:
        client.vat_number=update_data.vat_number
    if update_data.CR_number is not None:
        client.CR_number=update_data.CR_number
    if update_data.address is not None:
        client.address=update_data.address
    
    db.commit()
    db.refresh(client)
    return {"message": "Client updated successfully"}

@router.delete("/delete-client/{client_id}", status_code=status.HTTP_200_OK)
async def delete_client(client_id: int, current_user: user_dependency, db: db_dependency):
    await require_role(["lawyer","admin"],current_user)

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    db.delete(client)
    db.commit()
    return {"message": "Client account permanently deleted successfully."}

@router.put("/block-unblock-client/{client_id}",status_code=status.HTTP_200_OK)
async def block_unblock_client(client_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    client=db.query(Client).filter(Client.id==client_id,Client.is_deleted==False).first()
    
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Client not found")
    
    client.is_blocked=not client.is_blocked
    
    db.commit()
    db.refresh(client)
    
    new_status = "blocked" if client.is_blocked else "unblocked"
    return {"message": f"Client {client.id} has been {new_status}"}

@router.put("/{client_id}/soft-delete",status_code=status.HTTP_200_OK)
async def soft_delete_client(client_id:int, current_user:user_dependency, db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    client=db.query(Client).filter(Client.id==client_id).first()
    
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Client not found")
    
    if client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client {client.id} is already deleted.",
        )
     
    client.is_deleted = True

    db.commit()
    db.refresh(client)

    return {"message": f"Client {client.id} has been deleted temporary."}       


@router.put("/{client_id}/restore", status_code=status.HTTP_200_OK)
async def restore_client(
    client_id: int, current_user: user_dependency, db: db_dependency
):
    await require_role(["lawyer","admin"],current_user)

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    if not client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client {client.id} is not deleted, so it cannot be restored."
        )

    client.is_deleted = False

    db.commit()
    db.refresh(client)

    return {"message": f"Client {client.id} has been restored."}