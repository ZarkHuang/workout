from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    name_en = Column(String(100), nullable=True)
    target_muscle_group = Column(String(50), nullable=False, index=True) # CHEST, BACK, LEGS, SHOULDERS, ARMS, CORE
    secondary_muscle_group = Column(String(100), nullable=True)
    equipment = Column(String(50), default="BARBELL") # BARBELL, DUMBBELL, MACHINE, CABLE, BODYWEIGHT
    instructions = Column(Text, nullable=True)
    is_custom = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    routine_exercises = relationship("RoutineExercise", back_populates="exercise", cascade="all, delete-orphan")
    sets = relationship("WorkoutSet", back_populates="exercise")

class WorkoutRoutine(Base):
    __tablename__ = "workout_routines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    target_split = Column(String(50), default="FULL_BODY") # PUSH, PULL, LEGS, UPPER, LOWER, FULL_BODY
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="routines")
    exercises = relationship("RoutineExercise", back_populates="routine", cascade="all, delete-orphan", order_by="RoutineExercise.order_index")
    sessions = relationship("WorkoutSession", back_populates="routine")

class RoutineExercise(Base):
    __tablename__ = "routine_exercises"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    routine_id = Column(Integer, ForeignKey("workout_routines.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    target_sets = Column(Integer, default=3)
    target_reps = Column(Integer, default=10)
    order_index = Column(Integer, default=0)

    routine = relationship("WorkoutRoutine", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="routine_exercises")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    routine_id = Column(Integer, ForeignKey("workout_routines.id", ondelete="SET NULL"), nullable=True)
    session_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    total_volume_kg = Column(Float, default=0.0)
    ai_feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="sessions")
    routine = relationship("WorkoutRoutine", back_populates="sessions")
    sets = relationship("WorkoutSet", back_populates="session", cascade="all, delete-orphan", order_by="WorkoutSet.set_number")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    set_number = Column(Integer, default=1)
    weight_kg = Column(Float, default=0.0)
    reps = Column(Integer, default=0)
    rpe = Column(Float, default=8.0)
    is_completed = Column(Boolean, default=True)
    estimated_1rm = Column(Float, default=0.0)

    session = relationship("WorkoutSession", back_populates="sets")
    exercise = relationship("Exercise", back_populates="sets")
