from fastapi import APIRouter, HTTPException, Depends
from starlette import status
from database import SessionLocal
from pydantic import BaseModel, Field
from models.case import Case
from models.client import Client
from models.user import User
from sqlalchemy.orm import Session
from typing import Annotated, Optional, List
from datetime import datetime
from .auth import get_current_user,require_role

router=APIRouter(
    prefix="/cases",
    tags=["cases"]
)

class CreateCaseRequest(BaseModel):
    case_number:str = Field(min_length=3,max_length=50)
    case_name:str = Field(min_length=3,max_length=255)
    case_category:str = Field(pattern="^(theft|fraud|divorce)$")
    case_stage:str = Field(pattern="^(appeal|first degree)$")
    city_name: Optional[str] = Field(min_length=3, max_length=255)
    client_id: int
    remarks: Optional[str]
    staff_ids: Optional[List[int]] = None

    
class UpdateCaseRequest(BaseModel):
    case_name: Optional[str] = Field(None, min_length=3, max_length=255)
    case_category: Optional[str] = Field(None, pattern="^(theft|fraud|divorce)$")
    case_stage: Optional[str] = Field(None, pattern="^(appeal|first degree)$")
    city_name: Optional[str] = Field(None, min_length=3, max_length=255)
    client_id:Optional[int] = Field(None)
    remarks: Optional[str] = Field(None)
    case_status: Optional[str] = Field(None, pattern="^(open|closed)$")
    staff_ids: Optional[List[int]] = None

    
class ClientResponse(BaseModel):
    id: int
    name: str
    

    class Config:
        from_attributes = True

class LawyerResponse(BaseModel):
    id: int
    name: str
    

    class Config:
        from_attributes = True
        
class StaffResponse(BaseModel):
    id: int
    name: str
    

    class Config:
        from_attributes = True        
        

class CaseResponse(BaseModel):
    id: int
    case_number: str
    case_name: str
    case_category: str
    case_stage: str
    case_status: str
    issue_date: Optional[datetime] 
    city_name: Optional[str]
    remarks: Optional[str]
    lawyer: LawyerResponse
    client: ClientResponse
    staff_members: Optional[List[StaffResponse]] = []

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

@router.post("/create-case",status_code=status.HTTP_201_CREATED)
async def lawyer_create_case(case_data:CreateCaseRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    existing_case = db.query(Case).filter(Case.case_number == case_data.case_number).first()
    if existing_case:
        raise HTTPException(status_code=400, detail="Case number already exists")

    
    client=db.query(Client).filter(Client.id == case_data.client_id, Client.is_deleted == False).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found or deleted")
    
    new_case = Case(
        case_number=case_data.case_number,
        case_name=case_data.case_name,
        case_category=case_data.case_category,
        case_stage=case_data.case_stage,
        client_id=case_data.client_id,
        lawyer_id=current_user.get("id"),
        city_name=case_data.city_name,
        remarks=case_data.remarks
    )
    
    if case_data.staff_ids:
        for staff_id in case_data.staff_ids:
            staff = db.query(User).filter(User.id == staff_id, User.role=="staff",User.is_deleted == False).first()
            if not staff:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Staff with {staff_id} is not found or deleted")
            if staff not in new_case.staff_members:
                new_case.staff_members.append(staff)
    
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return {"message":"Case created successfully"}

@router.get("/",status_code=status.HTTP_200_OK, response_model=List[CaseResponse])
async def get_all_cases(current_user: user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)

        
    if current_user.get("role") == "staff":
        cases = db.query(Case).join(Case.staff_members).filter(
            Case.is_deleted == False,
            User.id == current_user.get("id")
        ).all()
    else:
        cases = db.query(Case).filter(Case.is_deleted == False).all()

    
    return cases

@router.get("/{case_id}",status_code=status.HTTP_200_OK, response_model=CaseResponse)
async def get_case(case_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
        
    if current_user.get("role") == "staff":
        case = db.query(Case).join(Case.staff_members).filter(
            Case.id==case_id,
            Case.is_deleted == False,
            User.id == current_user.get("id")
        ).first()
    else:
        case = db.query(Case).filter(Case.id==case_id,Case.is_deleted == False).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case

@router.put("/update-case/{case_id}",status_code=status.HTTP_200_OK)
async def update_case(case_id:int,update_data: UpdateCaseRequest, current_user:user_dependency, db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    case = db.query(Case).filter(Case.id == case_id, Case.is_deleted == False).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    if update_data.case_name is not None:
        case.case_name=update_data.case_name
    if update_data.case_category is not None:
        case.case_category= update_data.case_category
    if update_data.case_stage is not None:
        case.case_stage= update_data.case_stage
    if update_data.city_name is not None:
        case.city_name = update_data.city_name
    if update_data.case_status is not None:
        case.case_status = update_data.case_status
    if update_data.remarks is not None:
        case.remarks = update_data.remarks
    if update_data.client_id is not None:
        new_client = db.query(Client).filter(Client.id == update_data.client_id, Client.is_deleted == False).first()
        
        if not new_client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New client not found or deleted")
    
        case.client_id = update_data.client_id
    
    if hasattr(update_data, "staff_ids") and update_data.staff_ids is not None:
        case.staff_members.clear()
        for staff_id in update_data.staff_ids:
            staff = db.query(User).filter(
                User.id == staff_id,
                User.role == "staff",
                User.is_deleted == False
            ).first()
            if not staff:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Staff with ID {staff_id} not found or deleted"
                )
            case.staff_members.append(staff)
            
    db.commit()
    db.refresh(case)
    return {"message": "Case updated successfully"}

@router.put("/{case_id}/soft-delete",status_code=status.HTTP_200_OK)
async def soft_delete_case(case_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    case = db.query(Case).filter(Case.id==case_id).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    if case.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Case {case.id} is already deleted.",
        )
    
    case.is_deleted=True
    
    db.commit()
    db.refresh(case)

    return {"message": f"Case {case.id} has been deleted temporary."}

@router.put("/{case_id}/restore",status_code=status.HTTP_200_OK)
async def restore_case(case_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    case = db.query(Case).filter(Case.id==case_id).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    if not case.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Case {case.id} is not deleted, so it cannot be restored."
        )
    
    case.is_deleted = False

    db.commit()
    db.refresh(case)

    return {"message": f"Case {case.id} has been restored."}

@router.delete("/delete-case/{case_id}",status_code=status.HTTP_200_OK)
async def delete_case(case_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    case = db.query(Case).filter(Case.id==case_id).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    db.delete(case)
    db.commit()
    
    return {"message": f"Case {case_id} has been permanently deleted"}