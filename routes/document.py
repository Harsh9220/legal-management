from fastapi import APIRouter, Depends, HTTPException
from database import SessionLocal
from models.document import Document
from models.case import Case
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field
from starlette import status
from sqlalchemy.orm import Session
from datetime import datetime
from .auth import get_current_user, require_role

router=APIRouter(
    prefix="/document",
    tags=["document"]
)

class CreateDocumentRequest(BaseModel):
    document_name:str = Field(min_length=3,max_length=255)
    case_id:int

class UpdateDocumentRequest(BaseModel):
    document_name: Optional[str] = Field(None,min_length=3,max_length=255)
    
class DocumentResponse(BaseModel):
    id: int
    document_name: str
    uploader_id: int
    case_id: int
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

@router.post("/create-document",status_code=status.HTTP_201_CREATED)
async def create_document(document_data:CreateDocumentRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    case = db.query(Case).filter(Case.id == document_data.case_id,Case.is_deleted==False).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Case not found or deleted.")
    
    new_document = Document(
        document_name = document_data.document_name,
        uploader_id = current_user.get("id"),
        case_id = document_data.case_id
    )
    
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    return {"message":"Document uploaded successfully."}

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[DocumentResponse])
async def get_all_documents(current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)

    documents = db.query(Document).all()
    
    return documents

@router.get("/{document_id}",status_code=status.HTTP_200_OK,response_model=DocumentResponse)
async def get_document(document_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    document =  db.query(Document).filter(Document.id==document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not Found"
        )
    return document

@router.put("/update-document/{document_id}",status_code=status.HTTP_200_OK)
async def update_document(document_id:int,update_data:UpdateDocumentRequest, current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    document =  db.query(Document).filter(Document.id==document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not Found"
        )
    
    if update_data.document_name is not None:
        document.document_name=update_data.document_name

    
    db.commit()
    db.refresh(document)
    return {"message": "Document updated successfully"}
        
@router.delete("/delete-document/{document_id}",status_code=status.HTTP_200_OK)
async def delete_document(document_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)

    document =  db.query(Document).filter(Document.id==document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not Found"
        )
    
    db.delete(document)
    db.commit()  
    return {"message": "Document  deleted successfully"}