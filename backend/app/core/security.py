from datetime import datetime, timedelta, timezone

import requests
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import (
    API_TOKEN,
    AUTH_MODE,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
    OIDC_AUDIENCE,
    OIDC_ISSUER,
    OIDC_JWKS_URL,
)
from app.core.db import get_db
from app.models.entities import RoleEntity, RolePermissionEntity, UserEntity
from app.schemas.domain import UserContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def require_token(x_api_token: str = Header(default="")) -> None:
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(username: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_local(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def _decode_oidc(token: str) -> dict:
    if not OIDC_JWKS_URL:
        raise HTTPException(status_code=500, detail="OIDC_JWKS_URL not configured")
    header = jwt.get_unverified_header(token)
    jwks = requests.get(OIDC_JWKS_URL, timeout=5).json().get("keys", [])
    key = next((k for k in jwks if k.get("kid") == header.get("kid")), None)
    if not key:
        raise HTTPException(status_code=401, detail="OIDC signing key not found")
    return jwt.decode(token, key, algorithms=[key.get("alg", "RS256")], audience=OIDC_AUDIENCE, issuer=OIDC_ISSUER)


def get_user_context(token: str = Depends(oauth2_scheme)) -> UserContext:
    try:
        payload = _decode_oidc(token) if AUTH_MODE == "oidc" else _decode_local(token)
        role = payload.get("role", "security_analyst")
        return UserContext(username=payload["sub"], role=role)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT token") from exc


def require_permission(action: str):
    def _guard(ctx: UserContext = Depends(get_user_context), db: Session = Depends(get_db)) -> UserContext:
        role = db.scalar(select(RoleEntity).where(RoleEntity.name == ctx.role))
        if not role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role")
        perm = db.scalar(select(RolePermissionEntity).where(RolePermissionEntity.role_id == role.id, RolePermissionEntity.action == action))
        if not perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role lacks permission: {action}")
        return ctx

    return _guard


def authenticate_user(db: Session, username: str, password: str) -> UserContext | None:
    user = db.scalar(select(UserEntity).where(UserEntity.username == username))
    if not user or not verify_password(password, user.password_hash):
        return None
    role = db.scalar(select(RoleEntity).where(RoleEntity.id == user.role_id))
    return UserContext(username=user.username, role=role.name)
