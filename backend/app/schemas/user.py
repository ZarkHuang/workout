from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None # User Nickname
    gender: Optional[str] = "MALE" # MALE, FEMALE
    age: Optional[int] = 26
    height_cm: Optional[float] = 175.0
    current_weight_kg: Optional[float] = 70.0
    target_weight_kg: Optional[float] = 72.0
    body_fat_percentage: Optional[float] = None
    experience_level: Optional[str] = "INTERMEDIATE" # BEGINNER, INTERMEDIATE, ADVANCED
    fitness_goal: Optional[str] = "BULKING" # BULKING, CUTTING, MAINTENANCE
    activity_level: Optional[str] = "MODERATE" # SEDENTARY, LIGHT, MODERATE, ACTIVE, VERY_ACTIVE
    target_calories: Optional[int] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None

class UserProfileOut(BaseModel):
    id: int
    user_id: int
    gender: str
    age: int
    height_cm: float
    current_weight_kg: float
    target_weight_kg: float
    body_fat_percentage: Optional[float] = None
    experience_level: str
    fitness_goal: str
    activity_level: str
    target_calories: int
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    profile: Optional[UserProfileOut] = None

    class Config:
        from_attributes = True
