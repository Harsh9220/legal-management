from fastapi import APIRouter, Depends
from typing import Annotated
from models.case import Case
from models.invoice import Invoice
from models.task import Task
from database import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette import status
from datetime import date, timedelta
from .auth import get_current_user, require_role

router = APIRouter(prefix="/admin/dashboard", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/open-closed-cases",status_code=status.HTTP_200_OK)
async def open_closed_cases_dashboard(current_user:user_dependency,db:db_dependency):
    await require_role(["admin"],current_user)
    
    open_cases=db.query(Case).filter(Case.case_status=="open",Case.is_deleted==False).count()
    
    closed_cases = db.query(Case).filter(Case.case_status == "closed", Case.is_deleted == False).count()
    
    thirty_days_ago = date.today() - timedelta(days=30)
    new_cases=db.query(Case).filter(Case.created_at >= thirty_days_ago,Case.is_deleted==False).count()
    
    return {"open_cases":open_cases,"closed_cases":closed_cases,"new_cases":new_cases}

@router.get("/paid_unpaid_amount",status_code=status.HTTP_200_OK)
async def paid_unpaid_amount_dashboard(current_user:user_dependency,db:db_dependency):
    await require_role(["admin"],current_user)
    
    today=date.today()
    unpaid_amount=db.query(func.sum(Invoice.amount)).filter(Invoice.due_on_date<today).scalar() or 0
    total_amount=db.query(func.sum(Invoice.amount)).scalar() or 0
    paid_amount=total_amount - unpaid_amount
    
    return {"paid_amount":paid_amount,"unpaid_amount":unpaid_amount}

@router.get("/case_status_change",status_code=status.HTTP_200_OK)
async def case_status_change_dashboard(current_user:user_dependency,db:db_dependency):
    await require_role(["admin"],current_user)
    
    thirty_days_ago = date.today() - timedelta(days=30)
    
    case_status_change =  db.query(Case).filter(Case.updated_at >= thirty_days_ago,Case.is_deleted==False).count()
    
    return {"case_status_changes_last_30_days": case_status_change}

    
@router.get("/task",status_code=status.HTTP_200_OK)
async def task_dashboard(current_user:user_dependency,db:db_dependency):
    await require_role(["admin"],current_user)
    
    today=date.today()
    
    due_today = db.query(Task).filter(Task.due_date==today,Task.status!="complete").count()
    
    overdue = db.query(Task).filter(Task.due_date < today, Task.status!="complete").count()
    
    completed = db.query(Task).filter(Task.status == "complete").count()
    
    return {"due_today_task":due_today,"overdue_task":overdue,"completed_task":completed}
