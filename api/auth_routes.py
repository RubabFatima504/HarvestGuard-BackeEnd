"""Auth endpoints — register / login / current-user profile."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from db import User, get_session
from auth import hash_password, verify_password, create_access_token, get_current_user
from api.models import UserRegister, UserLogin, UserProfile, TokenResponse, UserProfileUpdate

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        cooperative_name=user.cooperative_name,
        role=user.role,
    )


@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegister, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        cooperative_name=payload.cooperative_name,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=_to_profile(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=_to_profile(user))


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return _to_profile(current_user)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.name is not None:
        current_user.name = payload.name
    if payload.cooperative_name is not None:
        current_user.cooperative_name = payload.cooperative_name
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return _to_profile(current_user)
