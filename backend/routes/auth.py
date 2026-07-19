import os

from auth_utils import create_access_token, get_current_user, hash_password, verify_password
from database import SessionLocal, User
from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, EmailStr

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


def _user_response(user: User, token: str):
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "name": user.name},
    }


@router.post("/auth/signup")
def signup(request: SignupRequest):
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="An account with this email already exists")

        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            name=request.name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(user.id)
        return _user_response(user, token)
    finally:
        db.close()


@router.post("/auth/login")
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(user.id)
        return _user_response(user, token)
    finally:
        db.close()


@router.post("/auth/google")
def google_auth(request: GoogleAuthRequest):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google sign-in isn't configured on the server (missing GOOGLE_CLIENT_ID)",
        )

    try:
        idinfo = google_id_token.verify_oauth2_token(
            request.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_id = idinfo["sub"]
    email = idinfo.get("email")
    name = idinfo.get("name")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            # Also check by email in case they'd already signed up with
            # email/password and are now linking Google to the same account
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.google_id = google_id
            else:
                user = User(email=email, google_id=google_id, name=name)
                db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(user.id)
        return _user_response(user, token)
    finally:
        db.close()


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}
