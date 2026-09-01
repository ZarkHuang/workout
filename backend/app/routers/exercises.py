from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.workout import Exercise, WorkoutSet, WorkoutSession
from app.schemas.workout import ExerciseCreate, ExerciseOut, PreviousSetHint
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

@router.get("", response_model=List[ExerciseOut])
def list_exercises(
    muscle_group: Optional[str] = Query(None, description="CHEST, BACK, LEGS, SHOULDERS, ARMS, CORE, CARDIO"),
    equipment: Optional[str] = None,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Exercise).filter(
        or_(
            Exercise.is_custom == False,
            Exercise.created_by_user_id == current_user.id
        )
    )

    if muscle_group and muscle_group.upper() != "ALL":
        query = query.filter(Exercise.target_muscle_group == muscle_group.upper())

    if equipment and equipment.upper() != "ALL":
        query = query.filter(Exercise.equipment == equipment.upper())

    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            or_(
                Exercise.name.ilike(search_pattern),
                Exercise.name_en.ilike(search_pattern)
            )
        )

    return query.order_by(Exercise.target_muscle_group, Exercise.name).all()

@router.post("", response_model=ExerciseOut)
def create_custom_exercise(
    exercise_in: ExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exercise = Exercise(
        name=exercise_in.name,
        name_en=exercise_in.name_en,
        target_muscle_group=exercise_in.target_muscle_group.upper(),
        secondary_muscle_group=exercise_in.secondary_muscle_group,
        equipment=exercise_in.equipment.upper() if exercise_in.equipment else "BARBELL",
        instructions=exercise_in.instructions,
        is_custom=True,
        created_by_user_id=current_user.id
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise

@router.get("/{exercise_id}", response_model=ExerciseOut)
def get_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="找不到該動作")
    return exercise

@router.get("/{exercise_id}/previous-hint", response_model=PreviousSetHint)
def get_previous_set_hint(
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Query all-time PR for this exercise for this user
    pr_stats = (
        db.query(
            func.max(WorkoutSet.weight_kg),
            func.max(WorkoutSet.estimated_1rm)
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id == exercise_id,
            WorkoutSet.is_completed == True
        )
        .first()
    )
    pr_max_weight = float(pr_stats[0] or 0.0) if pr_stats else 0.0
    pr_max_1rm = float(pr_stats[1] or 0.0) if pr_stats else 0.0

    # 2. Find the most recent set from the last completed session
    recent_set = (
        db.query(WorkoutSet)
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id == exercise_id,
            WorkoutSet.is_completed == True
        )
        .order_by(desc(WorkoutSession.created_at), desc(WorkoutSet.weight_kg))
        .first()
    )

    if not recent_set:
        return {
            "exercise_id": exercise_id,
            "last_weight_kg": 0.0,
            "last_reps": 0,
            "last_estimated_1rm": 0.0,
            "pr_max_weight_kg": 0.0,
            "pr_max_1rm": 0.0,
            "suggestion": "初次記錄此動作，建議從輕重量熱身組開始抓感受度！"
        }

    last_weight = recent_set.weight_kg
    last_reps = recent_set.reps
    last_1rm = recent_set.estimated_1rm or round(last_weight * (1 + last_reps / 30.0), 1)
    
    if last_reps >= 10:
        suggestion = f"上次達成 {last_weight}kg × {last_reps} 次！本次建議嘗試漸進式超負荷：加重 2.5kg ({last_weight + 2.5}kg) 做 8-10 次。"
    else:
        suggestion = f"上次完成 {last_weight}kg × {last_reps} 次。本次建議挑戰相同重量做 {last_reps + 1}~{last_reps + 2} 次！"

    return {
        "exercise_id": exercise_id,
        "last_weight_kg": last_weight,
        "last_reps": last_reps,
        "last_estimated_1rm": last_1rm,
        "pr_max_weight_kg": pr_max_weight,
        "pr_max_1rm": pr_max_1rm,
        "suggestion": suggestion
    }
