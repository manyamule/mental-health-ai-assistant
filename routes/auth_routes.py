from fastapi import APIRouter, HTTPException, Depends, status
from database.models import UserCreate, UserLogin
from database.crud import create_user, get_user_by_email, update_last_login
from database.config import get_database
from auth.auth_handler import verify_password, create_access_token, get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Register a new user"""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = await create_user(db, user)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Remove password from response
    new_user.pop("hashed_password", None)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": new_user["email"],
            "user_id": new_user["_id"],
            "is_admin": new_user.get("is_admin", False)
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login")
async def login(credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Login user"""
    # Get user
    user = await get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    await update_last_login(db, user["_id"])
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": user["_id"],
            "is_admin": user.get("is_admin", False)
        }
    )
    
    # Remove password from response
    user.pop("hashed_password", None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current user information"""
    user = await get_user_by_email(db, current_user["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.pop("hashed_password", None)
    return user

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}