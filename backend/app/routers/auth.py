from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token, oauth2_scheme
from app.models.user import User, UserProfile
from app.schemas.user import UserRegister, UserLogin, Token, UserOut, UserProfileUpdate, UserProfileOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

def calculate_tdee_and_macros(gender: str, age: int, height_cm: float, weight_kg: float, goal: str, activity_level: str):
    """
    Calculate BMR using Mifflin-St Jeor equation and determine TDEE and Macro targets
    """
    # 1. BMR
    if gender.upper() == "FEMALE":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    # 2. Activity Multiplier
    activity_multipliers = {
        "SEDENTARY": 1.2,       # 久坐/少動
        "LIGHT": 1.375,         # 輕度活動 (每週 1-3 天)
        "MODERATE": 1.55,       # 中度活動 (每週 3-5 天)
        "ACTIVE": 1.725,        # 高度活動 (每週 6-7 天)
        "VERY_ACTIVE": 1.9      # 極高強度 / 體力工作
    }
    multiplier = activity_multipliers.get(activity_level.upper(), 1.55)
    tdee = bmr * multiplier

    # 3. Adjust for Fitness Goal
    goal_upper = goal.upper()
    if goal_upper == "BULKING": # 增肌 (盈餘 250 kcal)
        target_calories = int(tdee + 250)
        protein_g = round(weight_kg * 2.0, 1) # 2.0g / kg
        fat_cals = target_calories * 0.25
        fat_g = round(fat_cals / 9, 1)
        remaining_cals = target_calories - (protein_g * 4 + fat_cals)
        carbs_g = max(0, round(remaining_cals / 4, 1))
    elif goal_upper == "CUTTING": # 減脂 (赤字 400 kcal)
        target_calories = max(1200, int(tdee - 400))
        protein_g = round(weight_kg * 2.2, 1) # 2.2g / kg 減脂保肌
        fat_cals = target_calories * 0.20
        fat_g = round(fat_cals / 9, 1)
        remaining_cals = target_calories - (protein_g * 4 + fat_cals)
        carbs_g = max(0, round(remaining_cals / 4, 1))
    else: # MAINTENANCE 維持體態
        target_calories = int(tdee)
        protein_g = round(weight_kg * 1.8, 1)
        fat_cals = target_calories * 0.25
        fat_g = round(fat_cals / 9, 1)
        remaining_cals = target_calories - (protein_g * 4 + fat_cals)
        carbs_g = max(0, round(remaining_cals / 4, 1))

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": target_calories,
        "target_protein_g": protein_g,
        "target_carbs_g": carbs_g,
        "target_fat_g": fat_g
    }

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登入憑證無效或已過期，請重新登入",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="此電子郵件已被註冊")
    
    hashed_pwd = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_pwd
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize default profile with TDEE
    default_stats = calculate_tdee_and_macros(
        gender="MALE", age=26, height_cm=175.0, weight_kg=70.0,
        goal="BULKING", activity_level="MODERATE"
    )
    
    profile = UserProfile(
        user_id=user.id,
        gender="MALE",
        age=26,
        height_cm=175.0,
        current_weight_kg=70.0,
        target_weight_kg=72.0,
        experience_level="INTERMEDIATE",
        fitness_goal="BULKING",
        activity_level="MODERATE",
        target_calories=default_stats["target_calories"],
        target_protein_g=default_stats["target_protein_g"],
        target_carbs_g=default_stats["target_carbs_g"],
        target_fat_g=default_stats["target_fat_g"]
    )
    db.add(profile)
    db.commit()

    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="電子郵件或密碼錯誤")
    
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.profile
    if not profile:
        # Create profile if not exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    calc = calculate_tdee_and_macros(
        gender=profile.gender,
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.current_weight_kg,
        goal=profile.fitness_goal,
        activity_level=profile.activity_level
    )
    
    profile_dict = {
        "id": profile.id,
        "user_id": profile.user_id,
        "gender": profile.gender,
        "age": profile.age,
        "height_cm": profile.height_cm,
        "current_weight_kg": profile.current_weight_kg,
        "target_weight_kg": profile.target_weight_kg,
        "body_fat_percentage": profile.body_fat_percentage,
        "experience_level": profile.experience_level,
        "fitness_goal": profile.fitness_goal,
        "activity_level": profile.activity_level,
        "target_calories": profile.target_calories,
        "target_protein_g": profile.target_protein_g,
        "target_carbs_g": profile.target_carbs_g,
        "target_fat_g": profile.target_fat_g,
        "bmr": calc["bmr"],
        "tdee": calc["tdee"],
        "updated_at": profile.updated_at
    }

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at,
        "profile": profile_dict
    }

@router.put("/profile", response_model=UserProfileOut)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    update_fields = profile_data.model_dump(exclude_unset=True)
    
    # Check if we need to auto-recalculate target calories & macros
    should_recalc = any(k in update_fields for k in ["gender", "age", "height_cm", "current_weight_kg", "fitness_goal", "activity_level"])
    
    for key, value in update_fields.items():
        if value is not None:
            setattr(profile, key, value)
            
    if should_recalc and "target_calories" not in update_fields:
        calc = calculate_tdee_and_macros(
            gender=profile.gender,
            age=profile.age,
            height_cm=profile.height_cm,
            weight_kg=profile.current_weight_kg,
            goal=profile.fitness_goal,
            activity_level=profile.activity_level
        )
        profile.target_calories = calc["target_calories"]
        profile.target_protein_g = calc["target_protein_g"]
        profile.target_carbs_g = calc["target_carbs_g"]
        profile.target_fat_g = calc["target_fat_g"]

    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)

    calc = calculate_tdee_and_macros(
        gender=profile.gender,
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.current_weight_kg,
        goal=profile.fitness_goal,
        activity_level=profile.activity_level
    )

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "gender": profile.gender,
        "age": profile.age,
        "height_cm": profile.height_cm,
        "current_weight_kg": profile.current_weight_kg,
        "target_weight_kg": profile.target_weight_kg,
        "body_fat_percentage": profile.body_fat_percentage,
        "experience_level": profile.experience_level,
        "fitness_goal": profile.fitness_goal,
        "activity_level": profile.activity_level,
        "target_calories": profile.target_calories,
        "target_protein_g": profile.target_protein_g,
        "target_carbs_g": profile.target_carbs_g,
        "target_fat_g": profile.target_fat_g,
        "bmr": calc["bmr"],
        "tdee": calc["tdee"],
        "updated_at": profile.updated_at
    }
