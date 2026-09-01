from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone
from app.core.database import get_db
from app.models.user import User
from app.models.nutrition import MealLog, DailyNutritionSummary, WeightLog
from app.schemas.nutrition import (
    MealCreate, MealOut, DailyMacroProgress,
    WeightLogCreate, WeightLogOut
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])

@router.get("/progress", response_model=DailyMacroProgress)
def get_daily_progress(
    target_date: Optional[date] = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    target_cals = profile.target_calories if profile else 2400
    target_p = profile.target_protein_g if profile else 140.0
    target_c = profile.target_carbs_g if profile else 280.0
    target_f = profile.target_fat_g if profile else 65.0

    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == current_user.id, MealLog.meal_date == target_date)
        .order_by(MealLog.created_at)
        .all()
    )

    consumed_cals = sum(m.calories for m in meals)
    consumed_p = sum(m.protein_g for m in meals)
    consumed_c = sum(m.carbs_g for m in meals)
    consumed_f = sum(m.fat_g for m in meals)

    return {
        "date": target_date,
        "target_calories": target_cals,
        "consumed_calories": consumed_cals,
        "remaining_calories": target_cals - consumed_cals,
        "target_protein_g": target_p,
        "consumed_protein_g": round(consumed_p, 1),
        "target_carbs_g": target_c,
        "consumed_carbs_g": round(consumed_c, 1),
        "target_fat_g": target_f,
        "consumed_fat_g": round(consumed_f, 1),
        "meals": meals
    }

@router.post("/meals", response_model=MealOut)
def add_meal(
    meal_in: MealCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    m_date = meal_in.meal_date or date.today()
    meal = MealLog(
        user_id=current_user.id,
        meal_type=meal_in.meal_type.upper(),
        food_name=meal_in.food_name,
        calories=meal_in.calories,
        protein_g=meal_in.protein_g,
        carbs_g=meal_in.carbs_g,
        fat_g=meal_in.fat_g,
        meal_date=m_date
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal

@router.delete("/meals/{meal_id}")
def delete_meal(
    meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meal = db.query(MealLog).filter(
        MealLog.id == meal_id,
        MealLog.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="找不到此餐點紀錄")
    
    db.delete(meal)
    db.commit()
    return {"message": "餐點紀錄已刪除"}

@router.get("/weight", response_model=List[WeightLogOut])
def get_weight_logs(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user.id)
        .order_by(desc(WeightLog.recorded_date))
        .limit(limit)
        .all()
    )

@router.post("/weight", response_model=WeightLogOut)
def record_weight(
    weight_in: WeightLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    r_date = weight_in.recorded_date or date.today()
    
    # Check if weight log for today already exists
    existing = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id,
        WeightLog.recorded_date == r_date
    ).first()

    if existing:
        existing.weight_kg = weight_in.weight_kg
        if weight_in.body_fat_pct is not None:
            existing.body_fat_pct = weight_in.body_fat_pct
        if weight_in.note is not None:
            existing.note = weight_in.note
        w_log = existing
    else:
        w_log = WeightLog(
            user_id=current_user.id,
            weight_kg=weight_in.weight_kg,
            body_fat_pct=weight_in.body_fat_pct,
            recorded_date=r_date,
            note=weight_in.note
        )
        db.add(w_log)

    # Also update profile current_weight_kg
    if current_user.profile:
        current_user.profile.current_weight_kg = weight_in.weight_kg
        if weight_in.body_fat_pct:
            current_user.profile.body_fat_percentage = weight_in.body_fat_pct

    db.commit()
    db.refresh(w_log)
    return w_log

@router.post("/cleanup-30d-rolling")
def perform_rolling_cleanup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rolling 30-day Cleanup:
    Aggregates meals older than 30 days into `daily_nutrition_summaries`
    and purges detailed meal logs to keep storage ultra-low!
    """
    cutoff_date = date.today() - timedelta(days=30)
    
    # Find all dates older than cutoff that have meals
    old_dates = (
        db.query(MealLog.meal_date)
        .filter(MealLog.user_id == current_user.id, MealLog.meal_date < cutoff_date)
        .distinct()
        .all()
    )

    aggregated_count = 0
    for row in old_dates:
        m_date = row[0]
        # Aggregate totals
        totals = db.query(
            func.sum(MealLog.calories).label("tot_cals"),
            func.sum(MealLog.protein_g).label("tot_p"),
            func.sum(MealLog.carbs_g).label("tot_c"),
            func.sum(MealLog.fat_g).label("tot_f")
        ).filter(
            MealLog.user_id == current_user.id,
            MealLog.meal_date == m_date
        ).first()

        # Check existing summary
        summary = db.query(DailyNutritionSummary).filter(
            DailyNutritionSummary.user_id == current_user.id,
            DailyNutritionSummary.summary_date == m_date
        ).first()

        if not summary:
            summary = DailyNutritionSummary(
                user_id=current_user.id,
                summary_date=m_date,
                total_calories=int(totals.tot_cals or 0),
                total_protein_g=float(totals.tot_p or 0.0),
                total_carbs_g=float(totals.tot_c or 0.0),
                total_fat_g=float(totals.tot_f or 0.0),
                is_aggregated=True
            )
            db.add(summary)
        else:
            summary.total_calories = int(totals.tot_cals or 0)
            summary.total_protein_g = float(totals.tot_p or 0.0)
            summary.total_carbs_g = float(totals.tot_c or 0.0)
            summary.total_fat_g = float(totals.tot_f or 0.0)
            summary.is_aggregated = True

        # Delete old detailed logs for this date
        db.query(MealLog).filter(
            MealLog.user_id == current_user.id,
            MealLog.meal_date == m_date
        ).delete()
        aggregated_count += 1

    db.commit()
    return {
        "status": "success",
        "message": f"已完成 30 天滾動歸檔，彙總了 {aggregated_count} 天的歷史資料並釋放明細空間！"
    }
