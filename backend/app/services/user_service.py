from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await UserService.get_user_by_email(db, user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await UserService.get_user_by_username(db, user_create.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Hash the password
        hashed_password = get_password_hash(user_create.password)
        
        # Create user object
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            company=user_create.company,
            phone=user_create.phone,
            is_active=True,
            is_verified=False
        )
        
        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        # Update fields if provided
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.username is not None:
            user.username = user_update.username
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.company is not None:
            user.company = user_update.company
        if user_update.phone is not None:
            user.phone = user_update.phone
        if user_update.password is not None:
            user.hashed_password = get_password_hash(user_update.password)
        
        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Delete user by ID"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    async def is_active(user: User) -> bool:
        """Check if user is active"""
        return user.is_active

    @staticmethod
    async def is_superuser(user: User) -> bool:
        """Check if user is superuser"""
        return user.is_superuser