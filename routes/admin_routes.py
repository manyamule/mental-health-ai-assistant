from fastapi import APIRouter, Depends, HTTPException
from database.crud import get_all_users, get_stats
from database.config import get_database, COUNSELORS_COLLECTION
from auth.auth_handler import get_current_admin
from motor.motor_asyncio import AsyncIOMotorDatabase
from database.models import Counselor
from bson import ObjectId

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/stats")
async def get_system_stats(
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get system statistics"""
    stats = await get_stats(db)
    return stats

@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all users (admin only)"""
    users = await get_all_users(db, skip, limit)
    return users

@router.post("/counselors")
async def add_counselor(
    counselor: Counselor,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Add a new counselor"""
    counselor_dict = counselor.dict(exclude={"id"})
    result = await db[COUNSELORS_COLLECTION].insert_one(counselor_dict)
    counselor_dict["_id"] = str(result.inserted_id)
    return counselor_dict

@router.get("/counselors")
async def list_all_counselors(
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all counselors (admin only)"""
    cursor = db[COUNSELORS_COLLECTION].find()
    counselors = await cursor.to_list(length=None)
    for counselor in counselors:
        counselor["_id"] = str(counselor["_id"])
    return counselors

@router.put("/counselors/{counselor_id}")
async def update_counselor(
    counselor_id: str,
    counselor_data: dict,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update counselor information"""
    result = await db[COUNSELORS_COLLECTION].update_one(
        {"_id": ObjectId(counselor_id)},
        {"$set": counselor_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Counselor not found")
    return {"message": "Counselor updated successfully"}

@router.delete("/counselors/{counselor_id}")
async def delete_counselor(
    counselor_id: str,
    current_user: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a counselor"""
    result = await db[COUNSELORS_COLLECTION].delete_one({"_id": ObjectId(counselor_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Counselor not found")
    return {"message": "Counselor deleted successfully"}