from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from . import database, models
import os

from typing import Optional

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'temporary_secret')  # Use better/secure key in production
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# PUBLIC_INTERFACE
def get_db():
    """
    FastAPI dependency for DB session.
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hashing helpers (for demonstration, use passlib in production)
import hashlib

def hash_password(password: str) -> str:
    """
    Hashes password using SHA256 (not secure for production!).
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Token helpers
def create_access_token(data: dict, expires_delta=None):
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    # Expiry logic could go here
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    """
    Dependency to get the current authenticated user.
    Raises HTTP 401 if user/token invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
