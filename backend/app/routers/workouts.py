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

def normalize_muscle_group(raw_mg: Optional[str], fallback: str = "CHEST") -> str:
    if not raw_mg:
        return fallback
    s = raw_mg.strip().upper()
    if s in ["CHEST", "BACK", "LEGS", "SHOULDERS", "ARMS", "CORE", "CARDIO"]:
        return s
    if any(k in s for k in ["LEG", "QUAD", "GLUTE", "HAMSTRING", "CALF", "LOWER", "腿", "臀", "股", "膕", "小腿", "下肢", "深蹲"]):
        return "LEGS"
    if any(k in s for k in ["BACK", "LAT", "PULL", "ROW", "背", "闊背", "斜方", "菱形", "拉"]):
        return "BACK"
    if any(k in s for k in ["SHOULDER", "DELT", "肩", "三角肌"]):
        return "SHOULDERS"
    if any(k in s for k in ["ARM", "BICEP", "TRICEP", "手", "二頭", "三頭", "臂"]):
        return "ARMS"
    if any(k in s for k in ["CORE", "ABS", "ABDOM", "核", "腹", "腰"]):
        return "CORE"
    if any(k in s for k in ["CARDIO", "HIIT", "AEROBIC", "有氧", "心肺", "燃脂"]):
        return "CARDIO"
    if any(k in s for k in ["CHEST", "PEC", "PUSH", "胸", "推"]):
        return "CHEST"
    return fallback

COMMON_EXERCISE_ALIASES = {
    "槓鈴深蹲": "槓鈴頸後深蹲",
    "頸後深蹲": "槓鈴頸後深蹲",
    "自由深蹲": "槓鈴頸後深蹲",
    "深蹲": "槓鈴頸後深蹲",
    "機械腿推": "機械斜板腿推 (倒蹬機)",
    "斜板腿推": "機械斜板腿推 (倒蹬機)",
    "倒蹬機": "機械斜板腿推 (倒蹬機)",
    "器械腿推": "機械斜板腿推 (倒蹬機)",
    "腿推": "機械斜板腿推 (倒蹬機)",
    "坐姿腿屈伸": "坐姿機械腿屈伸 (練股四頭)",
    "機械腿屈伸": "坐姿機械腿屈伸 (練股四頭)",
    "器械腿屈伸": "坐姿機械腿屈伸 (練股四頭)",
    "腿屈伸": "坐姿機械腿屈伸 (練股四頭)",
    "俯臥腿彎舉": "俯臥機械腿彎舉 (練腿後側)",
    "坐姿腿彎舉": "俯臥機械腿彎舉 (練腿後側)",
    "機械腿彎舉": "俯臥機械腿彎舉 (練腿後側)",
    "器械腿彎舉": "俯臥機械腿彎舉 (練腿後側)",
    "腿彎舉": "俯臥機械腿彎舉 (練腿後側)",
    "勾腿": "俯臥機械腿彎舉 (練腿後側)",
    "站姿提踵": "站姿槓鈴提踵 (練小腿)",
    "槓鈴提踵": "站姿槓鈴提踵 (練小腿)",
    "啞鈴提踵": "站姿槓鈴提踵 (練小腿)",
    "機械提踵": "站姿槓鈴提踵 (練小腿)",
    "提踵": "站姿槓鈴提踵 (練小腿)",
    "羅馬尼亞硬舉": "羅馬尼亞硬舉 (RDL)",
    "啞鈴羅馬尼亞硬舉": "羅馬尼亞硬舉 (RDL)",
    "rdl": "羅馬尼亞硬舉 (RDL)",
    "傳統硬舉": "傳統槓鈴硬舉",
    "槓鈴硬舉": "傳統槓鈴硬舉",
    "硬舉": "傳統槓鈴硬舉",
    "分腿蹲": "保加利亞分腿蹲",
    "啞鈴分腿蹲": "保加利亞分腿蹲",
    "臀推": "槓鈴臀推 (Hip Thrust)",
    "槓鈴臀推": "槓鈴臀推 (Hip Thrust)",
    "哈克深蹲": "哈克深蹲 (Hack Squat)",
    "槓鈴臥推": "槓鈴平板臥推",
    "平板槓鈴臥推": "槓鈴平板臥推",
    "平板臥推": "槓鈴平板臥推",
    "啞鈴臥推": "啞鈴平板臥推",
    "繩索夾胸": "繩索夾胸 (滑輪飛鳥)",
    "滑輪飛鳥": "繩索夾胸 (滑輪飛鳥)",
    "滑輪夾胸": "繩索夾胸 (滑輪飛鳥)",
    "雙槓臂屈伸": "雙槓臂屈伸 (胸部偏向)",
    "高位下拉": "滑輪高位下拉",
    "寬握高位下拉": "滑輪高位下拉",
    "槓鈴划船": "槓鈴俯身划船",
    "俯身槓鈴划船": "槓鈴俯身划船",
    "俯身划船": "槓鈴俯身划船",
    "站姿肩推": "槓鈴站姿肩推 (OHP)",
    "槓鈴肩推": "槓鈴站姿肩推 (OHP)",
    "啞鈴肩推": "坐姿啞鈴肩推",
    "啞鈴側平舉": "站姿啞鈴側平舉",
    "側平舉": "站姿啞鈴側平舉",
    "繩索面拉": "繩索面拉 (Face Pull)",
    "面拉": "繩索面拉 (Face Pull)",
    "後束飛鳥": "俯身啞鈴飛鳥 (後束)",
    "俯身飛鳥": "俯身啞鈴飛鳥 (後束)",
    "槓鈴二頭彎舉": "站姿槓鈴二頭彎舉",
    "槓鈴彎舉": "站姿槓鈴二頭彎舉",
    "三頭下壓": "三頭繩索高位下壓",
    "繩索下壓": "三頭繩索高位下壓",
}

def infer_muscle_from_name(name: str, fallback: str = "CHEST") -> str:
    if not name:
        return fallback
    if any(k in name for k in ["深蹲", "分腿蹲", "腿推", "倒蹬", "腿屈伸", "腿彎舉", "勾腿", "提踵", "臀推", "硬舉", "RDL", "弓箭步", "臀", "腿"]):
        return "LEGS"
    if any(k in name for k in ["引體", "下拉", "划船", "直臂下壓", "背"]):
        return "BACK"
    if any(k in name for k in ["肩推", "側平舉", "前平舉", "面拉", "後束", "聳肩", "肩"]):
        return "SHOULDERS"
    if any(k in name for k in ["彎舉", "三頭", "二頭", "臂屈伸", "碎顱"]):
        return "ARMS"
    if any(k in name for k in ["捲腹", "棒式", "抬腿", "核心", "腹"]):
        return "CORE"
    if any(k in name for k in ["跑步", "飛輪", "戰繩", "波比", "有氧", "划船機"]):
        return "CARDIO"
    if any(k in name for k in ["臥推", "夾胸", "飛鳥", "伏地挺身", "胸"]):
        return "CHEST"
    return fallback

def resolve_or_create_exercise(
    db: Session,
    user_id: int,
    exercise_id: Optional[int] = None,
    exercise_name: Optional[str] = None,
    target_muscle_group: Optional[str] = None
) -> Exercise:
    clean_name = (exercise_name or "").strip()
    norm_target = _normalize_ex_name(clean_name)
    alias_canonical = COMMON_EXERCISE_ALIASES.get(clean_name.lower()) or COMMON_EXERCISE_ALIASES.get(norm_target)

    # 1. If exercise_id is provided, check if it exists and matches exercise_name (when exercise_name is given)
    ex_by_id = None
    if exercise_id:
        ex_by_id = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if ex_by_id:
            if not clean_name:
                return ex_by_id
            norm_db = _normalize_ex_name(ex_by_id.name)
            if (
                ex_by_id.name == clean_name
                or (alias_canonical and ex_by_id.name == alias_canonical)
                or norm_db == norm_target
                or (len(norm_db) >= 2 and len(norm_target) >= 2 and (norm_db in norm_target or norm_target in norm_db))
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

        # 2a. Exact name or alias canonical match
        for c in candidates:
            if c.name.strip().lower() == clean_name.lower():
                return c
            if alias_canonical and c.name.strip() == alias_canonical:
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
        inferred_mg = infer_muscle_from_name(clean_name, fallback="")
        muscle = normalize_muscle_group(
            inferred_mg or target_muscle_group,
            fallback=(ex_by_id.target_muscle_group if ex_by_id else "CHEST")
        )
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

def repair_corrupted_sessions(db: Session, user_id: Optional[int] = None):
    """
    Repairs historical sessions where an old frontend bug mapped all exercises in a
    non-chest session (e.g., Leg workout '腿部'/'臀腿', Back workout '背部', Shoulder workout '肩部')
    to '槓鈴平板臥推' (id=1) or '保加利亞分腿蹲'.
    Preserves the user's exact recorded weights, reps, set_numbers, and 1RM!
    """
    split_default_names = {
        "LEGS": ["槓鈴頸後深蹲", "羅馬尼亞硬舉 (RDL)", "機械斜板腿推 (倒蹬機)", "坐姿機械腿屈伸 (練股四頭)", "站姿槓鈴提踵 (練小腿)"],
        "BACK": ["滑輪高位下拉", "槓鈴俯身划船", "單臂啞鈴划船", "坐姿繩索划船", "站姿槓鈴二頭彎舉"],
        "SHOULDERS": ["槓鈴站姿肩推 (OHP)", "坐姿啞鈴肩推", "站姿啞鈴側平舉", "繩索面拉 (Face Pull)", "俯身啞鈴飛鳥 (後束)"],
    }

    query = db.query(WorkoutSession)
    if user_id is not None:
        query = query.filter(WorkoutSession.user_id == user_id)
    sessions = query.all()

    changed = False
    for sess in sessions:
        if not sess.sets:
            continue
        title = (sess.session_name or "").upper()
        target_split = None
        if any(k in title for k in ["腿", "臀", "下肢", "股四頭", "後鏈", "LEGS", "QUADS", "GLUTES"]):
            target_split = "LEGS"
        elif any(k in title for k in ["背", "闊背", "拉", "BACK", "PULL"]):
            target_split = "BACK"
        elif any(k in title for k in ["肩", "三角肌", "SHOULDER"]):
            target_split = "SHOULDERS"

        if not target_split:
            continue

        ex_names_in_sess = set(st.exercise.name for st in sess.sets if st.exercise)
        # Check if all sets in this session were collapsed into a single wrong fallback exercise
        if len(ex_names_in_sess) == 1:
            only_name = next(iter(ex_names_in_sess))
            is_corrupted_bench = (only_name == "槓鈴平板臥推" and target_split != "CHEST")
            is_corrupted_split_squat = (only_name == "保加利亞分腿蹲" and len(sess.sets) > 4)
            if not (is_corrupted_bench or is_corrupted_split_squat):
                continue

            # Group sets into exercise blocks Whenever set_number resets to 1 (or every 3-4 sets if monotonic)
            blocks = []
            current_block = []
            for st in sess.sets:
                if current_block and st.set_number <= current_block[-1].set_number:
                    blocks.append(current_block)
                    current_block = [st]
                else:
                    current_block.append(st)
            if current_block:
                blocks.append(current_block)

            # If set_number was monotonic across the whole session, chunk by 3 sets
            if len(blocks) == 1 and len(sess.sets) >= 6:
                blocks = [sess.sets[i:i+3] for i in range(0, len(sess.sets), 3)]

            template_names = split_default_names[target_split]
            for b_idx, block in enumerate(blocks):
                target_ex_name = template_names[b_idx % len(template_names)]
                resolved = resolve_or_create_exercise(
                    db=db,
                    user_id=sess.user_id,
                    exercise_id=None,
                    exercise_name=target_ex_name,
                    target_muscle_group=target_split
                )
                for s_idx, st in enumerate(block):
                    st.exercise_id = resolved.id
                    st.set_number = s_idx + 1
                changed = True

    if changed:
        db.commit()

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
    repair_corrupted_sessions(db=db, user_id=current_user.id)
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
    repair_corrupted_sessions(db=db, user_id=current_user.id)
    """
    Scientific Muscle Recovery Model (24h - 72h based on muscle group size & volume):
    - CORE (核心/腹肌): 24h full recovery window
    - SHOULDERS (肩部) / ARMS (二三頭手臂): 36h full recovery window
    - CHEST (胸大肌) / BACK (背闊與上背): 48h standard full recovery window (up to 60h for high volume)
    - LEGS (臀腿大肌群 + CNS): 72h full recovery window
    Status thresholds:
    - < 45%: FATIGUED (急性疲勞發炎期，建議休息避免過度訓練)
    - 45% ~ 84%: RECOVERING (組織超補償修復中，可輕度活動或再休數小時)
    - >= 85%: RECOVERED (已充分修復，可進行高強度漸進超負荷訓練)
    """
    muscle_groups_info = [
        {"key": "CHEST", "label": "胸大肌 (Chest)", "base_hours": 48},
        {"key": "BACK", "label": "背闊與上背 (Back)", "base_hours": 48},
        {"key": "LEGS", "label": "腿部與臀部 (Legs)", "base_hours": 72},
        {"key": "SHOULDERS", "label": "三角肌肩部 (Shoulders)", "base_hours": 36},
        {"key": "ARMS", "label": "手臂肱二/三頭 (Arms)", "base_hours": 36},
        {"key": "CORE", "label": "核心與腹肌 (Core)", "base_hours": 24}
    ]

    now = datetime.now(timezone.utc)
    results: List[MuscleRecoveryStatus] = []
    recovered_muscles = []
    fatigued_muscles = []

    for mg in muscle_groups_info:
        key = mg["key"]
        base_target_hours = mg["base_hours"]
        
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
                hours_until_recovered=0.0,
                target_recovery_hours=base_target_hours,
                last_trained_date=None,
                last_volume_kg=0.0
            ))
            recovered_muscles.append(mg["label"])
            continue

        trained_at, vol = recent_record
        if trained_at.tzinfo is None:
            trained_at = trained_at.replace(tzinfo=timezone.utc)

        vol_float = float(vol or 0.0)
        # Adjust target recovery window slightly if session volume for this muscle was very high (> 6000kg)
        target_hours = base_target_hours
        if vol_float >= 6000 and base_target_hours < 72:
            target_hours = min(72, base_target_hours + 12)

        hours_passed = max(0.0, (now - trained_at).total_seconds() / 3600.0)

        # Linear + supercompensation recovery curve from 10% (at 0h) to 100% (at target_hours)
        if hours_passed >= target_hours:
            percentage = 100
        else:
            percentage = int(min(100, max(10, round(10 + (hours_passed / float(target_hours)) * 90))))

        # Remaining hours until 85% (ready to train hard again) / 100% (full recovery)
        ready_threshold_hours = target_hours * (75.0 / 90.0)  # hours needed to reach 85%
        hours_remaining = max(0.0, round(ready_threshold_hours - hours_passed, 1))

        if percentage >= 85:
            status_str = "RECOVERED"
            recovered_muscles.append(mg["label"])
            hours_remaining = 0.0
        elif percentage >= 45:
            status_str = "RECOVERING"
        else:
            status_str = "FATIGUED"
            fatigued_muscles.append(mg["label"])

        results.append(MuscleRecoveryStatus(
            muscle_group=key,
            label_zh=mg["label"],
            recovery_percentage=min(100, percentage),
            status=status_str,
            hours_since_last_trained=round(hours_passed, 1),
            hours_until_recovered=hours_remaining,
            target_recovery_hours=target_hours,
            last_trained_date=trained_at.strftime("%Y-%m-%d %H:%M"),
            last_volume_kg=round(vol_float, 1)
        ))

    # -------------------------------------------------------------
    # Calculate User Workout Streak & Dynamic Avatar Aura Evolution Mode
    # -------------------------------------------------------------
    user_sessions = (
        db.query(WorkoutSession.created_at)
        .filter(WorkoutSession.user_id == current_user.id)
        .order_by(desc(WorkoutSession.created_at))
        .all()
    )

    streak_days = 0
    days_since_last_workout = None
    suggested_aura = "SLOTH"

    if user_sessions:
        unique_dates = sorted(
            list({s.created_at.date() for s in user_sessions if s.created_at}),
            reverse=True
        )

        most_recent_session_dt = user_sessions[0].created_at
        if most_recent_session_dt.tzinfo is None:
            most_recent_session_dt = most_recent_session_dt.replace(tzinfo=timezone.utc)

        days_since_last_workout = round(
            max(0.0, (now - most_recent_session_dt).total_seconds() / 86400.0), 1
        )

        today_d = now.date()
        latest_d = unique_dates[0]
        days_gap = (today_d - latest_d).days

        # Streak calculation: If trained today (gap == 0) or yesterday (gap == 1), streak is active
        if days_gap <= 1:
            check_d = latest_d
            for d in unique_dates:
                if d == check_d:
                    streak_days += 1
                    check_d -= timedelta(days=1)
                elif d < check_d:
                    break

        # Aura Evolution Thresholds:
        # - Idle >= 3 days: SLOTH (偷懶坐地模式，光環熄滅)
        # - Streak >= 7: LV3 (⚡ 極意神境)
        # - Streak >= 3: LV2 (🔥 超級賽亞人爆氣)
        # - Streak >= 1: LV1 (✨ 晨曦微光)
        # - Otherwise (e.g. days_gap == 2, streak broken): OFF (⚪ 純淨模式)
        if days_gap >= 3:
            suggested_aura = "SLOTH"
        elif streak_days >= 7:
            suggested_aura = "LV3"
        elif streak_days >= 3:
            suggested_aura = "LV2"
        elif streak_days >= 1:
            suggested_aura = "LV1"
        else:
            suggested_aura = "OFF"
    else:
        # 0 workout sessions recorded -> SLOTH (偷懶未開練模式)
        suggested_aura = "SLOTH"

    return MuscleRecoveryOverview(
        muscles=results,
        recommended_focus=recovered_muscles if recovered_muscles else ["全身輕量適應 / 主動恢復"],
        avoid_muscles=fatigued_muscles,
        streak_days=streak_days,
        days_since_last_workout=days_since_last_workout,
        suggested_aura=suggested_aura
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
    repair_corrupted_sessions(db=db, user_id=current_user.id)
    sets = (
        db.query(
            WorkoutSet.session_id,
            WorkoutSet.exercise_id,
            Exercise.name.label("exercise_name"),
            Exercise.target_muscle_group.label("target_muscle_group"),
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
            or_(WorkoutSet.estimated_1rm > 0, WorkoutSet.weight_kg > 0, WorkoutSet.reps > 0)
        )
        .order_by(WorkoutSession.created_at, WorkoutSet.id)
        .all()
    )

    # Group by exercise name and session_id (take max 1RM per session for clean progression curve)
    session_best = {}
    exercise_order = []
    exercise_meta = {}
    for s in sets:
        ex_name = s.exercise_name
        if ex_name not in exercise_order:
            exercise_order.append(ex_name)
        exercise_meta[ex_name] = {
            "exercise_id": s.exercise_id,
            "target_muscle_group": s.target_muscle_group or "CHEST"
        }
        calc_1rm = float(s.estimated_1rm or 0.0)
        if calc_1rm <= 0 and (s.weight_kg or 0) > 0 and (s.reps or 0) > 0:
            calc_1rm = round(s.weight_kg * (1.0 + s.reps / 30.0), 1)
        elif calc_1rm <= 0 and (s.reps or 0) > 0:
            # Bodyweight or reps-only movement fallback so it still plots on trend chart
            calc_1rm = float(s.reps)

        key = (ex_name, s.session_id)
        if key not in session_best or calc_1rm > session_best[key]["estimated_1rm"]:
            session_best[key] = {
                "date": s.created_at.strftime("%Y-%m-%d"),
                "estimated_1rm": calc_1rm,
                "weight_kg": float(s.weight_kg or 0.0),
                "reps": int(s.reps or 0),
                "target_muscle_group": s.target_muscle_group or "CHEST"
            }

    trends = {name: [] for name in exercise_order}
    for (ex_name, _), record in session_best.items():
        trends[ex_name].append(record)

    active_trends = {k: v for k, v in trends.items() if len(v) > 0}
    return {"trends": active_trends, "exercise_meta": exercise_meta}

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

