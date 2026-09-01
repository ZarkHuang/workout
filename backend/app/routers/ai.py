import os
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.workout import Exercise, WorkoutSession, WorkoutSet
from app.models.nutrition import MealLog
from app.schemas.nutrition import NaturalLanguageDietRequest, ParsedDietResponse, ParsedFoodItem
from app.schemas.ai import (
    AIRoutineRecommendRequest, AIRoutineRecommendResponse, AIRoutineExerciseItem,
    AIChatRequest, AIChatResponse
)
from app.routers.auth import get_current_user
from app.routers.workouts import get_muscle_recovery_status

router = APIRouter(prefix="/api/ai", tags=["ai"])

def get_gemini_client():
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL or "gemini-2.5-flash",
            generation_config={"temperature": 0.3}
        )
        return model
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return None

def extract_json_from_text(text: str) -> dict:
    """Extract JSON object from text even if enclosed in markdown code blocks"""
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Try finding markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Try finding raw curly braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass

    raise ValueError("無法解析 AI 回傳的 JSON 格式")

# 1. Natural Language Diet Parser (Pure Text, Low Token)
@router.post("/parse-diet", response_model=ParsedDietResponse)
def parse_diet_text(
    request: NaturalLanguageDietRequest,
    current_user: User = Depends(get_current_user)
):
    model = get_gemini_client()
    
    # Fallback heuristic if no API Key is provided
    if not model:
        return ParsedDietResponse(
            summary_name=request.text[:50],
            total_calories=450,
            total_protein_g=35.0,
            total_carbs_g=40.0,
            total_fat_g=12.0,
            items=[
                ParsedFoodItem(
                    name=request.text,
                    portion="預設份量",
                    calories=450,
                    protein_g=35.0,
                    carbs_g=40.0,
                    fat_g=12.0
                )
            ],
            confidence_note="（未設定 Gemini API Key，此為系統預估數值，可直接手動修改）"
        )

    prompt = f"""
你是一位頂尖的運動營養學專家。請分析以下使用者輸入的飲食文字描述，精確估算各食物的熱量與三大營養素（蛋白質、碳水化合物、脂肪）：
使用者描述: "{request.text}"

請以純 JSON 格式回應，不要包含多餘說明，Schema 格式如下：
{{
  "summary_name": "餐點總結簡稱（例如：烤雞腿地瓜便當）",
  "total_calories": 520,
  "total_protein_g": 42.5,
  "total_carbs_g": 48.0,
  "total_fat_g": 11.5,
  "items": [
    {{
      "name": "好市多烤雞腿",
      "portion": "1 隻 (約 180g)",
      "calories": 280,
      "protein_g": 32.0,
      "carbs_g": 0.0,
      "fat_g": 14.0
    }},
    {{
      "name": "地瓜",
      "portion": "150g",
      "calories": 160,
      "protein_g": 2.0,
      "carbs_g": 38.0,
      "fat_g": 0.5
    }}
  ],
  "confidence_note": "評估備註（例如：以常見超商/餐廳份量估算）"
}}
"""

    try:
        response = model.generate_content(prompt)
        parsed = extract_json_from_text(response.text)
        return ParsedDietResponse(
            summary_name=parsed.get("summary_name", request.text[:30]),
            total_calories=int(parsed.get("total_calories", 0)),
            total_protein_g=float(parsed.get("total_protein_g", 0.0)),
            total_carbs_g=float(parsed.get("total_carbs_g", 0.0)),
            total_fat_g=float(parsed.get("total_fat_g", 0.0)),
            items=[ParsedFoodItem(**item) for item in parsed.get("items", [])],
            confidence_note=parsed.get("confidence_note", "")
        )
    except Exception as e:
        # Fallback on parse failure
        return ParsedDietResponse(
            summary_name=request.text[:40],
            total_calories=400,
            total_protein_g=30.0,
            total_carbs_g=40.0,
            total_fat_g=10.0,
            items=[
                ParsedFoodItem(
                    name=request.text,
                    portion="自訂份量",
                    calories=400,
                    protein_g=30.0,
                    carbs_g=40.0,
                    fat_g=10.0
                )
            ],
            confidence_note=f"AI 解析微調提示 ({str(e)})"
        )

SPLIT_TEMPLATES = {
    "CHEST": {
        "title": "胸部力量與肌肥大專攻課表",
        "target_split": "CHEST",
        "rationale": "專注胸大肌（上胸、中胸、下胸）多角度漸進式超負荷訓練，建立飽滿胸型，搭配三頭肌收尾。",
        "warmup_tips": ["彈力帶肩袖外旋 20 次", "空槓臥推熱身 15 次激活胸肌", "動態胸椎伸展 10 次"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="槓鈴平板臥推", target_muscle_group="CHEST", target_sets=4, target_reps="6-8", suggested_weight_kg=60.0, notes="正式主項，控制離心慢放 2 秒，頂峰主動夾胸"),
            AIRoutineExerciseItem(exercise_name="上斜啞鈴臥推", target_muscle_group="CHEST", target_sets=4, target_reps="8-10", suggested_weight_kg=22.0, notes="椅背約 30 度，專注強化鎖骨處上胸厚度"),
            AIRoutineExerciseItem(exercise_name="雙槓臂屈伸 (胸部偏向)", target_muscle_group="CHEST", target_sets=3, target_reps="10-12", suggested_weight_kg=0.0, notes="身體前傾 30 度，下放至下胸充分伸展"),
            AIRoutineExerciseItem(exercise_name="繩索夾胸 (滑輪飛鳥)", target_muscle_group="CHEST", target_sets=3, target_reps="12-15", suggested_weight_kg=15.0, notes="頂峰用力擠壓胸縫 1 秒，離心深度拉伸"),
            AIRoutineExerciseItem(exercise_name="三頭繩索高位下壓", target_muscle_group="ARMS", target_sets=3, target_reps="12-15", suggested_weight_kg=20.0, notes="胸推輔助肌群收尾轟炸")
        ],
        "cooldown_tips": ["胸大肌靠牆靜態伸展左右各 45 秒", "前三角肌與手臂拉伸 30 秒"]
    },
    "BACK": {
        "title": "背闊與上背深度轟炸課表",
        "target_split": "BACK",
        "rationale": "涵蓋垂直拉與水平拉黃金動作，全面雕塑 V 字倒三角背闊與中上背厚度，搭配二頭肌收尾。",
        "warmup_tips": ["滑輪極輕重量直臂下壓 15 次預先激活背闊", "貓牛式背部脊椎活動 10 次", "肩胛引體 12 次"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="滑輪高位下拉", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=50.0, notes="大腿卡緊固定墊，挺胸拉至上胸，頂峰收縮背闊"),
            AIRoutineExerciseItem(exercise_name="槓鈴俯身划船", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=50.0, notes="俯身 45 度背打直，槓鈴貼大腿拉向肚臍"),
            AIRoutineExerciseItem(exercise_name="單臂啞鈴划船", target_muscle_group="BACK", target_sets=3, target_reps="10-12", suggested_weight_kg=22.0, notes="單側拉向髖部，底部完全伸展背闊"),
            AIRoutineExerciseItem(exercise_name="坐姿繩索划船", target_muscle_group="BACK", target_sets=3, target_reps="10-12", suggested_weight_kg=45.0, notes="肩胛骨向脊椎方向完整內夾"),
            AIRoutineExerciseItem(exercise_name="站姿槓鈴二頭彎舉", target_muscle_group="ARMS", target_sets=3, target_reps="10-12", suggested_weight_kg=25.0, notes="拉力輔助肌群最後泵感加強")
        ],
        "cooldown_tips": ["吊單槓背闊肌重力伸展 40 秒", "嬰兒式背部與下背拉伸 60 秒"]
    },
    "BACK_WIDTH": {
        "title": "V字倒三角·闊背寬度垂直拉專攻課表",
        "target_split": "BACK",
        "rationale": "專注於闊背肌肌纖維走向，以垂直拉與單臂拉伸為主軸，最大化背部展開寬度與翅膀視覺效果。",
        "warmup_tips": ["滑輪直臂下壓 20 次預先激活闊背", "懸垂肩胛下壓 12 次", "動態背部伸展"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="滑輪高位下拉 (寬握)", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=50.0, notes="專注闊背外側拉伸與收縮，大臂內夾"),
            AIRoutineExerciseItem(exercise_name="滑輪高位下拉 (窄握反手/V把)", target_muscle_group="BACK", target_sets=4, target_reps="10-12", suggested_weight_kg=45.0, notes="長運動行程，強化闊背下部深度收縮"),
            AIRoutineExerciseItem(exercise_name="站姿繩索直臂下壓", target_muscle_group="BACK", target_sets=4, target_reps="12-15", suggested_weight_kg=20.0, notes="孤立闊背肌，手肘微彎鎖定，頂峰擠壓 1 秒"),
            AIRoutineExerciseItem(exercise_name="單臂啞鈴划船", target_muscle_group="BACK", target_sets=3, target_reps="10-12", suggested_weight_kg=22.0, notes="弧線拉向髖關節，底部充分放展"),
            AIRoutineExerciseItem(exercise_name="啞鈴斜板二頭彎舉", target_muscle_group="ARMS", target_sets=3, target_reps="10-12", suggested_weight_kg=12.0, notes="二頭肌長頭拉伸收尾")
        ],
        "cooldown_tips": ["雙手抓住立柱側身拉伸闊背肌 45 秒", "吊單槓懸垂拉伸 40 秒"]
    },
    "BACK_THICKNESS": {
        "title": "重裝裝甲·上背中背厚度划船專攻課表",
        "target_split": "BACK",
        "rationale": "以大重量水平划船與肩胛內收為主軸，深度轟炸菱形肌、中下斜方肌與豎脊肌，打造立體厚實背部。",
        "warmup_tips": ["空槓俯身划船 15 次抓背部發力感", "繩索面拉 15 次激活上背", "胸椎活動度旋轉"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="槓鈴俯身划船", target_muscle_group="BACK", target_sets=4, target_reps="6-8", suggested_weight_kg=55.0, notes="厚度主項，核心吸滿，肘部帶動拉向肚臍夾緊上背"),
            AIRoutineExerciseItem(exercise_name="坐姿繩索划船", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=50.0, notes="頂峰肩胛骨完全後夾 1 秒，離心控制慢放"),
            AIRoutineExerciseItem(exercise_name="單臂啞鈴划船", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=24.0, notes="大重量單側划船，專注背部擠壓"),
            AIRoutineExerciseItem(exercise_name="繩索面拉 (Face Pull)", target_muscle_group="SHOULDERS", target_sets=4, target_reps="12-15", suggested_weight_kg=20.0, notes="手肘拉高外展，強化後束、斜方中下束與菱形肌"),
            AIRoutineExerciseItem(exercise_name="站姿槓鈴二頭彎舉", target_muscle_group="ARMS", target_sets=3, target_reps="10-12", suggested_weight_kg=25.0, notes="二頭肌爆發收尾")
        ],
        "cooldown_tips": ["抱胸拱背圓背拉伸 45 秒", "貓牛式伸展放鬆脊椎 60 秒"]
    },
    "CHEST_UPPER": {
        "title": "鎖骨飽滿·上胸力量與厚度專攻課表",
        "target_split": "CHEST",
        "rationale": "著重強化上胸（鎖骨端胸大肌），改善胸型上部空缺，打造立體厚實鎧甲胸肌。",
        "warmup_tips": ["彈力帶肩袖外旋 20 次", "上斜空槓推舉 15 次", "動態擴胸 15 次"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="上斜槓鈴臥推", target_muscle_group="CHEST", target_sets=4, target_reps="6-8", suggested_weight_kg=50.0, notes="椅背約 30 度，槓鈴下落至鎖骨下方 2 公分"),
            AIRoutineExerciseItem(exercise_name="上斜啞鈴臥推", target_muscle_group="CHEST", target_sets=4, target_reps="8-10", suggested_weight_kg=20.0, notes="頂峰主動夾胸，離心感受上胸強烈拉伸"),
            AIRoutineExerciseItem(exercise_name="槓鈴平板臥推", target_muscle_group="CHEST", target_sets=3, target_reps="8-10", suggested_weight_kg=55.0, notes="複合維持中胸厚度"),
            AIRoutineExerciseItem(exercise_name="低位繩索上拉夾胸 (滑輪飛鳥)", target_muscle_group="CHEST", target_sets=4, target_reps="12-15", suggested_weight_kg=12.5, notes="滑輪置於最低處，雙手沿上斜角度向上夾緊胸肌上部"),
            AIRoutineExerciseItem(exercise_name="三頭繩索高位下壓", target_muscle_group="ARMS", target_sets=3, target_reps="12-15", suggested_weight_kg=20.0, notes="推力三頭收尾")
        ],
        "cooldown_tips": ["手扶門框上胸伸展 45 秒", "胸大肌靠牆伸展 30 秒"]
    },
    "SHOULDERS": {
        "title": "三角肌前中後束立體雕塑課表",
        "target_split": "SHOULDERS",
        "rationale": "大重量推舉突破肩部推力極限，中束與後束多角度孤立雕塑立體南瓜肩。",
        "warmup_tips": ["輕量啞鈴側平舉 20 次", "彈力帶 Face Pull 15 次激活肩袖", "Y-T-W 穩定熱身"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="槓鈴站姿肩推 (OHP)", target_muscle_group="SHOULDERS", target_sets=4, target_reps="6-8", suggested_weight_kg=40.0, notes="核心與臀部鎖死，垂直推過頭頂"),
            AIRoutineExerciseItem(exercise_name="坐姿啞鈴肩推", target_muscle_group="SHOULDERS", target_sets=4, target_reps="8-10", suggested_weight_kg=18.0, notes="手肘保持在身體前側 30 度，頂峰不撞擊"),
            AIRoutineExerciseItem(exercise_name="站姿啞鈴側平舉", target_muscle_group="SHOULDERS", target_sets=4, target_reps="12-15", suggested_weight_kg=8.0, notes="手肘微彎引導抬起至肩高，頂點停頓 0.5 秒"),
            AIRoutineExerciseItem(exercise_name="繩索面拉 (Face Pull)", target_muscle_group="SHOULDERS", target_sets=4, target_reps="12-15", suggested_weight_kg=20.0, notes="繩結拉向雙耳同時外旋手臂，強化後束與肩胛"),
            AIRoutineExerciseItem(exercise_name="俯身啞鈴飛鳥 (後束)", target_muscle_group="SHOULDERS", target_sets=3, target_reps="12-15", suggested_weight_kg=7.0, notes="俯身平行地面，專注三角肌後束擠壓")
        ],
        "cooldown_tips": ["手臂橫過胸前三角肌靜態拉伸左右各 30 秒", "背後扣手開肩伸展 45 秒"]
    },
    "LEGS": {
        "title": "臀腿下肢力量與爆發力突破課表",
        "target_split": "LEGS",
        "rationale": "以深蹲與 RDL 雙黃金複合動作為核心，前後側平衡刺激股四頭與臀大肌、膕繩肌群。",
        "warmup_tips": ["自重深蹲 15 次激活髖關節", "弓箭步轉體拉伸各 10 次", "大腿內收與外展動態活動"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="槓鈴頸後深蹲", target_muscle_group="LEGS", target_sets=4, target_reps="6-8", suggested_weight_kg=70.0, notes="正式主項，吸滿腹壓下蹲至大腿低於水平"),
            AIRoutineExerciseItem(exercise_name="羅馬尼亞硬舉 (RDL)", target_muscle_group="LEGS", target_sets=4, target_reps="8-10", suggested_weight_kg=60.0, notes="膝蓋微彎臀部後推，專注腿後側與臀大肌強烈拉伸"),
            AIRoutineExerciseItem(exercise_name="機械斜板腿推 (倒蹬機)", target_muscle_group="LEGS", target_sets=3, target_reps="10-12", suggested_weight_kg=120.0, notes="腳踩踏板中上方，頂點膝蓋微彎不鎖死"),
            AIRoutineExerciseItem(exercise_name="坐姿機械腿屈伸 (練股四頭)", target_muscle_group="LEGS", target_sets=3, target_reps="12-15", suggested_weight_kg=40.0, notes="頂峰完全鎖定收縮 1 秒後控制下放"),
            AIRoutineExerciseItem(exercise_name="站姿槓鈴提踵 (練小腿)", target_muscle_group="LEGS", target_sets=3, target_reps="15-20", suggested_weight_kg=40.0, notes="腳後跟充分下沉拉伸後高高踮起")
        ],
        "cooldown_tips": ["股四頭肌站姿後拉伸各 45 秒", "坐姿前折腿後側拉伸 60 秒", "小腿靠牆推伸 45 秒"]
    },
    "PUSH": {
        "title": "上肢推力胸肩三頭整合突破課表",
        "target_split": "PUSH",
        "rationale": "整合胸大肌、前中三角肌與肱三頭肌等推力肌群，高效建立上肢推力鏈。",
        "warmup_tips": ["肩袖外旋 15 次", "伏地挺身 10 次", "空槓推舉 12 次"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="槓鈴平板臥推", target_muscle_group="CHEST", target_sets=4, target_reps="6-8", suggested_weight_kg=60.0, notes="推力主項，控制離心慢放"),
            AIRoutineExerciseItem(exercise_name="上斜啞鈴臥推", target_muscle_group="CHEST", target_sets=3, target_reps="8-10", suggested_weight_kg=22.0, notes="強化上胸飽滿度"),
            AIRoutineExerciseItem(exercise_name="坐姿啞鈴肩推", target_muscle_group="SHOULDERS", target_sets=3, target_reps="8-10", suggested_weight_kg=18.0, notes="三角肌前束與中束推力"),
            AIRoutineExerciseItem(exercise_name="站姿啞鈴側平舉", target_muscle_group="SHOULDERS", target_sets=4, target_reps="12-15", suggested_weight_kg=8.0, notes="雕塑中束肩寬"),
            AIRoutineExerciseItem(exercise_name="三頭繩索高位下壓", target_muscle_group="ARMS", target_sets=3, target_reps="12-15", suggested_weight_kg=20.0, notes="三頭外側頭完全鎖定")
        ],
        "cooldown_tips": ["胸肩拉伸 45 秒", "三頭肌過頭拉伸 30 秒"]
    },
    "PULL": {
        "title": "上肢拉力背闊二頭立體加厚課表",
        "target_split": "PULL",
        "rationale": "整合背闊肌、斜方肌、三角肌後束與肱二頭肌，打造強韌上肢拉力鏈。",
        "warmup_tips": ["直臂下壓 15 次", "肩胛骨後收活動 15 次"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="滑輪高位下拉", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=50.0, notes="垂直拉主項，大臂拉向腰際"),
            AIRoutineExerciseItem(exercise_name="槓鈴俯身划船", target_muscle_group="BACK", target_sets=4, target_reps="8-10", suggested_weight_kg=50.0, notes="水平拉主項，背部夾緊"),
            AIRoutineExerciseItem(exercise_name="單臂啞鈴划船", target_muscle_group="BACK", target_sets=3, target_reps="10-12", suggested_weight_kg=22.0, notes="單側獨立拉伸"),
            AIRoutineExerciseItem(exercise_name="繩索面拉 (Face Pull)", target_muscle_group="SHOULDERS", target_sets=3, target_reps="12-15", suggested_weight_kg=20.0, notes="三角肌後束與上背"),
            AIRoutineExerciseItem(exercise_name="站姿槓鈴二頭彎舉", target_muscle_group="ARMS", target_sets=3, target_reps="10-12", suggested_weight_kg=25.0, notes="二頭肌泵感收尾")
        ],
        "cooldown_tips": ["懸垂背部伸展 40 秒", "手臂二頭前側拉伸 30 秒"]
    },
    "CARDIO": {
        "title": "心肺耐力與高效燃脂有氧課表",
        "target_split": "CARDIO",
        "rationale": "結合恆速心肺 (Zone 2) 與高強度間歇 (HIIT)，最大化熱量赤字與心肺耐力，促進全身血液循環與肌肉主動恢復。",
        "warmup_tips": ["慢速原地踏步與關節環繞 3 分鐘", "開合跳 20 次激活全身心率", "動態腿部擺盪各 15 次"],
        "exercises": [
            AIRoutineExerciseItem(exercise_name="跑步機坡度快走 / 變速慢跑", target_muscle_group="CARDIO", target_sets=1, target_reps="20分鐘", suggested_weight_kg=0.0, notes="設定坡度 8-10%，速度 5.0 km/h，維持穩態燃脂心率"),
            AIRoutineExerciseItem(exercise_name="划船機高強度間歇 (HIIT)", target_muscle_group="CARDIO", target_sets=5, target_reps="30秒衝刺", suggested_weight_kg=0.0, notes="全力衝刺 30 秒，慢划休息 60 秒，循環 5 組"),
            AIRoutineExerciseItem(exercise_name="飛輪間歇踩踏", target_muscle_group="CARDIO", target_sets=4, target_reps="45秒衝刺", suggested_weight_kg=0.0, notes="站姿高阻力爬坡與高速平路衝刺交替"),
            AIRoutineExerciseItem(exercise_name="波比跳與登山者式循環", target_muscle_group="CARDIO", target_sets=3, target_reps="15次", suggested_weight_kg=0.0, notes="無間歇切換，全身大肌群參與極速燃脂"),
            AIRoutineExerciseItem(exercise_name="戰繩交替波浪", target_muscle_group="CARDIO", target_sets=3, target_reps="30秒", suggested_weight_kg=0.0, notes="核心鎖緊，雙手高速甩動爆發心肺")
        ],
        "cooldown_tips": ["股四頭肌與小腿靜態拉伸各 45 秒", "嬰兒式深呼吸放鬆 60 秒降低心率"]
    }
}

# 2. AI Workout Recommender (Dedicated Body-Part Splits)
@router.post("/recommend-workout", response_model=AIRoutineRecommendResponse)
def recommend_workout(
    req: AIRoutineRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    recovery = get_muscle_recovery_status(current_user=current_user, db=db)
    
    # Recent 3 workout sessions
    recent_sessions = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == current_user.id)
        .order_by(WorkoutSession.created_at.desc())
        .limit(3)
        .all()
    )
    recent_history_text = ", ".join([f"{s.session_name} ({s.created_at.strftime('%m/%d')})" for s in recent_sessions]) or "無近期訓練紀錄"

    # Recovery text
    recovery_summary = "; ".join([f"{m.label_zh}: {m.status} ({m.recovery_percentage}%)" for m in recovery.muscles])

    # Determine targeted body-part split (CHEST, BACK, SHOULDERS, LEGS, PUSH, PULL, CARDIO)
    focus_pref = (req.focus_preference or "").upper().strip()
    if focus_pref in SPLIT_TEMPLATES:
        target_focus = focus_pref
    else:
        # Auto-detect best split: candidate from 4 major body-part splits
        major_candidates = ["CHEST", "BACK", "SHOULDERS", "LEGS"]
        muscle_map = {m.muscle_group: m for m in recovery.muscles}
        
        # Sort candidates: 1. highest recovery percentage, 2. longest hours since last trained (None -> float('inf'))
        best_candidate = "CHEST"
        best_score = (-1, -1)
        for cand in major_candidates:
            m_stat = muscle_map.get(cand)
            rec_pct = m_stat.recovery_percentage if m_stat else 100
            hours_ago = m_stat.hours_since_last_trained if (m_stat and m_stat.hours_since_last_trained is not None) else 999.0
            score = (rec_pct, hours_ago)
            if score > best_score:
                best_score = score
                best_candidate = cand
        target_focus = best_candidate

    target_labels = {
        "CHEST": "胸部專攻",
        "BACK": "背部專攻",
        "SHOULDERS": "肩部專攻",
        "LEGS": "腿部專攻",
        "PUSH": "推力日 (胸/肩/三頭)",
        "PULL": "拉力日 (背/二頭)",
        "CARDIO": "有氧燃脂日 (心肺/HIIT)"
    }
    target_label_zh = target_labels.get(target_focus, "胸部專攻")

    sub_focus_key = (req.sub_focus or "").upper().strip()
    custom_notes = req.custom_notes or req.special_conditions or ""

    # Match sub-focus template if available
    template_key = target_focus
    if target_focus == "BACK" and sub_focus_key in ["WIDTH", "LAT_WIDTH"]:
        template_key = "BACK_WIDTH"
    elif target_focus == "BACK" and sub_focus_key in ["THICKNESS", "UPPER_BACK"]:
        template_key = "BACK_THICKNESS"
    elif target_focus == "CHEST" and sub_focus_key in ["UPPER", "UPPER_CHEST"]:
        template_key = "CHEST_UPPER"

    fallback_template = SPLIT_TEMPLATES.get(template_key, SPLIT_TEMPLATES.get(target_focus, SPLIT_TEMPLATES["CHEST"]))

    sub_focus_desc = "全面均衡"
    if sub_focus_key in ["WIDTH", "LAT_WIDTH"]:
        sub_focus_desc = "【闊背肌寬度 (V字倒三角垂直拉為主：寬握下拉/引體向上/直臂下壓)】"
    elif sub_focus_key in ["THICKNESS", "UPPER_BACK"]:
        sub_focus_desc = "【上背中背厚度 (水平划船為主：槓鈴划船/單臂划船/坐姿划船/面拉)】"
    elif sub_focus_key in ["UPPER", "UPPER_CHEST"]:
        sub_focus_desc = "【鎖骨上胸飽滿度 (上斜推舉/低位滑輪上拉飛鳥)】"
    elif sub_focus_key in ["LATERAL", "LATERAL_DELT"]:
        sub_focus_desc = "【三角肌中束肩寬 (啞鈴/繩索側平舉)】"
    elif sub_focus_key in ["QUADS"]:
        sub_focus_desc = "【股四頭肌前側力量 (深蹲/腿推/腿屈伸)】"
    elif sub_focus_key in ["GLUTES", "HAMSTRINGS"]:
        sub_focus_desc = "【臀大肌與後鏈伸展 (RDL/臀推/腿彎舉)】"

    model = get_gemini_client()
    if not model:
        return AIRoutineRecommendResponse(
            routine_title=fallback_template["title"],
            target_split=fallback_template["target_split"],
            rationale=f"系統依據您的恢復狀態（{target_label_zh}已充分修復）與專攻偏好（{sub_focus_desc}）為您規劃深度課表。{fallback_template['rationale']}",
            warmup_tips=fallback_template["warmup_tips"],
            exercises=fallback_template["exercises"],
            cooldown_tips=fallback_template["cooldown_tips"]
        )

    prompt = f"""
你是一位頂尖的 NSCA-CSCS 力量與健美體態專家。
【重要排課原則】
學員嚴格採用「單一部位分化訓練 (Body-Part Split: 胸、肩、背、腿)」！
⚠️ 嚴格禁止在同一次訓練中混搭互相衝突的大肌群（例如：絕對不可胸部與背部混練、絕對不可胸部與大腿深蹲混練）！
今日指定專攻部位為：【{target_label_zh} ({target_focus})】。

【學員特定子維度 / 客製需求】
- 🎯 進階子專攻重點: {sub_focus_desc}
- 💬 學員客製許願/特殊偏好: {custom_notes or '無'}

【跨部位衝突客製與教練專業提醒原則】
若學員在客製許願中指定了與今日主目標部位不一致的動作（例如：今日選【胸部專攻】，但備註【想要引體向上】）：
1. 彈性滿足：可在課表最後 1 動作或熱身中為其加入該動作滿足願望。
2. 專業教練備註（重要）：在 rationale（推薦理由）及該動作的 notes（備註）中，明確說明：「💡 教練提醒：已依您的願望加入【指定動作】，但此動作屬於【非今日主目標部位】，建議作為輕量輔助/拉伸完成，避免累積過多疲勞影響後續分化訓練的修復週期！」

請設計 4-5 個專屬於該部位的黃金訓練動作（可含 1 個協同輔助肌群，如練胸可搭三頭、練背可搭二頭、練肩可搭後束、練腿可搭小腿，80% 以上動作必須為【{target_label_zh}】並緊密貼合指定子維度）。

【學員數據】
- 今日目標部位: {target_label_zh} ({target_focus})
- 性別: {profile.gender if profile else 'MALE'}
- 訓練目標: {profile.fitness_goal if profile else 'BULKING'}
- 各部位修復度: {recovery_summary}
- 近期歷史: {recent_history_text}
- 今日可用時間: {req.duration_minutes} 分鐘
- 可用器材: {req.available_equipment}
- 備註: {req.special_conditions or '無特別限制'}

請嚴格以純 JSON 格式回應：
{{
  "routine_title": "{target_label_zh} - {sub_focus_desc.replace('【', '').replace('】', '')}客製課表",
  "target_split": "{target_focus}",
  "rationale": "今日推薦理由（若有跨部位許願，在此包含專業教練溫馨提醒，2-3 句話）",
  "warmup_tips": ["熱身動作 1", "熱身動作 2"],
  "exercises": [
    {{
      "exercise_name": "動作名稱（如：槓鈴平板臥推）",
      "target_muscle_group": "{target_focus if target_focus in ['CHEST', 'BACK', 'SHOULDERS', 'LEGS'] else 'CHEST'}",
      "target_sets": 4,
      "target_reps": "8-10",
      "suggested_weight_kg": 50.0,
      "notes": "訓練要領與離心控制叮嚀"
    }}
  ],
  "cooldown_tips": ["收操伸展 1", "收操伸展 2"]
}}
"""

    try:
        response = model.generate_content(prompt)
        parsed = extract_json_from_text(response.text)
        return AIRoutineRecommendResponse(
            routine_title=parsed.get("routine_title", fallback_template["title"]),
            target_split=parsed.get("target_split", target_focus),
            rationale=parsed.get("rationale", fallback_template["rationale"]),
            warmup_tips=parsed.get("warmup_tips", fallback_template["warmup_tips"]),
            exercises=[AIRoutineExerciseItem(**ex) for ex in parsed.get("exercises", [])] if parsed.get("exercises") else fallback_template["exercises"],
            cooldown_tips=parsed.get("cooldown_tips", fallback_template["cooldown_tips"])
        )
    except Exception as e:
        print(f"AI Recommend fallback triggered: {e}")
        return AIRoutineRecommendResponse(
            routine_title=fallback_template["title"],
            target_split=fallback_template["target_split"],
            rationale=f"根據您的肌群修復數據（{target_label_zh}已 100% 充血恢復），今日推薦進行單一部位深度訓練。{fallback_template['rationale']}",
            warmup_tips=fallback_template["warmup_tips"],
            exercises=fallback_template["exercises"],
            cooldown_tips=fallback_template["cooldown_tips"]
        )

# 3. Stateless Context-Aware AI Coach Chat (Zero DB Storage, 1-Click Adoption)
@router.post("/chat", response_model=AIChatResponse)
def ai_coach_chat(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    recovery = get_muscle_recovery_status(current_user=current_user, db=db)
    
    # Today nutrition
    today_meals = db.query(MealLog).filter(MealLog.user_id == current_user.id, MealLog.meal_date == datetime.now(timezone.utc).date()).all()
    today_cals = sum(m.calories for m in today_meals)
    today_p = sum(m.protein_g for m in today_meals)
    target_cals = profile.target_calories if profile else 2400
    target_p = profile.target_protein_g if profile else 140.0

    model = get_gemini_client()
    if not model:
        return AIChatResponse(
            reply="您好！我是 FitPulse 智慧隨身教練。請在後端設定 `GEMINI_API_KEY` 以啟動強大的 Gemini AI 智能對話與即時菜單生成功能！",
            suggested_routine=None
        )

    # Build context-rich prompt
    system_context = f"""
你是一位具備運動科學與營養學專業的頂尖私人健身教練「FitPulse AI 教練」。你的語氣積極、專業、鼓勵且條理清晰。

【當前學員即時資訊】
- 稱呼: {current_user.name}
- 性別: {profile.gender if profile else 'MALE'}
- 體重: {profile.current_weight_kg if profile else 70} kg (目標: {profile.target_weight_kg if profile else 72} kg)
- 健身目標: {profile.fitness_goal if profile else 'BULKING'}
- 今日營養進度: 已攝取 {today_cals} kcal (目標 {target_cals} kcal), 蛋白質已攝取 {today_p:.1f}g (目標 {target_p:.1f}g)
- 肌肉恢復狀態: {', '.join([f'{m.label_zh}: {m.status}' for m in recovery.muscles])}

【學員問題】
"{req.message}"

【重要指示】
1. 若學員詢問「今天練什麼」、「排課」、「換動作菜單」、「幫我安排訓練」：
   - 請嚴格遵循【單一部位分化訓練 (胸/肩/背/腿)】或【推/拉/腿】原則。
   - ⚠️ 嚴禁在同一次訓練中混搭互相衝突的大肌群（例如：絕不可胸部與背部混練、絕不可胸部與大腿深蹲混練）！
   - 請優先選擇學員當前已充分修復（RECOVERED）的單一肌群作為今日專攻，並在回覆中附帶專屬的結構化 JSON 菜單區塊，格式為：
```json
{{
  "routine_title": "課表名稱（如：胸部力量突破課表）",
  "target_split": "CHEST/BACK/SHOULDERS/LEGS/PUSH/PULL",
  "rationale": "排課簡述",
  "warmup_tips": ["熱身 1", "熱身 2"],
  "exercises": [
    {{
      "exercise_name": "動作名稱",
      "target_muscle_group": "CHEST",
      "target_sets": 4,
      "target_reps": "8-10",
      "suggested_weight_kg": 50,
      "notes": "備註"
    }}

  ]
}}
```
這樣系統會自動為學員生成【👉 一鍵採用此課表並開始訓練】按鈕！
2. 若為一般飲食、動作要領、痠痛疑問，則給予簡潔有力、條理分明的專業建議即可。
"""

    try:
        response = model.generate_content(system_context)
        reply_text = response.text

        # Check if there is an embedded JSON routine in the response
        suggested_routine = None
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", reply_text)
        if match:
            try:
                routine_data = json.loads(match.group(1))
                if "exercises" in routine_data and len(routine_data["exercises"]) > 0:
                    suggested_routine = AIRoutineRecommendResponse(
                        routine_title=routine_data.get("routine_title", "AI 教練推薦課表"),
                        target_split=routine_data.get("target_split", "FULL_BODY"),
                        rationale=routine_data.get("rationale", "教練對話客製菜單"),
                        warmup_tips=routine_data.get("warmup_tips", []),
                        exercises=[AIRoutineExerciseItem(**ex) for ex in routine_data.get("exercises", [])],
                        cooldown_tips=routine_data.get("cooldown_tips", [])
                    )
            except Exception:
                pass

        return AIChatResponse(
            reply=reply_text,
            suggested_routine=suggested_routine
        )
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg or "400" in err_msg or "PERMISSION_DENIED" in err_msg:
            hint = "您的 Google Gemini API Key 無效或格式不符（有效的官方 Key 通常以 `AIzaSy` 開頭）。\n請前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請一組 API Key，並貼入 `backend/.env` 的 `GEMINI_API_KEY` 欄位。"
        elif "not found" in err_msg.lower() or "404" in err_msg:
            hint = f"模型名稱 `{settings.GEMINI_MODEL}` 尚未支援或不存在，建議在 `backend/.env` 設定 `GEMINI_MODEL=gemini-1.5-flash`。"
        else:
            hint = f"AI 連線異常 ({err_msg})。"
        
        return AIChatResponse(
            reply=f"🤖 **教練系統提示**：\n{hint}\n\n💡 *提示：在設定好 API Key 前，您仍可正常使用運動記錄、課表庫與營養進度追蹤功能！*",
            suggested_routine=None
        )
