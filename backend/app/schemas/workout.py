from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ExerciseBase(BaseModel):
    name: str
    name_en: Optional[str] = None
    target_muscle_group: str # CHEST, BACK, LEGS, SHOULDERS, ARMS, CORE
    secondary_muscle_group: Optional[str] = None
    equipment: Optional[str] = "BARBELL" # BARBELL, DUMBBELL, MACHINE, CABLE, BODYWEIGHT
    instructions: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseOut(ExerciseBase):
    id: int
    is_custom: bool
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

class RoutineExerciseCreate(BaseModel):
    exercise_id: int
    target_sets: int = 3
    target_reps: int = 10
    order_index: int = 0

class RoutineExerciseOut(BaseModel):
    id: int
    exercise_id: int
    target_sets: int
    target_reps: int
    order_index: int
    exercise: Optional[ExerciseOut] = None

    class Config:
        from_attributes = True

class RoutineCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_split: str = "FULL_BODY"
    exercises: List[RoutineExerciseCreate] = []

class RoutineOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    target_split: str
    created_at: datetime
    exercises: List[RoutineExerciseOut] = []

    class Config:
        from_attributes = True

class SetCreate(BaseModel):
    exercise_id: int
    set_number: int
    weight_kg: float
    reps: int
    rpe: Optional[float] = 8.0
    is_completed: bool = True

class SetOut(BaseModel):
    id: int
    session_id: int
    exercise_id: int
    set_number: int
    weight_kg: float
    reps: int
    rpe: float
    is_completed: bool
    estimated_1rm: float
    exercise_name: Optional[str] = None

    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    routine_id: Optional[int] = None
    session_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = 0
    sets: List[SetCreate] = []
    ai_feedback_notes: Optional[str] = None

class SessionOut(BaseModel):
    id: int
    user_id: int
    routine_id: Optional[int] = None
    session_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int
    total_volume_kg: float
    ai_feedback_notes: Optional[str] = None
    created_at: datetime
    sets: List[SetOut] = []

    class Config:
        from_attributes = True

class MuscleRecoveryStatus(BaseModel):
    muscle_group: str # CHEST, BACK, LEGS, SHOULDERS, ARMS, CORE
    label_zh: str
    recovery_percentage: int # 0 to 100
    status: str # RECOVERED, RECOVERING, FATIGUED
    hours_since_last_trained: Optional[float] = None
    last_trained_date: Optional[str] = None
    last_volume_kg: float = 0.0

class MuscleRecoveryOverview(BaseModel):
    muscles: List[MuscleRecoveryStatus]
    recommended_focus: List[str]
    avoid_muscles: List[str]

class PreviousSetHint(BaseModel):
    exercise_id: int
    last_weight_kg: float
    last_reps: int
    last_estimated_1rm: float
    suggestion: str # e.g. "上次達成 60kg x 10，本次建議挑戰 62.5kg x 8-10 或加 1 組"
