from motor.motor_asyncio import AsyncIOMotorDatabase
from database.models import User, UserCreate, Session, Conversation, Appointment, Counselor
from database.config import (
    USERS_COLLECTION, SESSIONS_COLLECTION, CONVERSATIONS_COLLECTION,
    APPOINTMENTS_COLLECTION, COUNSELORS_COLLECTION
)
from auth.auth_handler import get_password_hash
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# ============= USER OPERATIONS =============

async def create_user(db: AsyncIOMotorDatabase, user: UserCreate) -> dict:
    """Create a new user"""
    # Check if user already exists
    existing_user = await db[USERS_COLLECTION].find_one({"email": user.email})
    if existing_user:
        return None
    
    # Hash password and create user
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()
    user_dict["is_active"] = True
    user_dict["is_admin"] = False
    
    result = await db[USERS_COLLECTION].insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return user_dict

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    """Get user by email"""
    user = await db[USERS_COLLECTION].find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    """Get user by ID"""
    user = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
    return user

async def update_last_login(db: AsyncIOMotorDatabase, user_id: str):
    """Update user's last login timestamp"""
    await db[USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login": datetime.utcnow()}}
    )

# ============= SESSION OPERATIONS =============

async def create_session(db: AsyncIOMotorDatabase, user_id: str, session_id: str, document_context: Optional[dict] = None) -> dict:
    """Create a new session"""
    session_dict = {
        "user_id": user_id,
        "session_id": session_id,
        "start_time": datetime.utcnow(),
        "emotions_detected": [],
        "document_context": document_context
    }
    
    result = await db[SESSIONS_COLLECTION].insert_one(session_dict)
    session_dict["_id"] = str(result.inserted_id)
    return session_dict

async def get_user_sessions(db: AsyncIOMotorDatabase, user_id: str, limit: int = 10) -> List[dict]:
    """Get user's recent sessions"""
    cursor = db[SESSIONS_COLLECTION].find({"user_id": user_id}).sort("start_time", -1).limit(limit)
    sessions = await cursor.to_list(length=limit)
    
    for session in sessions:
        session["_id"] = str(session["_id"])
    
    return sessions

async def end_session(db: AsyncIOMotorDatabase, session_id: str, overall_sentiment: str):
    """End a session"""
    session = await db[SESSIONS_COLLECTION].find_one({"session_id": session_id})
    if session:
        end_time = datetime.utcnow()
        duration = (end_time - session["start_time"]).total_seconds() / 60
        
        await db[SESSIONS_COLLECTION].update_one(
            {"session_id": session_id},
            {"$set": {
                "end_time": end_time,
                "duration_minutes": int(duration),
                "overall_sentiment": overall_sentiment
            }}
        )

# ============= CONVERSATION OPERATIONS =============

async def save_message(db: AsyncIOMotorDatabase, session_id: str, user_id: str, role: str, content: str, emotions: Optional[dict] = None) -> dict:
    """Save a conversation message"""
    message_dict = {
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "role": role,
        "content": content,
        "emotions": emotions
    }
    
    result = await db[CONVERSATIONS_COLLECTION].insert_one(message_dict)
    message_dict["_id"] = str(result.inserted_id)
    return message_dict

async def get_session_conversations(db: AsyncIOMotorDatabase, session_id: str) -> List[dict]:
    """Get all messages from a session"""
    cursor = db[CONVERSATIONS_COLLECTION].find({"session_id": session_id}).sort("timestamp", 1)
    messages = await cursor.to_list(length=None)
    
    for msg in messages:
        msg["_id"] = str(msg["_id"])
    
    return messages

# ============= APPOINTMENT OPERATIONS =============

async def create_appointment(db: AsyncIOMotorDatabase, user_id: str, appointment_data: dict) -> dict:
    """Create a new appointment"""
    appointment_dict = appointment_data.copy()
    appointment_dict["user_id"] = user_id
    appointment_dict["status"] = "scheduled"
    appointment_dict["created_at"] = datetime.utcnow()
    
    result = await db[APPOINTMENTS_COLLECTION].insert_one(appointment_dict)
    appointment_dict["_id"] = str(result.inserted_id)
    return appointment_dict

async def get_user_appointments(db: AsyncIOMotorDatabase, user_id: str) -> List[dict]:
    """Get user's appointments"""
    cursor = db[APPOINTMENTS_COLLECTION].find({"user_id": user_id}).sort("scheduled_time", -1)
    appointments = await cursor.to_list(length=None)
    
    for appt in appointments:
        appt["_id"] = str(appt["_id"])
    
    return appointments

async def get_counselors(db: AsyncIOMotorDatabase) -> List[dict]:
    """Get all active counselors"""
    cursor = db[COUNSELORS_COLLECTION].find({"is_active": True})
    counselors = await cursor.to_list(length=None)
    
    for counselor in counselors:
        counselor["_id"] = str(counselor["_id"])
    
    return counselors

# ============= ADMIN OPERATIONS =============

async def get_all_users(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 50) -> List[dict]:
    """Get all users (admin only)"""
    cursor = db[USERS_COLLECTION].find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("hashed_password", None)  # Don't return passwords
    
    return users

async def get_stats(db: AsyncIOMotorDatabase) -> dict:
    """Get system statistics"""
    total_users = await db[USERS_COLLECTION].count_documents({})
    total_sessions = await db[SESSIONS_COLLECTION].count_documents({})
    total_conversations = await db[CONVERSATIONS_COLLECTION].count_documents({})
    total_appointments = await db[APPOINTMENTS_COLLECTION].count_documents({})
    
    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_conversations": total_conversations,
        "total_appointments": total_appointments
    }