from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import re
from app.core.database import get_db
from app.models.user import User
from app.models.workout import Exercise, WorkoutRoutine, RoutineExercise, WorkoutSession, WorkoutSet
from app.schemas.workout import (
    RoutineCreate, RoutineOut, SessionCreate, SessionOut,
    MuscleRecoveryOverview, MuscleRecoveryStatus
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/workouts", tags=["workouts"])

def _normalize_ex_name(name: str) -> str:
    if not name:
        return ""
    cleaned = re.sub(r"[\(（].*?[\)）]", "", name)
    cleaned = re.sub(r"[\s\-_·/]+", "", cleaned)
    return cleaned.strip().lower()

def resolve_or_create_exercise(
    db: Session,
    user_id: int,
    exercise_id: Optional[int] = None,
    exercise_name: Optional[str] = None,
    target_muscle_group: Optional[str] = None
) -> Exercise:
    clean_name = (exercise_name or "").strip()
    norm_target = _normalize_ex_name(clean_name)

    # 1. If exercise_id is provided, check if it exists and matches exercise_name (when exercise_name is given)
    ex_by_id = None
    if exercise_id:
        ex_by_id = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if ex_by_id:
            if not clean_name:
                return ex_by_id
            norm_db = _normalize_ex_name(ex_by_id.name)
            if ex_by_id.name == clean_name or norm_db == norm_target or (
                len(norm_db) >= 2 and len(norm_target) >= 2 and (norm_db in norm_target or norm_target in norm_db)
            ):
                return ex_by_id

    # 2. If exercise_name is provided, try matching against available exercises
    if clean_name:
        candidates = db.query(Exercise).filter(
            or_(
                Exercise.is_custom == False,
                Exercise.created_by_user_id == user_id
            )
        ).order_by(Exercise.id).all()

        # 2a. Exact name match
        for c in candidates:
            if c.name.strip().lower() == clean_name.lower():
                return c

        # 2b. Normalized name match (ignoring parentheses like (RDL), (OHP), (練股四頭))
        if norm_target:
            for c in candidates:
                if _normalize_ex_name(c.name) == norm_target:
                    return c

            # 2c. Substring match on normalized name (minimum 3 chars to avoid false positives)
            for c in candidates:
                norm_c = _normalize_ex_name(c.name)
                if len(norm_c) >= 3 and len(norm_target) >= 3:
                    if norm_c in norm_target or norm_target in norm_c:
                        return c

        # 3. Not found in library -> Auto-create custom exercise for this user so their exact exercise name is preserved!
        muscle = (target_muscle_group or (ex_by_id.target_muscle_group if ex_by_id else "CHEST")).upper().strip()
        if muscle not in ["CHEST", "BACK", "LEGS", "SHOULDERS", "ARMS", "CORE", "CARDIO"]:
            muscle = "CHEST"
        new_ex = Exercise(
            name=clean_name,
            target_muscle_group=muscle,
            equipment="BARBELL",
            is_custom=True,
            created_by_user_id=user_id
        )
        db.add(new_ex)
        db.flush()
        return new_ex

    if ex_by_id:
        return ex_by_id

    fallback = db.query(Exercise).order_by(Exercise.id).first()
    if fallback:
        return fallback

    new_ex = Exercise(
        name="自訂訓練動作",
        target_muscle_group="CHEST",
        equipment="BARBELL",
        is_custom=True,
        created_by_user_id=user_id
    )
    db.add(new_ex)
    db.flush()
    return new_ex

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
        target_split=(routine_in.target_split or "FULL_BODY").upper()
    )
    db.add(routine)
    db.flush()

    for idx, ex_in in enumerate(routine_in.exercises):
        resolved_ex = resolve_or_create_exercise(
            db=db,
            user_id=current_user.id,
            exercise_id=ex_in.exercise_id,
            exercise_name=ex_in.exercise_name,
            target_muscle_group=ex_in.target_muscle_group
        )
        re_item = RoutineExercise(
            routine_id=routine.id,
            exercise_id=resolved_ex.id,
            target_sets=ex_in.target_sets,
            target_reps=ex_in.target_reps,
            order_index=idx
        )
        db.add(re_item)
    
    db.commit()
    db.refresh(routine)
    return routine

@router.put("/routines/{routine_id}", response_model=RoutineOut)
def update_routine(
    routine_id: int,
    routine_in: RoutineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    routine = db.query(WorkoutRoutine).filter(
        WorkoutRoutine.id == routine_id,
        WorkoutRoutine.user_id == current_user.id
    ).first()
    if not routine:
        raise HTTPException(status_code=404, detail="找不到課表")

    routine.title = routine_in.title
    routine.description = routine_in.description
    if routine_in.target_split:
        routine.target_split = routine_in.target_split.upper()

    # Replace routine exercises
    db.query(RoutineExercise).filter(RoutineExercise.routine_id == routine.id).delete()
    db.flush()

    for idx, ex_in in enumerate(routine_in.exercises):
        resolved_ex = resolve_or_create_exercise(
            db=db,
            user_id=current_user.id,
            exercise_id=ex_in.exercise_id,
            exercise_name=ex_in.exercise_name,
            target_muscle_group=ex_in.target_muscle_group
        )
        re_item = RoutineExercise(
            routine_id=routine.id,
            exercise_id=resolved_ex.id,
            target_sets=ex_in.target_sets,
            target_reps=ex_in.target_reps,
            order_index=idx
        )
        db.add(re_item)

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
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == current_user.id)
        .order_by(desc(WorkoutSession.created_at), desc(WorkoutSession.id))
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

def _ensure_utc(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@router.post("/sessions", response_model=SessionOut)
def record_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now_utc = datetime.now(timezone.utc)
    start = _ensure_utc(session_in.start_time) if session_in.start_time else now_utc
    end = _ensure_utc(session_in.end_time) if session_in.end_time else now_utc
    
    duration = session_in.duration_minutes
    if not duration and start and end:
        duration = max(1, int((end - start).total_seconds() / 60))

    total_volume = 0.0
    for s in session_in.sets:
        if s.is_completed:
            total_volume += (s.weight_kg * s.reps)

    # Use start_time date if user selected a specific past/custom date, otherwise now_utc
    record_created_at = start if session_in.start_time else now_utc

    session = WorkoutSession(
        user_id=current_user.id,
        routine_id=session_in.routine_id,
        session_name=session_in.session_name,
        start_time=start,
        end_time=end,
        duration_minutes=duration,
        total_volume_kg=round(total_volume, 1),
        ai_feedback_notes=session_in.ai_feedback_notes,
        created_at=record_created_at
    )
    db.add(session)
    db.flush()

    created_sets = []
    for s_in in session_in.sets:
        resolved_ex = resolve_or_create_exercise(
            db=db,
            user_id=current_user.id,
            exercise_id=s_in.exercise_id,
            exercise_name=s_in.exercise_name,
            target_muscle_group=s_in.target_muscle_group
        )

        # Calculate 1RM (Epley formula: W * (1 + R / 30))
        est_1rm = 0.0
        if s_in.reps > 0 and s_in.weight_kg > 0:
            est_1rm = round(s_in.weight_kg * (1.0 + s_in.reps / 30.0), 1)

        w_set = WorkoutSet(
            session_id=session.id,
            exercise_id=resolved_ex.id,
            set_number=s_in.set_number,
            weight_kg=s_in.weight_kg,
            reps=s_in.reps,
            rpe=s_in.rpe or 8.0,
            is_completed=s_in.is_completed,
            estimated_1rm=est_1rm
        )
        db.add(w_set)
        created_sets.append((w_set, resolved_ex))

    db.flush()

    # If this session was started from a saved routine, keep the routine's exercises/sets/reps synced with the user's actual recorded performance
    if session.routine_id and created_sets:
        routine = db.query(WorkoutRoutine).filter(
            WorkoutRoutine.id == session.routine_id,
            WorkoutRoutine.user_id == current_user.id
        ).first()
        if routine:
            grouped_by_ex = {}
            ex_order = []
            for w_set, resolved_ex in created_sets:
                if resolved_ex.id not in grouped_by_ex:
                    grouped_by_ex[resolved_ex.id] = []
                    ex_order.append(resolved_ex.id)
                grouped_by_ex[resolved_ex.id].append(w_set)

            for ex_id in ex_order:
                sets_for_ex = grouped_by_ex[ex_id]
                re_row = db.query(RoutineExercise).filter(
                    RoutineExercise.routine_id == routine.id,
                    RoutineExercise.exercise_id == ex_id
                ).first()
                best_reps = max((int(s.reps or 0) for s in sets_for_ex), default=10) or 10
                if re_row:
                    re_row.target_sets = len(sets_for_ex)
                    re_row.target_reps = best_reps

    sets_out = []
    for w_set, resolved_ex in created_sets:
        sets_out.append({
            "id": w_set.id,
            "session_id": session.id,
            "exercise_id": w_set.exercise_id,
            "set_number": w_set.set_number,
            "weight_kg": w_set.weight_kg,
            "reps": w_set.reps,
            "rpe": w_set.rpe,
            "is_completed": w_set.is_completed,
            "estimated_1rm": w_set.estimated_1rm,
            "exercise_name": resolved_ex.name if resolved_ex else ""
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

@router.put("/sessions/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(WorkoutSession).filter(
        WorkoutSession.id == session_id,
        WorkoutSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="找不到此筆訓練紀錄")

    session.session_name = session_in.session_name
    if session_in.duration_minutes is not None:
        session.duration_minutes = session_in.duration_minutes
    if session_in.start_time is not None:
        session.start_time = _ensure_utc(session_in.start_time)
    if session_in.end_time is not None:
        session.end_time = _ensure_utc(session_in.end_time)
    if session_in.ai_feedback_notes is not None:
        session.ai_feedback_notes = session_in.ai_feedback_notes

    total_volume = 0.0
    for s in session_in.sets:
        if s.is_completed:
            total_volume += (s.weight_kg * s.reps)
    session.total_volume_kg = round(total_volume, 1)

    # Replace sets
    db.query(WorkoutSet).filter(WorkoutSet.session_id == session.id).delete()
    db.flush()

    created_sets = []
    for s_in in session_in.sets:
        resolved_ex = resolve_or_create_exercise(
            db=db,
            user_id=current_user.id,
            exercise_id=s_in.exercise_id,
            exercise_name=s_in.exercise_name,
            target_muscle_group=s_in.target_muscle_group
        )
        est_1rm = 0.0
        if s_in.reps > 0 and s_in.weight_kg > 0:
            est_1rm = round(s_in.weight_kg * (1.0 + s_in.reps / 30.0), 1)

        w_set = WorkoutSet(
            session_id=session.id,
            exercise_id=resolved_ex.id,
            set_number=s_in.set_number,
            weight_kg=s_in.weight_kg,
            reps=s_in.reps,
            rpe=s_in.rpe or 8.0,
            is_completed=s_in.is_completed,
            estimated_1rm=est_1rm
        )
        db.add(w_set)
        created_sets.append((w_set, resolved_ex))

    db.flush()

    # If this session was started from a saved routine, keep the routine's exercises/sets/reps synced with the user's actual recorded performance
    if session.routine_id and created_sets:
        routine = db.query(WorkoutRoutine).filter(
            WorkoutRoutine.id == session.routine_id,
            WorkoutRoutine.user_id == current_user.id
        ).first()
        if routine:
            grouped_by_ex = {}
            ex_order = []
            for w_set, resolved_ex in created_sets:
                if resolved_ex.id not in grouped_by_ex:
                    grouped_by_ex[resolved_ex.id] = []
                    ex_order.append(resolved_ex.id)
                grouped_by_ex[resolved_ex.id].append(w_set)

            for ex_id in ex_order:
                sets_for_ex = grouped_by_ex[ex_id]
                re_row = db.query(RoutineExercise).filter(
                    RoutineExercise.routine_id == routine.id,
                    RoutineExercise.exercise_id == ex_id
                ).first()
                best_reps = max((int(s.reps or 0) for s in sets_for_ex), default=10) or 10
                if re_row:
                    re_row.target_sets = len(sets_for_ex)
                    re_row.target_reps = best_reps

    sets_out = []
    for w_set, resolved_ex in created_sets:
        sets_out.append({
            "id": w_set.id,
            "session_id": session.id,
            "exercise_id": w_set.exercise_id,
            "set_number": w_set.set_number,
            "weight_kg": w_set.weight_kg,
            "reps": w_set.reps,
            "rpe": w_set.rpe,
            "is_completed": w_set.is_completed,
            "estimated_1rm": w_set.estimated_1rm,
            "exercise_name": resolved_ex.name if resolved_ex else ""
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
    Returns 1RM history for all movements trained by the user for plotting strength progression curves.
    """
    sets = (
        db.query(
            WorkoutSet.session_id,
            WorkoutSet.exercise_id,
            Exercise.name.label("exercise_name"),
            WorkoutSet.estimated_1rm,
            WorkoutSet.weight_kg,
            WorkoutSet.reps,
            WorkoutSession.created_at
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .join(Exercise, WorkoutSet.exercise_id == Exercise.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.is_completed == True,
            WorkoutSet.estimated_1rm > 0
        )
        .order_by(WorkoutSession.created_at, WorkoutSet.id)
        .all()
    )

    # Group by exercise name and session_id (take max 1RM per session for clean progression curve)
    session_best = {}
    exercise_order = []
    for s in sets:
        ex_name = s.exercise_name
        if ex_name not in exercise_order:
            exercise_order.append(ex_name)
        key = (ex_name, s.session_id)
        if key not in session_best or s.estimated_1rm > session_best[key]["estimated_1rm"]:
            session_best[key] = {
                "date": s.created_at.strftime("%Y-%m-%d"),
                "estimated_1rm": s.estimated_1rm,
                "weight_kg": s.weight_kg,
                "reps": s.reps
            }

    trends = {name: [] for name in exercise_order}
    for (ex_name, _), record in session_best.items():
        trends[ex_name].append(record)

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

