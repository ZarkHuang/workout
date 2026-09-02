from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.models.user import User
from app.models.workout import Exercise, WorkoutRoutine, RoutineExercise, WorkoutSession, WorkoutSet
from app.schemas.workout import (
    RoutineCreate, RoutineOut, SessionCreate, SessionOut,
    MuscleRecoveryOverview, MuscleRecoveryStatus
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/workouts", tags=["workouts"])

# 1. Routines
@router.get("/routines", response_model=List[RoutineOut])
def get_routines(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(WorkoutRoutine).filter(WorkoutRoutine.user_id == current_user.id).order_by(desc(WorkoutRoutine.created_at)).all()

@router.post("/routines", response_model=RoutineOut)
def create_routine(
    routine_in: RoutineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    routine = WorkoutRoutine(
        user_id=current_user.id,
        title=routine_in.title,
        description=routine_in.description,
        target_split=routine_in.target_split.upper()
    )
    db.add(routine)
    db.flush()

    for idx, ex_in in enumerate(routine_in.exercises):
        re = RoutineExercise(
            routine_id=routine.id,
            exercise_id=ex_in.exercise_id,
            target_sets=ex_in.target_sets,
            target_reps=ex_in.target_reps,
            order_index=idx
        )
        db.add(re)
    
    db.commit()
    db.refresh(routine)
    return routine

@router.delete("/routines/{routine_id}")
def delete_routine(
    routine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    routine = db.query(WorkoutRoutine).filter(
        WorkoutRoutine.id == routine_id,
        WorkoutRoutine.user_id == current_user.id
    ).first()
    if not routine:
        raise HTTPException(status_code=404, detail="找不到課表")
    db.delete(routine)
    db.commit()
    return {"message": "課表已成功刪除"}

# 2. Workout Sessions (Live / Completed)
@router.get("/sessions", response_model=List[SessionOut])
def get_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == current_user.id)
        .order_by(desc(WorkoutSession.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    result = []
    for s in sessions:
        sets_out = []
        for st in s.sets:
            sets_out.append({
                "id": st.id,
                "session_id": st.session_id,
                "exercise_id": st.exercise_id,
                "set_number": st.set_number,
                "weight_kg": st.weight_kg,
                "reps": st.reps,
                "rpe": st.rpe,
                "is_completed": st.is_completed,
                "estimated_1rm": st.estimated_1rm,
                "exercise_name": st.exercise.name if st.exercise else "未知動作"
            })
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "routine_id": s.routine_id,
            "session_name": s.session_name,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration_minutes": s.duration_minutes,
            "total_volume_kg": s.total_volume_kg,
            "ai_feedback_notes": s.ai_feedback_notes,
            "created_at": s.created_at,
            "sets": sets_out
        })
    return result

@router.post("/sessions", response_model=SessionOut)
def record_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start = session_in.start_time or datetime.now(timezone.utc)
    end = session_in.end_time or datetime.now(timezone.utc)
    
    duration = session_in.duration_minutes
    if not duration and start and end:
        duration = max(1, int((end - start).total_seconds() / 60))

    total_volume = 0.0
    for s in session_in.sets:
        if s.is_completed:
            total_volume += (s.weight_kg * s.reps)

    session = WorkoutSession(
        user_id=current_user.id,
        routine_id=session_in.routine_id,
        session_name=session_in.session_name,
        start_time=start,
        end_time=end,
        duration_minutes=duration,
        total_volume_kg=round(total_volume, 1),
        ai_feedback_notes=session_in.ai_feedback_notes,
        created_at=datetime.now(timezone.utc)
    )
    db.add(session)
    db.flush()

    sets_out = []
    for s_in in session_in.sets:
        # Calculate 1RM (Epley formula: W * (1 + R / 30))
        est_1rm = 0.0
        if s_in.reps > 0 and s_in.weight_kg > 0:
            est_1rm = round(s_in.weight_kg * (1.0 + s_in.reps / 30.0), 1)

        w_set = WorkoutSet(
            session_id=session.id,
            exercise_id=s_in.exercise_id,
            set_number=s_in.set_number,
            weight_kg=s_in.weight_kg,
            reps=s_in.reps,
            rpe=s_in.rpe or 8.0,
            is_completed=s_in.is_completed,
            estimated_1rm=est_1rm
        )
        db.add(w_set)
        db.flush()
        
        ex = db.query(Exercise).filter(Exercise.id == s_in.exercise_id).first()
        sets_out.append({
            "id": w_set.id,
            "session_id": session.id,
            "exercise_id": w_set.exercise_id,
            "set_number": w_set.set_number,
            "weight_kg": w_set.weight_kg,
            "reps": w_set.reps,
            "rpe": w_set.rpe,
            "is_completed": w_set.is_completed,
            "estimated_1rm": est_1rm,
            "exercise_name": ex.name if ex else ""
        })

    db.commit()
    db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "routine_id": session.routine_id,
        "session_name": session.session_name,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "duration_minutes": session.duration_minutes,
        "total_volume_kg": session.total_volume_kg,
        "ai_feedback_notes": session.ai_feedback_notes,
        "created_at": session.created_at,
        "sets": sets_out
    }

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(WorkoutSession).filter(
        WorkoutSession.id == session_id,
        WorkoutSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="找不到此筆訓練紀錄")
    db.delete(session)
    db.commit()
    return {"message": "訓練紀錄已成功刪除"}

# 3. Muscle Recovery Heatmap Calculation
@router.get("/recovery", response_model=MuscleRecoveryOverview)
def get_muscle_recovery_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculates muscle recovery percentage based on:
    - Target muscle groups: CHEST, BACK, LEGS, SHOULDERS, ARMS, CORE
    - Time elapsed since last workout containing this muscle group
    - Recovery formula: 0~24h: 10-40% (FATIGUED), 24~48h: 40-85% (RECOVERING), >=48h or Never: 100% (RECOVERED)
    """
    muscle_groups_info = [
        {"key": "CHEST", "label": "胸大肌 (Chest)"},
        {"key": "BACK", "label": "背闊與上背 (Back)"},
        {"key": "LEGS", "label": "腿部與臀部 (Legs)"},
        {"key": "SHOULDERS", "label": "三角肌肩部 (Shoulders)"},
        {"key": "ARMS", "label": "手臂肱二/三頭 (Arms)"},
        {"key": "CORE", "label": "核心與腹肌 (Core)"}
    ]

    now = datetime.now(timezone.utc)
    results: List[MuscleRecoveryStatus] = []
    recovered_muscles = []
    fatigued_muscles = []

    for mg in muscle_groups_info:
        key = mg["key"]
        
        # Query most recent session containing this muscle group
        recent_record = (
            db.query(WorkoutSession.created_at, func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).label("volume"))
            .join(WorkoutSet, WorkoutSet.session_id == WorkoutSession.id)
            .join(Exercise, Exercise.id == WorkoutSet.exercise_id)
            .filter(
                WorkoutSession.user_id == current_user.id,
                Exercise.target_muscle_group == key,
                WorkoutSet.is_completed == True
            )
            .group_by(WorkoutSession.id, WorkoutSession.created_at)
            .order_by(desc(WorkoutSession.created_at))
            .first()
        )

        if not recent_record:
            # Never trained -> 100% recovered
            results.append(MuscleRecoveryStatus(
                muscle_group=key,
                label_zh=mg["label"],
                recovery_percentage=100,
                status="RECOVERED",
                hours_since_last_trained=None,
                last_trained_date=None,
                last_volume_kg=0.0
            ))
            recovered_muscles.append(mg["label"])
            continue

        trained_at, vol = recent_record
        if trained_at.tzinfo is None:
            trained_at = trained_at.replace(tzinfo=timezone.utc)

        hours_passed = max(0.0, (now - trained_at).total_seconds() / 3600.0)

        # Standard recovery window is 48~72 hours
        if hours_passed >= 60:
            percentage = 100
            status_str = "RECOVERED"
            recovered_muscles.append(mg["label"])
        elif hours_passed >= 36:
            percentage = int(70 + (hours_passed - 36) / 24.0 * 30)
            status_str = "RECOVERED" if percentage >= 85 else "RECOVERING"
            if percentage >= 85:
                recovered_muscles.append(mg["label"])
        elif hours_passed >= 18:
            percentage = int(40 + (hours_passed - 18) / 18.0 * 30)
            status_str = "RECOVERING"
        else:
            percentage = int(max(10, (hours_passed / 18.0) * 40))
            status_str = "FATIGUED"
            fatigued_muscles.append(mg["label"])

        results.append(MuscleRecoveryStatus(
            muscle_group=key,
            label_zh=mg["label"],
            recovery_percentage=min(100, percentage),
            status=status_str,
            hours_since_last_trained=round(hours_passed, 1),
            last_trained_date=trained_at.strftime("%Y-%m-%d %H:%M"),
            last_volume_kg=round(float(vol or 0.0), 1)
        ))

    return MuscleRecoveryOverview(
        muscles=results,
        recommended_focus=recovered_muscles if recovered_muscles else ["全身輕量適應"],
        avoid_muscles=fatigued_muscles
    )

# 4. Strength Trends & 1RM
@router.get("/stats/1rm-trends")
def get_strength_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns 1RM history for top compound movements for plotting strength progression curves.
    """
    # Key movements to track: Bench press, Squat, Deadlift, OHP, Pull-up, Row
    key_exercises = (
        db.query(Exercise)
        .filter(
            or_(
                Exercise.name.ilike("%臥推%"),
                Exercise.name.ilike("%深蹲%"),
                Exercise.name.ilike("%硬舉%"),
                Exercise.name.ilike("%肩推%"),
                Exercise.name.ilike("%引體向上%"),
                Exercise.name.ilike("%划船%")
            )
        )
        .all()
    )

    exercise_map = {e.id: e.name for e in key_exercises}
    if not exercise_map:
        return {"trends": {}}

    sets = (
        db.query(
            WorkoutSet.exercise_id,
            WorkoutSet.estimated_1rm,
            WorkoutSet.weight_kg,
            WorkoutSet.reps,
            WorkoutSession.created_at
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id.in_(list(exercise_map.keys())),
            WorkoutSet.is_completed == True,
            WorkoutSet.estimated_1rm > 0
        )
        .order_by(WorkoutSession.created_at)
        .all()
    )

    trends = {}
    for ex_id, name in exercise_map.items():
        trends[name] = []

    for s in sets:
        name = exercise_map.get(s.exercise_id)
        if name:
            trends[name].append({
                "date": s.created_at.strftime("%Y-%m-%d"),
                "estimated_1rm": s.estimated_1rm,
                "weight_kg": s.weight_kg,
                "reps": s.reps
            })

    # Filter out empty lists
    active_trends = {k: v for k, v in trends.items() if len(v) > 0}
    return {"trends": active_trends}

# 5. Weekly Comparison Dashboard & 90-Day Rolling Cleanup
@router.get("/weekly-comparison")
def get_weekly_comparison(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    # Start of this week (Monday 00:00 UTC)
    start_of_this_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_last_week = start_of_this_week - timedelta(days=7)

    this_week_sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.created_at >= start_of_this_week
    ).all()

    last_week_sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.created_at >= start_of_last_week,
        WorkoutSession.created_at < start_of_this_week
    ).all()

    this_vol = sum(s.total_volume_kg for s in this_week_sessions)
    last_vol = sum(s.total_volume_kg for s in last_week_sessions)
    this_mins = sum(s.duration_minutes for s in this_week_sessions)
    last_mins = sum(s.duration_minutes for s in last_week_sessions)

    if last_vol > 0:
        vol_change_pct = round(((this_vol - last_vol) / last_vol) * 100, 1)
    else:
        vol_change_pct = 100.0 if this_vol > 0 else 0.0

    return {
        "this_week": {
            "volume_kg": round(this_vol, 1),
            "sessions_count": len(this_week_sessions),
            "duration_minutes": this_mins,
            "start_date": start_of_this_week.strftime("%m/%d")
        },
        "last_week": {
            "volume_kg": round(last_vol, 1),
            "sessions_count": len(last_week_sessions),
            "duration_minutes": last_mins,
            "start_date": start_of_last_week.strftime("%m/%d")
        },
        "volume_change_pct": vol_change_pct,
        "is_progressing": vol_change_pct >= 0
    }

@router.post("/cleanup-90d-rolling")
def cleanup_old_workout_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    old_sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.created_at < cutoff
    ).all()
    count = len(old_sessions)
    for s in old_sessions:
        db.delete(s)
    db.commit()
    return {"message": f"已完成 90 天滾動清理，清除了 {count} 筆歷史訓練紀錄！"}

