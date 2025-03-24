from fastapi import APIRouter,Depends,HTTPException
from database import SessionLocal
from models.session import Session as CourtSession
from models.case import Case
from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from sqlalchemy.orm import Session
from starlette import status
from datetime import date, datetime
from .auth import get_current_user,require_role

router=APIRouter(
    prefix="/session",
    tags=["session"]
)

class CreateSessionRequest(BaseModel):
    case_id:int
    result:str=Field(min_length=3,max_length=100)
    session_date:Optional[date]
    court_type:str=Field(min_length=3,max_length=100)
    
class CaseResponse(BaseModel):
    id:int
    case_name:str
    
class SessionResponse(BaseModel):
    id: int
    case_id: int
    result: str
    session_date: date
    court_type: str
    created_at: datetime
    case:CaseResponse

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

@router.post("/create-session",status_code=status.HTTP_201_CREATED)
async def create_session(session_data:CreateSessionRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    case=db.query(Case).filter(Case.id==session_data.case_id,Case.is_deleted==False).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found or deleted")
    
    session_date=session_data.session_date or date.today()
    
    new_session = CourtSession(
        case_id = session_data.case_id,
        result = session_data.result,
        session_date = session_date,
        court_type = session_data.court_type
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"message":"Session created successfully"}

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[SessionResponse])
async def get_all_session(current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    session = db.query(CourtSession).all()
    
    return session

@router.get("/{session_id}",status_code=status.HTTP_200_OK,response_model=SessionResponse)
async def get_session(session_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    session=db.query(CourtSession).filter(CourtSession.id==session_id).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    return session

@router.delete("/delete-session/{session_id}",status_code=status.HTTP_200_OK)
async def delete_session(session_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","admin"],current_user)
    
    session=db.query(CourtSession).filter(CourtSession.id==session_id).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    
    db.delete(session)
    db.commit()
    return {"message": "Session  deleted successfully"}