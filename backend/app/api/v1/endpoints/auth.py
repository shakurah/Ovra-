import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.core.logging_config import log_auth_event, log_error, get_logger
from app.services.user_service import UserService
from app.schemas.user import (
    UserRegister, 
    UserLogin, 
    User, 
    UserCreate, 
    Token
)
from app.api.dependencies import get_current_active_user

router = APIRouter()


@router.post("/register/", response_model=User)
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    logger = get_logger("auth")
    
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        
        # Convert UserRegister to UserCreate
        user_create = UserCreate(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            company=user_data.company,
            phone=user_data.phone
        )
        
        # Create user
        user = await UserService.create_user(db, user_create)
        
        # Log successful registration
        log_auth_event(
            event="REGISTER",
            user_id=str(user.id),
            email=user.email,
            success=True,
            full_name=user.full_name,
            company=user.company,
            ip_address=request.client.host if request.client else None
        )
        
        logger.info(f"User registered successfully: {user.email} (ID: {user.id})")
        return user
        
    except Exception as e:
        # Log failed registration
        log_auth_event(
            event="REGISTER",
            email=user_data.email,
            success=False,
            error=str(e),
            ip_address=request.client.host if request.client else None
        )
        log_error(e, "User registration", email=user_data.email)
        raise


@router.post("/login/", response_model=Token)
async def login(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login user and return access/refresh tokens.
    """
    logger = get_logger("auth")
    
    try:
        logger.info(f"Login attempt for email: {user_data.email}")
        
        # Authenticate user
        user = await UserService.authenticate_user(
            db, email=user_data.email, password=user_data.password
        )
        
        if not user:
            # Log failed login attempt
            log_auth_event(
                event="LOGIN",
                email=user_data.email,
                success=False,
                error="Incorrect email or password",
                ip_address=request.client.host if request.client else None
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not await UserService.is_active(user):
            # Log inactive user login attempt
            log_auth_event(
                event="LOGIN",
                user_id=str(user.id),
                email=user.email,
                success=False,
                error="User account is inactive",
                ip_address=request.client.host if request.client else None
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Update last login time
        await UserService.update_last_login(db, user.id)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Log successful login
        log_auth_event(
            event="LOGIN",
            user_id=str(user.id),
            email=user.email,
            success=True,
            ip_address=request.client.host if request.client else None
        )
        
        logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=User.model_validate(user)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged above)
        raise
    except Exception as e:
        # Log unexpected errors
        log_auth_event(
            event="LOGIN",
            email=user_data.email,
            success=False,
            error=str(e),
            ip_address=request.client.host if request.client else None
        )
        log_error(e, "User login", email=user_data.email)
        raise



@router.get("/me/", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.post("/token/refresh/", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    """
    from app.core.security import decode_token
    
    # Decode refresh token
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user = await UserService.get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not await UserService.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=User.model_validate(user)
    )


@router.post("/logout/")
async def logout(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout user (invalidate token on client side).
    """
    return {"message": "Successfully logged out"}


@router.post("/token/verify/")
async def verify_token(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify if token is valid.
    """
    from app.core.security import decode_token
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = await UserService.get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {"valid": True, "user_id": user.id}