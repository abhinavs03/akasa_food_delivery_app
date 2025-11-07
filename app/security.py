import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from .database import engine
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_session():
    with Session(engine) as session:
        yield session

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password and return (is_valid, error_message)
    Password requirements:
    - At least 8 characters
    - At most 72 characters (bcrypt limit)
    - At least one letter
    - At least one digit
    
    Note: password should already be stripped of leading/trailing whitespace
    """
    # Check minimum length first (most common error)
    if len(password) < 8:
        return False, f"Password must be at least 8 characters long (you entered {len(password)} characters)"
    
    # Check maximum byte length (bcrypt limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        return False, f"Password must be no more than 72 characters long (your password is {len(password)} characters)"
    
    # Check for at least one letter
    has_letter = any(c.isalpha() for c in password)
    if not has_letter:
        return False, "Password must contain at least one letter (a-z or A-Z)"
    
    # Check for at least one digit
    has_digit = any(c.isdigit() for c in password)
    if not has_digit:
        return False, "Password must contain at least one digit (0-9)"
    
    return True, ""

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt directly.
    Note: password should already be validated before calling this function.
    """
    # Double-check: ensure password is within bcrypt's 72-byte limit
    password_bytes = password.encode('utf-8')
    byte_length = len(password_bytes)
    
    if byte_length > 72:
        raise ValueError(f"Password exceeds 72-byte limit ({byte_length} bytes). This should have been caught by validation.")
    
    # Hash using bcrypt directly (more reliable than passlib for this use case)
    try:
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string (bcrypt returns bytes)
        return hashed.decode('utf-8')
    except ValueError as e:
        error_str = str(e).lower()
        if "72" in error_str or "byte" in error_str:
            raise ValueError("Password is too long. Maximum 72 characters allowed.") from e
        raise ValueError(f"Password hashing error: {str(e)}") from e

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash using bcrypt directly.
    """
    try:
        # Bcrypt has a 72-byte limit, so we truncate if necessary (same as hashing)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Convert hash string back to bytes if needed
        if isinstance(hashed, str):
            hashed_bytes = hashed.encode('utf-8')
        else:
            hashed_bytes = hashed
        
        # Verify using bcrypt
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        cookie_val = request.cookies.get("access_token")
        if cookie_val and cookie_val.startswith("Bearer "):
            token = cookie_val.split(" ", 1)[1]
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")  # type: ignore
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    return user
