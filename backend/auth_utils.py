import os
from datetime import datetime, timedelta

import bcrypt
import jwt
from database import SessionLocal, User
from fastapi import Depends, HTTPException, Request

# Secret used to sign our own session tokens (separate from Google's tokens).
# Falls back to a dev default so local testing doesn't break, but you should
# set a real random value in .env for anything beyond local dev.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    # bcrypt only uses the first 72 bytes of input — truncate explicitly
    # so behavior is predictable rather than silently ignoring the rest.
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1]


def get_current_user(request: Request) -> User:
    """Require a logged-in user. Raises 401 if not authenticated."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_access_token(token)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    finally:
        db.close()


def get_current_user_optional(request: Request) -> User | None:
    """Like get_current_user, but returns None instead of raising when
    there's no valid session — for endpoints that work for both logged-in
    and anonymous users (e.g. et/point can log history only if logged in).
    """
    token = _extract_token(request)
    if not token:
        return None
    try:
        user_id = decode_access_token(token)
    except HTTPException:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()
