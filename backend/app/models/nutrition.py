from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_type = Column(String(30), default="LUNCH") # BREAKFAST, LUNCH, DINNER, SNACK
    food_name = Column(String(200), nullable=False)
    calories = Column(Integer, default=0)
    protein_g = Column(Float, default=0.0)
    carbs_g = Column(Float, default=0.0)
    fat_g = Column(Float, default=0.0)
    meal_date = Column(Date, default=date.today, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="meals")

class DailyNutritionSummary(Base):
    __tablename__ = "daily_nutrition_summaries"
    __table_args__ = (UniqueConstraint("user_id", "summary_date", name="uq_user_summary_date"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_date = Column(Date, nullable=False, index=True)
    total_calories = Column(Integer, default=0)
    total_protein_g = Column(Float, default=0.0)
    total_carbs_g = Column(Float, default=0.0)
    total_fat_g = Column(Float, default=0.0)
    logged_weight_kg = Column(Float, nullable=True)
    is_aggregated = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="daily_summaries")

class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    body_fat_pct = Column(Float, nullable=True)
    recorded_date = Column(Date, default=date.today, index=True)
    note = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="weight_logs")
