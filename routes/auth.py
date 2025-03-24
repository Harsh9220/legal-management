from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from database import SessionLocal
from pydantic import BaseModel
from models.user import User
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta, datetime, timezone
from starlette import status
from typing import Annotated,List
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    if user.is_blocked or user.is_deleted:
        return False
    return user


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    payload = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        user_role = payload.get("role")
        exp = payload.get("exp")

        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        if not username or not user_id or not user_role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        return {"username": username, "id": user_id, "role": user_role}
    
    except JWTError as e:
        
        logger.error(f"JWTError occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or token expired.",
        )


async def require_role(
    required_roles: List[str], current_user: Annotated[dict, Depends(get_current_user)]
):
    if current_user.get("role") not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted for role: {current_user.get('role')}",
        )
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=20)
    )
    return {"access_token": token, "token_type": "bearer"}


def create_default_admin(db: Session):
    admin_exists = db.query(User).filter(User.role == "admin").first()
    if not admin_exists:
        admin_user = User(
            username="admin12",
            email="harsh@gmail.com",
            name="Harsh",
            hashed_password=bcrypt_context.hash("12"),
            role="admin",
            mobile="9945673422",
            address="Default Address",
        )
        db.add(admin_user)
        db.commit()


def init_admin():
    with SessionLocal() as db:
        create_default_admin(db)


init_admin() 