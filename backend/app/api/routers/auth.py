from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.users import authenticate_user, create_user, get_user_by_username
from app.db.session import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, payload.username)
    if existing is not None:
        raise HTTPException(status_code=409, detail="username_taken")
    try:
        user = create_user(db, username=payload.username, password=payload.password)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="username_taken")
    return UserOut(id=user.id, username=user.username)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    token = create_access_token(subject=user.username, expires_delta=timedelta(minutes=60 * 24))
    return TokenOut(access_token=token)

