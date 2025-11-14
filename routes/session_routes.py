from fastapi import APIRouter, Depends, HTTPException
from database.crud import (
    create_session, get_user_sessions, get_session_conversations,
    end_session, save_message
)
from database.config import get_database
from auth.auth_handler import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

@router.post("/start")
async def start_session(
    session_id: str,
    document_context: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Start a new session"""
    session = await create_session(
        db,
        user_id=current_user["user_id"],
        session_id=session_id,
        document_context=document_context
    )
    return session

@router.get("/my-sessions")
async def get_my_sessions(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current user's sessions"""
    sessions = await get_user_sessions(db, current_user["user_id"], limit)
    return sessions

@router.get("/{session_id}/conversations")
async def get_conversations(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all conversations from a session"""
    conversations = await get_session_conversations(db, session_id)
    return conversations

@router.post("/{session_id}/end")
async def finish_session(
    session_id: str,
    overall_sentiment: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """End a session"""
    await end_session(db, session_id, overall_sentiment)
    return {"message": "Session ended successfully"}

@router.post("/{session_id}/message")
async def add_message(
    session_id: str,
    role: str,
    content: str,
    emotions: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Add a message to session"""
    message = await save_message(
        db,
        session_id=session_id,
        user_id=current_user["user_id"],
        role=role,
        content=content,
        emotions=emotions
    )
    return message