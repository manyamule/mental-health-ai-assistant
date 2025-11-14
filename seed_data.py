"""
Seed database with initial data
Run this once to populate the database with sample data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from database.config import MONGODB_URL, DATABASE_NAME
from database.config import (
    USERS_COLLECTION, COUNSELORS_COLLECTION
)
from auth.auth_handler import get_password_hash
from datetime import datetime

async def seed_database():
    """Seed database with initial data"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("🌱 Seeding database...")
    
    # 1. Create admin user
    print("\n1️⃣ Creating admin user...")
    admin_exists = await db[USERS_COLLECTION].find_one({"email": "admin@mentalhealth.com"})
    
    if not admin_exists:
        admin_user = {
            "email": "admin@mentalhealth.com",
            "username": "admin",
            "full_name": "System Administrator",
            "hashed_password": get_password_hash("admin123"),  # Change in production!
            "is_active": True,
            "is_admin": True,
            "created_at": datetime.utcnow()
        }
        await db[USERS_COLLECTION].insert_one(admin_user)
        print("   ✓ Admin user created")
        print("   📧 Email: admin@mentalhealth.com")
        print("   🔑 Password: admin123")
    else:
        print("   ⚠️ Admin user already exists")
    
    # 2. Create sample counselors
    print("\n2️⃣ Creating sample counselors...")
    
    sample_counselors = [
        {
            "name": "Dr. Sarah Johnson",
            "specialization": ["Depression", "Anxiety", "Stress Management"],
            "qualifications": "Ph.D. in Clinical Psychology, Licensed Therapist",
            "experience_years": 12,
            "rating": 4.8,
            "email": "sarah.johnson@mentalhealth.com",
            "phone": "+1-555-0101",
            "bio": "Dr. Johnson specializes in cognitive behavioral therapy and has extensive experience treating anxiety and depression.",
            "is_active": True,
            "available_slots": [
                {"day": "Monday", "time": "09:00-17:00"},
                {"day": "Wednesday", "time": "09:00-17:00"},
                {"day": "Friday", "time": "09:00-17:00"}
            ]
        },
        {
            "name": "Dr. Michael Chen",
            "specialization": ["Trauma", "PTSD", "Grief Counseling"],
            "qualifications": "M.D. in Psychiatry, Board Certified",
            "experience_years": 15,
            "rating": 4.9,
            "email": "michael.chen@mentalhealth.com",
            "phone": "+1-555-0102",
            "bio": "Dr. Chen is an experienced psychiatrist specializing in trauma recovery and PTSD treatment.",
            "is_active": True,
            "available_slots": [
                {"day": "Tuesday", "time": "10:00-18:00"},
                {"day": "Thursday", "time": "10:00-18:00"}
            ]
        },
        {
            "name": "Dr. Emily Rodriguez",
            "specialization": ["Family Therapy", "Relationship Counseling", "Life Coaching"],
            "qualifications": "Licensed Marriage and Family Therapist",
            "experience_years": 8,
            "rating": 4.7,
            "email": "emily.rodriguez@mentalhealth.com",
            "phone": "+1-555-0103",
            "bio": "Dr. Rodriguez helps individuals and families navigate relationship challenges and life transitions.",
            "is_active": True,
            "available_slots": [
                {"day": "Monday", "time": "14:00-20:00"},
                {"day": "Wednesday", "time": "14:00-20:00"},
                {"day": "Saturday", "time": "09:00-15:00"}
            ]
        }
    ]
    
    for counselor in sample_counselors:
        existing = await db[COUNSELORS_COLLECTION].find_one({"email": counselor["email"]})
        if not existing:
            await db[COUNSELORS_COLLECTION].insert_one(counselor)
            print(f"   ✓ Created: {counselor['name']}")
        else:
            print(f"   ⚠️ Already exists: {counselor['name']}")
    
    print("\n✅ Database seeding complete!")
    print("\n" + "="*50)
    print("📝 Login Credentials:")
    print("="*50)
    print("Admin Login:")
    print("  Email: admin@mentalhealth.com")
    print("  Password: admin123")
    print("\n⚠️  IMPORTANT: Change admin password in production!")
    print("="*50)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())