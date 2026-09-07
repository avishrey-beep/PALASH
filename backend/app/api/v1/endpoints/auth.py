from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.auth_service import AuthService, get_current_user
from backend.app.models.user import User
from backend.app.models.curriculum import Language

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    school_id: Optional[str] = None
    roles: Optional[List[str]] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user and returns JWT access and refresh tokens."""
    return AuthService.login(db, req.username, req.password)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user (default role: TEACHER)."""
    user = AuthService.register_user(
        db,
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        school_id=req.school_id,
        roles=req.roles
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "school_id": user.school_id,
        "roles": [r.name for r in user.roles]
    }

@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refreshes an expired access token using a valid refresh token."""
    return AuthService.refresh_access_token(db, req.refresh_token)

class UpdateProfileRequest(BaseModel):
    """Fields a teacher may change on their own profile from the app.

    All optional -- only the supplied fields are updated (PATCH semantics).
    Role, username and email are intentionally NOT editable here: roles are an
    admin concern and identity fields need a separate verified flow.
    """

    full_name: Optional[str] = None
    preferred_language: Optional[str] = Field(default=None, min_length=2, max_length=10)


def _profile_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "school_id": user.school_id,
        "preferred_language": user.preferred_language,
        "roles": [r.name for r in user.roles],
    }


@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile and assigned roles."""
    return _profile_dict(current_user)


@router.patch("/me")
def update_current_user_profile(
    req: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated teacher's own editable profile fields.

    ``preferred_language`` is validated against the languages the platform
    actually supports, so the app can't persist a code the backend has no data
    for. Nothing is fabricated: an unknown code is rejected with 400 rather
    than silently stored.
    """
    if req.full_name is not None:
        current_user.full_name = req.full_name

    if req.preferred_language is not None:
        lang = (
            db.query(Language)
            .filter(Language.code == req.preferred_language, Language.is_active == True)  # noqa: E712
            .first()
        )
        if lang is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported or inactive language code: {req.preferred_language}",
            )
        current_user.preferred_language = req.preferred_language

    db.commit()
    db.refresh(current_user)
    return _profile_dict(current_user)
