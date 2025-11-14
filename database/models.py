from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

# Custom ObjectId type for Pydantic v2
class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# User Model
class User(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: EmailStr
    username: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    profile_picture: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    emergency_contact: Optional[Dict] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# User Registration
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None

# User Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Session Model
class Session(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str
    session_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    emotions_detected: List[Dict] = []
    overall_sentiment: Optional[str] = None
    document_context: Optional[Dict] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Conversation Model
class Conversation(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    session_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: str  # 'user' or 'assistant'
    content: str
    emotions: Optional[Dict] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Counselor Model
class Counselor(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    specialization: List[str]
    qualifications: str
    experience_years: int
    rating: float = 0.0
    available_slots: List[Dict] = []
    email: EmailStr
    phone: str
    bio: str
    profile_picture: Optional[str] = None
    is_active: bool = True
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Appointment Model
class Appointment(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str
    counselor_id: str
    scheduled_time: datetime
    duration_minutes: int = 60
    status: str = "scheduled"  # scheduled, completed, cancelled
    meeting_type: str = "video"  # video, audio, chat
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Appointment Booking Request
class AppointmentCreate(BaseModel):
    counselor_id: str
    scheduled_time: datetime
    duration_minutes: int = 60
    meeting_type: str = "video"
    notes: Optional[str] = None