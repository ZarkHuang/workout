from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class MealCreate(BaseModel):
    meal_type: str = "LUNCH" # BREAKFAST, LUNCH, DINNER, SNACK
    food_name: str
    calories: int
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    meal_date: Optional[date] = None

class MealOut(BaseModel):
    id: int
    user_id: int
    meal_type: str
    food_name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    meal_date: date
    created_at: datetime

    class Config:
        from_attributes = True

class DailyMacroProgress(BaseModel):
    date: date
    target_calories: int
    consumed_calories: int
    remaining_calories: int
    target_protein_g: float
    consumed_protein_g: float
    target_carbs_g: float
    consumed_carbs_g: float
    target_fat_g: float
    consumed_fat_g: float
    meals: List[MealOut] = []

class WeightLogCreate(BaseModel):
    weight_kg: float
    body_fat_pct: Optional[float] = None
    recorded_date: Optional[date] = None
    note: Optional[str] = None

class WeightLogOut(BaseModel):
    id: int
    user_id: int
    weight_kg: float
    body_fat_pct: Optional[float] = None
    recorded_date: date
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NaturalLanguageDietRequest(BaseModel):
    text: str = Field(..., description="飲食描述，例如：全家烤雞胸肉 1 片 + 蒸地瓜 150g + 無糖豆漿 400ml")
    meal_type: Optional[str] = "LUNCH"

class ParsedFoodItem(BaseModel):
    name: str
    portion: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

class ParsedDietResponse(BaseModel):
    summary_name: str
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    items: List[ParsedFoodItem] = []
    confidence_note: Optional[str] = None
