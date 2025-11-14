from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = "mental_health_db"

# Async client for FastAPI
async_client = None
async_db = None

# Sync client for scripts
sync_client = MongoClient(MONGODB_URL)
sync_db = sync_client[DATABASE_NAME]

async def connect_to_mongo():
    """Connect to MongoDB on startup"""
    global async_client, async_db
    async_client = AsyncIOMotorClient(MONGODB_URL)
    async_db = async_client[DATABASE_NAME]
    print(f"✓ Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """Close MongoDB connection on shutdown"""
    global async_client
    if async_client:
        async_client.close()
        print("✓ MongoDB connection closed")

def get_database():
    """Get database instance"""
    return async_db

# Collection names
USERS_COLLECTION = "users"
SESSIONS_COLLECTION = "sessions"
CONVERSATIONS_COLLECTION = "conversations"
APPOINTMENTS_COLLECTION = "appointments"
COUNSELORS_COLLECTION = "counselors"
ADMIN_LOGS_COLLECTION = "admin_logs"