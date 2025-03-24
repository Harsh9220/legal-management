from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from models.user import User
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated, Optional, List
from starlette import status
from datetime import datetime
from .auth import get_current_user, require_role, bcrypt_context

router = APIRouter(prefix="/staff", tags=["staff"])


class CreateStaffRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=3, max_length=255)
    address: Optional[str] = Field(None, min_length=2, max_length=255)
    password: str = Field(min_length=1)
    mobile: Optional[str] = Field(None, min_length=7, max_length=20)


class UpdateStaffRequest(BaseModel):
    email: Optional[EmailStr] = Field(None)
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    address: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=1)
    mobile: Optional[str] = Field(None, min_length=7, max_length=20)
    
class StaffResponse(BaseModel):
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


@router.post("/create-staff", status_code=status.HTTP_201_CREATED)
async def lawyer_create_staff(
    staff_data: CreateStaffRequest, current_user: user_dependency, db: db_dependency
):
    await require_role(["lawyer","admin"], current_user)
    
    if db.query(User).filter(User.username == staff_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    if db.query(User).filter(User.email == staff_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists"
        )
    new_staff = User(
        email=staff_data.email,
        username=staff_data.username,
        name=staff_data.name,
        address=staff_data.address,
        hashed_password=bcrypt_context.hash(staff_data.password),
        role="staff",
        mobile=staff_data.mobile,
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return {"message": "staff account created successfully"}


@router.get("/staffs", status_code=status.HTTP_200_OK,response_model=List[StaffResponse])
async def get_all_staffs(current_user: user_dependency, db: db_dependency):
    await require_role(["lawyer","admin"], current_user)
    return db.query(User).filter(User.role == "staff", User.is_deleted == False).all()


@router.get("/{staff_id}", status_code=status.HTTP_200_OK,response_model=StaffResponse)
async def get_staff(staff_id: int, current_user: user_dependency, db: db_dependency):
    await require_role(["lawyer","admin"], current_user)
    staff = (
        db.query(User)
        .filter(User.id == staff_id, User.role == "staff", User.is_deleted == False)
        .first()
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Staff not Found"
        )
    return staff


@router.put("/update-staff/{staff_id}", status_code=status.HTTP_200_OK)
async def update_staff(
    staff_id: int,
    update_data: UpdateStaffRequest,
    current_user: user_dependency,
    db: db_dependency,
):
    await require_role(["lawyer","admin"], current_user)
    staff = db.query(User).filter(User.id == staff_id, User.role == "staff",User.is_deleted==False).first()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found"
        )

    if update_data.email is not None:
        if db.query(User).filter(User.email == update_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists"
            )
        staff.email = update_data.email
    if update_data.name is not None:
        staff.name = update_data.name
    if update_data.address is not None:
        staff.address = update_data.address
    if update_data.mobile is not None:
        staff.mobile = update_data.mobile
    if update_data.password is not None:
        staff.hashed_password = bcrypt_context.hash(update_data.password)

    db.commit()
    db.refresh(staff)
    return {"message": "Staff account updated successfully"}


@router.delete("/delete-staff/{staff_id}", status_code=status.HTTP_200_OK)
async def delete_staff(staff_id: int, current_user: user_dependency, db: db_dependency):
    await require_role(["lawyer","admin"], current_user)

    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found"
        )

    db.delete(staff)
    db.commit()
    return {"message": "Staff account deleted successfully"}


@router.put("/block-unblock-staff/{staff_id}", status_code=status.HTTP_200_OK)
async def block_unblock_staff(
    staff_id: int, current_user: user_dependency, db: db_dependency
):
    await require_role(["lawyer","admin"], current_user)

    staff = (
        db.query(User)
        .filter(User.id == staff_id, User.role == "staff", User.is_deleted == False)
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found"
        )
    staff.is_blocked = not staff.is_blocked

    db.commit()
    db.refresh(staff)

    new_status = "blocked" if staff.is_blocked else "unblocked"
    return {"message": f"Staff {staff.id} has been {new_status}"}


@router.put("/{staff_id}/soft-delete", status_code=status.HTTP_200_OK)
async def soft_delete_staff(
    staff_id: int, current_user: user_dependency, db: db_dependency
):
    await require_role(["lawyer","admin"], current_user)

    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found"
        )

    if staff.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Staff {staff.id} is already deleted.",
        )

    staff.is_deleted = True

    db.commit()
    db.refresh(staff)

    return {"message": f"Staff {staff.id} has been deleted temporary."}


@router.put("/{staff_id}/restore", status_code=status.HTTP_200_OK)
async def restore_staff(
    staff_id: int, current_user: user_dependency, db: db_dependency
):
    await require_role(["lawyer","admin"], current_user)

    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found"
        )
    if not staff.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Staff {staff.id} is not deleted, so it cannot be restored.",
        )

    staff.is_deleted = False

    db.commit()
    db.refresh(staff)

    return {"message": f"Staff {staff.id} has been restored."}
