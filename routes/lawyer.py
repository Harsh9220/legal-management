from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional, List
from models.user import User
from database import SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from starlette import status
from datetime import datetime
from .auth import get_current_user, require_role, bcrypt_context

router = APIRouter(prefix="/lawyer", tags=["lawyer"])


class CreateLawyerRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=3, max_length=255)
    address: Optional[str] = Field(None, min_length=2, max_length=255)
    password: str = Field(min_length=1)
    mobile: Optional[str] = Field(None, min_length=7, max_length=20)


class UpdateLawyerRequest(BaseModel):
    email: Optional[EmailStr] = Field(None)
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    address: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=1)
    mobile: Optional[str] = Field(None, min_length=7, max_length=20)
    
class LawyerResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    name: str
    address: Optional[str] = None
    mobile: Optional[str] = None
    role: str
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


@router.post("/create-lawyer", status_code=status.HTTP_201_CREATED)
async def create_lawyer(
    lawyer_data: CreateLawyerRequest, current_user: user_dependency, db: db_dependency
):
    await require_role(["admin"], current_user)
    
    if db.query(User).filter(User.username == lawyer_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
        
    if db.query(User).filter(User.email == lawyer_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )

    new_lawyer = User(
        email=lawyer_data.email,
        username=lawyer_data.username,
        name=lawyer_data.name,
        address=lawyer_data.address,
        hashed_password=bcrypt_context.hash(lawyer_data.password),
        role="lawyer",
        mobile=lawyer_data.mobile,
    )
    db.add(new_lawyer)
    db.commit()
    db.refresh(new_lawyer)
    return {"message": "Lawyer account created successfully"}


@router.get("/", status_code=status.HTTP_200_OK,response_model=List[LawyerResponse])
async def get_all_lawyers(current_user: user_dependency, db: db_dependency):
    await require_role(["admin"], current_user)
    return db.query(User).filter(User.role == "lawyer").all()


@router.get("/lawyer/{lawyer_id}", status_code=status.HTTP_200_OK,response_model=LawyerResponse)
async def get_lawyer(lawyer_id: int, current_user: user_dependency, db: db_dependency):

    await require_role(["admin"], current_user)
    lawyer = db.query(User).filter(User.id == lawyer_id, User.role == "lawyer").first()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer not found"
        )
    return lawyer


@router.put("/update-lawyer/{lawyer_id}", status_code=status.HTTP_200_OK)
async def update_lawyer(
    lawyer_id: int,
    update_data: UpdateLawyerRequest,
    current_user: user_dependency,
    db: db_dependency,
):

    await require_role(["admin"], current_user)
    lawyer = db.query(User).filter(User.id == lawyer_id, User.role == "lawyer").first()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer not found"
        )
    
    if update_data.email is not None:
        if db.query(User).filter(User.email == update_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )
        lawyer.email = update_data.email
    if update_data.name is not None:
        lawyer.name = update_data.name
    if update_data.address is not None:
        lawyer.address = update_data.address
    if update_data.mobile is not None:
        lawyer.mobile = update_data.mobile
    if update_data.password is not None:
        lawyer.hashed_password = bcrypt_context.hash(update_data.password)

    db.commit()
    db.refresh(lawyer)
    return {"message": "Lawyer account updated successfully"}


@router.put("/block-unblock-lawyer/{lawyer_id}", status_code=status.HTTP_200_OK)
async def block_unblock_lawyer(
    lawyer_id: int, current_user: user_dependency, db: db_dependency
):
    await require_role(["admin"], current_user)

    lawyer = db.query(User).filter(User.id == lawyer_id, User.role == "lawyer").first()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer not found"
        )

    lawyer.is_blocked = not lawyer.is_blocked

    db.commit()
    db.refresh(lawyer)

    new_status = "blocked" if lawyer.is_blocked else "unblocked"
    return {"message": f"Lawyer {lawyer.id} has been {new_status}"}


@router.delete("/lawyer/{lawyer_id}", status_code=status.HTTP_200_OK)
async def delete_lawyer(
    lawyer_id: int, current_user: user_dependency, db: db_dependency
):
    await require_role(["admin"], current_user)

    lawyer = db.query(User).filter(User.id == lawyer_id, User.role == "lawyer").first()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lawyer not found"
        )
    db.delete(lawyer)
    db.commit()
    return {"message": "Lawyer account deleted successfully"}
