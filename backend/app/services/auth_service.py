from datetime import timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

from backend.app.core.config import settings
from backend.app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from backend.app.models.user import User, Role, AuditLog
from backend.app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

class AuthService:
    @staticmethod
    def register_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        school_id: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> User:
        if db.query(User).filter_by(username=username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        if db.query(User).filter_by(email=email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        assigned_roles = roles or ["TEACHER"]
        role_objs = db.query(Role).filter(Role.name.in_(assigned_roles)).all()

        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            school_id=school_id,
            is_active=True,
            is_verified=True,
            roles=role_objs
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        user = db.query(User).filter((User.username == username) | (User.email == username)).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is deactivated")
        return user

    @classmethod
    def login(cls, db: Session, username: str, password: str) -> Dict[str, Any]:
        user = cls.authenticate_user(db, username, password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        
        user_roles = [r.name for r in user.roles]
        access_token = create_access_token(subject=user.id, roles=user_roles)
        refresh_token = create_refresh_token(subject=user.id)

        # Audit log
        log = AuditLog(user_id=user.id, action="LOGIN", resource_type="AUTH", details="User login successful")
        db.add(log)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "roles": user_roles,
                "school_id": user.school_id
            }
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Dict[str, Any]:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type for refresh")
            user_id = payload.get("sub")
            user = db.query(User).filter_by(id=user_id).first()
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User not found or inactive")
            
            user_roles = [r.name for r in user.roles]
            new_access_token = create_access_token(subject=user.id, roles=user_roles)
            return {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        raise credentials_exception
    return user

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role_names = [r.name for r in current_user.roles]
        if "ADMIN" in user_role_names:
            return current_user  # Admin bypass
        for role in allowed_roles:
            if role in user_role_names:
                return current_user
        raise HTTPException(status_code=403, detail="Forbidden: insufficient permissions")
    return role_checker
