from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    routines = relationship("WorkoutRoutine", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete-orphan")
    meals = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    daily_summaries = relationship("DailyNutritionSummary", back_populates="user", cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    gender = Column(String(20), default="MALE")  # MALE, FEMALE
    age = Column(Integer, default=26)
    height_cm = Column(Float, default=175.0)
    current_weight_kg = Column(Float, default=70.0)
    target_weight_kg = Column(Float, default=72.0)
    body_fat_percentage = Column(Float, nullable=True)
    
    experience_level = Column(String(30), default="INTERMEDIATE")  # BEGINNER, INTERMEDIATE, ADVANCED
    fitness_goal = Column(String(30), default="BULKING")  # BULKING, CUTTING, MAINTENANCE
    activity_level = Column(String(30), default="MODERATE")  # SEDENTARY, LIGHT, MODERATE, ACTIVE, VERY_ACTIVE
    
    target_calories = Column(Integer, default=2400)
    target_protein_g = Column(Float, default=140.0)
    target_carbs_g = Column(Float, default=280.0)
    target_fat_g = Column(Float, default=65.0)
    
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="profile")
