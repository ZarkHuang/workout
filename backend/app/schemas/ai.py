from pydantic import BaseModel, Field
from typing import Optional, List

class AIRoutineExerciseItem(BaseModel):
    exercise_name: str
    target_muscle_group: str
    target_sets: int
    target_reps: str # e.g. "8-12" or "10"
    suggested_weight_kg: Optional[float] = None
    notes: Optional[str] = None

class AIRoutineRecommendRequest(BaseModel):
    duration_minutes: Optional[int] = 60
    available_equipment: Optional[str] = "GYM" # GYM, DUMBBELLS_ONLY, HOME_BODYWEIGHT
    focus_preference: Optional[str] = None # e.g. "CHEST", "LEGS", "AUTO"
    special_conditions: Optional[str] = None # e.g. "下背微痠", "時間緊迫"

class AIRoutineRecommendResponse(BaseModel):
    routine_title: str
    target_split: str
    rationale: str # 為什麼今天推薦這套（分析恢復度與歷史）
    warmup_tips: List[str]
    exercises: List[AIRoutineExerciseItem]
    cooldown_tips: Optional[List[str]] = []

class AIChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class AIChatRequest(BaseModel):
    message: str
    conversation_history: List[AIChatMessage] = [] # frontend sends recent 2-4 messages for context in memory only

class AIChatResponse(BaseModel):
    reply: str
    suggested_routine: Optional[AIRoutineRecommendResponse] = None # if AI suggested a routine, provide structured data for 1-click adoption
