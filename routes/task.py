from fastapi import APIRouter,Depends,HTTPException
from database import SessionLocal
from models.task import Task
from models.case import Case
from models.user import User
from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from sqlalchemy.orm import Session
from starlette import status
from datetime import date, datetime
from .auth import get_current_user,require_role

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

class CreateTaskRequest(BaseModel):
    task_name:str = Field(min_length=3,max_length=255)
    due_date:Optional[date]
    priority:str = Field(pattern="^(high|medium|low)$")
    assign_to_staff : Optional[int]=None
    case_id:int
    
    
class UpdateTaskRequest(BaseModel):
    task_name:Optional[str] = Field(None,min_length=3,max_length=255)
    due_date:Optional[date] = Field(None)
    priority: Optional[str] = Field(None,pattern="^(high|medium|low)$")
    assign_to_staff: Optional[int] = Field(None)
    status: Optional[str] = Field(None,pattern="^(complete|need review|incomplete)$")
    
    
class TaskResponse(BaseModel):
    id: int
    task_name: str
    due_date: date
    priority: str
    status: str
    case_id: int
    assign_to_staff: Optional[int] = None
    created_by: int
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

@router.post("/create-task",status_code=status.HTTP_201_CREATED)
async def create_task(task_data:CreateTaskRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    case = db.query(Case).filter(Case.id==task_data.case_id,Case.is_deleted==False).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Case not found or deleted")
    
    if task_data.assign_to_staff is not None:
        staff = db.query(User).filter(User.id ==  task_data.assign_to_staff, User.role == "staff",User.is_deleted==False).first()
        if not staff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Assigned staff is not found or deleted.")
    
    due_date = task_data.due_date or date.today()
    
    new_task = Task(
        task_name = task_data.task_name,
        due_date =  due_date,
        priority = task_data.priority,
        assign_to_staff = task_data.assign_to_staff,
        case_id = task_data.case_id,
        created_by = current_user.get("id"),
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message":"Task created successfully"}

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[TaskResponse])
async def get_all_tasks(current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
        
    tasks = db.query(Task).all()
    
    return tasks
@router.get("/dashboard",status_code=status.HTTP_200_OK)
async def task_dashboard(current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
    
    today=date.today()
    
    due_today = db.query(Task).filter(Task.due_date==today,Task.status!="complete").count()
    
    overdue = db.query(Task).filter(Task.due_date < today, Task.status!="complete").count()
    
    completed = db.query(Task).filter(Task.status == "complete").count()
    
    return {"due_today_task":due_today,"overdue_task":overdue,"completed_task":completed}


@router.get("/{task_id}",status_code=status.HTTP_200_OK)
async def get_task(task_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)
        
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found.")
    
    return task

@router.put("/update-task/{task_id}",status_code=status.HTTP_200_OK)
async def update_task(task_id:int,update_data:UpdateTaskRequest,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)

    task = db.query(Task).filter(Task.id==task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found.")
    
    if update_data.task_name is not None:
        task.task_name=update_data.task_name
    if update_data.due_date is not None:
        task.due_date=update_data.due_date
    if update_data.priority is not None:
        task.priority=update_data.priority
    if update_data.assign_to_staff is not None:
        staff = db.query(User).filter(User.id ==  update_data.assign_to_staff, User.role == "staff",User.is_deleted==False).first()
        if not staff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Assigned staff is not found or deleted.")
        task.assign_to_staff=update_data.assign_to_staff
    if update_data.status is not None:
        task.status = update_data.status
    
    db.commit()
    db.refresh(task)
    return {"message": "Task updated successfully"}

@router.delete("/delete-task/{task_id}",status_code=status.HTTP_200_OK)
async def delete_task(task_id:int,current_user:user_dependency,db:db_dependency):
    await require_role(["lawyer","staff","admin"],current_user)

    task = db.query(Task).filter(Task.id==task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task not found.")
    
    db.delete(task)
    db.commit()
    return {"message": f"Task has been deleted"}

