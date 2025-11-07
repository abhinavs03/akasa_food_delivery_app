from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..models import User
from ..security import get_session, hash_password, verify_password, create_access_token, validate_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    # Validate email format (basic check)
    if "@" not in email or "." not in email.split("@")[-1]:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Please enter a valid email address"},
            status_code=400,
        )
    
    # Validate password - this should catch all validation errors
    # Strip password for validation and use cleaned version
    password_clean = password.strip()
    is_valid, error_msg = validate_password(password_clean)
    if not is_valid:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": error_msg},
            status_code=400,
        )
    
    try:
        # Check if email already exists
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "This email is already registered. Please login instead."},
                status_code=400,
            )
        
        # Create user - use cleaned password (already validated)
        user = User(email=email, hashed_password=hash_password(password_clean))
        session.add(user)
        session.commit()
        session.refresh(user)
        response = RedirectResponse(url="/auth/login", status_code=303)
        return response
    except ValueError as e:
        # Handle password-related errors
        error_message = str(e)
        # Show the actual error for debugging, but make it user-friendly
        if "Password is too long" in error_message:
            error_message = "Password is too long. Maximum 72 characters allowed."
        elif "Password hashing error" in error_message:
            # Show the underlying error for debugging
            error_message = f"Password error: {error_message.replace('Password hashing error: ', '')}"
        elif "exceeds" in error_message.lower() and "72" in error_message:
            error_message = "Password validation error. Please check password requirements."
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": error_message},
            status_code=400,
        )
    except Exception as e:
        # Catch any other unexpected errors (database, etc.)
        error_message = str(e)
        # Log the actual error for debugging but show user-friendly message
        import logging
        logging.error(f"Registration error: {error_message}")
        
        # Make error messages more user-friendly
        if "72" in error_message.lower() and ("byte" in error_message.lower() or "truncate" in error_message.lower()):
            error_message = "Password validation error. Please ensure your password is 8-72 characters and contains at least one letter and one digit."
        elif "unique" in error_message.lower() or "constraint" in error_message.lower():
            error_message = "This email is already registered. Please login instead."
        else:
            error_message = "Registration failed. Please try again or contact support if the problem persists."
        
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": error_message},
            status_code=500,
        )

@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password. Please try again."},
            status_code=400,
        )
    token = create_access_token(user.email)
    response = RedirectResponse(url="/items", status_code=303)
    # Store token in cookie for simplicity (HttpOnly recommended)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, samesite="lax")
    return response

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response
