from fastapi import APIRouter, Depends, HTTPException
from database.models import AppointmentCreate
from database.crud import (
    create_appointment, get_user_appointments, get_counselors
)
from database.config import get_database
from auth.auth_handler import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

@router.get("/counselors")
async def list_counselors(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all available counselors"""
    counselors = await get_counselors(db)
    return counselors

@router.post("/book")
async def book_appointment(
    appointment: AppointmentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Book an appointment with a counselor"""
    appointment_data = appointment.dict()
    new_appointment = await create_appointment(
        db,
        user_id=current_user["user_id"],
        appointment_data=appointment_data
    )
    return new_appointment

@router.get("/my-appointments")
async def get_my_appointments(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current user's appointments"""
    appointments = await get_user_appointments(db, current_user["user_id"])
    return appointments