from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.domain.schemas import TokenOut, UserCreate, UserLogin, UserOut
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: Session = Depends(get_db)) -> TokenOut:
    email = str(payload.email).lower()
    existing = session.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Аккаунт с таким email уже существует")

    user = User(email=email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, session: Session = Depends(get_db)) -> TokenOut:
    user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})
    return TokenOut(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
