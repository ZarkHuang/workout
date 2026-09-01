from sqlalchemy.orm import Session
from app.models.workout import Exercise

GOLDEN_EXERCISES = [
    # CHEST (胸部)
    {
        "name": "槓鈴平板臥推",
        "name_en": "Barbell Bench Press",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "SHOULDERS,ARMS",
        "equipment": "BARBELL",
        "instructions": "雙腳踩實地面，核心收緊，肩胛後收下沉。將槓鈴平穩下放至胸骨中下段，吐氣推起至手肘微彎不鎖死。"
    },
    {
        "name": "上斜啞鈴臥推",
        "name_en": "Incline Dumbbell Bench Press",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "SHOULDERS,ARMS",
        "equipment": "DUMBBELL",
        "instructions": "調整臥推椅角度約 30 度，專注刺激上胸。下放時手肘與軀幹呈約 45-60 度，向上推舉時頂峰收縮。"
    },
    {
        "name": "雙槓臂屈伸 (胸部偏向)",
        "name_en": "Chest Dip",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "ARMS,SHOULDERS",
        "equipment": "BODYWEIGHT",
        "instructions": "身體前傾約 30 度，手肘微開，感受下胸與胸大肌充分伸展後推回起始位置。"
    },
    {
        "name": "機械式坐姿胸推",
        "name_en": "Machine Chest Press",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "ARMS",
        "equipment": "MACHINE",
        "instructions": "調整椅墊高度使握把對準乳頭連線，背部貼緊靠墊，穩定推起感受胸肌擠壓。"
    },
    {
        "name": "繩索夾胸 (滑輪飛鳥)",
        "name_en": "Cable Fly / Crossover",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "SHOULDERS",
        "equipment": "CABLE",
        "instructions": "手肘保持固定微彎角度，利用胸大肌收縮帶動雙手於胸前環抱，專注離心慢放拉伸。"
    },
    {
        "name": "啞鈴平板飛鳥",
        "name_en": "Dumbbell Flat Fly",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "SHOULDERS",
        "equipment": "DUMBBELL",
        "instructions": "手肘固定微彎，雙手如同抱大樹般向兩側張開，在最底端感受胸肌大幅伸展後合攏。"
    },
    {
        "name": "標準伏地挺身",
        "name_en": "Standard Push-Up",
        "target_muscle_group": "CHEST",
        "secondary_muscle_group": "CORE,ARMS",
        "equipment": "BODYWEIGHT",
        "instructions": "雙手略比肩寬，全身成一直線，胸部貼近地面後發力推回。"
    },

    # BACK (背部)
    {
        "name": "傳統硬舉",
        "name_en": "Conventional Deadlift",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "LEGS,CORE",
        "equipment": "BARBELL",
        "instructions": "雙腳與髖同寬，槓鈴貼近小腿骨。下背保持中立不彎腰，臀部後推發力將槓鈴拉起，頂峰鎖定臀部。"
    },
    {
        "name": "引體向上 (正手)",
        "name_en": "Pull-Up",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "ARMS,CORE",
        "equipment": "BODYWEIGHT",
        "instructions": "正手握槓略寬於肩，背闊肌發力將胸口拉向單槓，下放時控制離心至手臂完全伸直。"
    },
    {
        "name": "槓鈴俯身划船",
        "name_en": "Barbell Bent-Over Row",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "ARMS,CORE",
        "equipment": "BARBELL",
        "instructions": "軀幹俯身約 45 度，背部挺直。沿著大腿將槓鈴拉向肚臍位置，肩胛骨向內夾緊。"
    },
    {
        "name": "滑輪高位下拉",
        "name_en": "Lat Pulldown",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "ARMS",
        "equipment": "CABLE",
        "instructions": "雙手寬握把手，大腿卡緊固定墊。挺胸引導把手拉至上胸位置，感受背闊肌夾緊。"
    },
    {
        "name": "單臂啞鈴划船",
        "name_en": "Single-Arm Dumbbell Row",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "ARMS,CORE",
        "equipment": "DUMBBELL",
        "instructions": "一側手膝跪於臥推椅上支撐，另一側單手持啞鈴拉向髖部，頂點短暫停頓感受背部收縮。"
    },
    {
        "name": "坐姿繩索划船",
        "name_en": "Seated Cable Row",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "ARMS",
        "equipment": "CABLE",
        "instructions": "背部挺直微挺胸，雙手將 V 字把手拉至下腹部，肩胛骨完整後收夾緊。"
    },
    {
        "name": "直臂繩索下壓",
        "name_en": "Straight-Arm Cable Pulldown",
        "target_muscle_group": "BACK",
        "secondary_muscle_group": "CORE",
        "equipment": "CABLE",
        "instructions": "手臂微彎固定，利用背闊肌獨立發力將繩索弧形下壓至大腿前側。"
    },

    # LEGS (腿部與臀部)
    {
        "name": "槓鈴頸後深蹲",
        "name_en": "Barbell Back Squat",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "CORE",
        "equipment": "BARBELL",
        "instructions": "槓鈴置於斜方肌上，雙腳與肩同寬微外八。吸氣腹壓鎖緊，屈髖屈膝下蹲至大腿低於水平，推地站起。"
    },
    {
        "name": "羅馬尼亞硬舉 (RDL)",
        "name_en": "Romanian Deadlift",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "BACK",
        "equipment": "BARBELL",
        "instructions": "膝蓋微彎固定角度，專注臀部向後推 (Hip Hinge)，感受腿後側與臀大肌強烈拉伸後頂髖收縮。"
    },
    {
        "name": "機械斜板腿推 (倒蹬機)",
        "name_en": "Leg Press",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "CORE",
        "equipment": "MACHINE",
        "instructions": "雙腳置於踏板中上方，下放至膝蓋呈 90 度，推起時膝蓋保持微彎不鎖死。"
    },
    {
        "name": "保加利亞分腿蹲",
        "name_en": "Bulgarian Split Squat",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "CORE",
        "equipment": "DUMBBELL",
        "instructions": "後腳擱在臥推椅上，前腳單腿下蹲至大腿平行地面，極佳的單側臀腿強化動作。"
    },
    {
        "name": "坐姿機械腿屈伸 (練股四頭)",
        "name_en": "Leg Extension",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "",
        "equipment": "MACHINE",
        "instructions": "膝關節對準轉軸，發力踢起至水平位置，頂峰收縮 1 秒後緩慢下放。"
    },
    {
        "name": "俯臥機械腿後勾",
        "name_en": "Lying Leg Curl",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "",
        "equipment": "MACHINE",
        "instructions": "骨盆緊貼墊子，發力勾向臀部，專注強化腿後側膕繩肌群。"
    },
    {
        "name": "站姿槓鈴提踵 (練小腿)",
        "name_en": "Standing Calf Raise",
        "target_muscle_group": "LEGS",
        "secondary_muscle_group": "",
        "equipment": "BARBELL",
        "instructions": "前腳掌踩在踏板邊緣，腳後跟下沉充分拉伸小腿，隨後高高踮起擠壓小腿腓腸肌。"
    },

    # SHOULDERS (肩部)
    {
        "name": "槓鈴站姿肩推 (OHP)",
        "name_en": "Overhead Press",
        "target_muscle_group": "SHOULDERS",
        "secondary_muscle_group": "ARMS,CORE",
        "equipment": "BARBELL",
        "instructions": "核心與臀部收緊，槓鈴從鎖骨上方垂直向上推過頭頂，頭部微後仰避開槓鈴後回位。"
    },
    {
        "name": "坐姿啞鈴肩推",
        "name_en": "Seated Dumbbell Shoulder Press",
        "target_muscle_group": "SHOULDERS",
        "secondary_muscle_group": "ARMS",
        "equipment": "DUMBBELL",
        "instructions": "坐在近 90 度靠背椅上，雙手將啞鈴從耳側向上推舉至頭頂合攏。"
    },
    {
        "name": "站姿啞鈴側平舉",
        "name_en": "Dumbbell Lateral Raise",
        "target_muscle_group": "SHOULDERS",
        "secondary_muscle_group": "",
        "equipment": "DUMBBELL",
        "instructions": "微屈膝俯身，手肘微彎引導啞鈴向兩側抬起至肩膀高度，專注雕塑三角肌中束南瓜肩。"
    },
    {
        "name": "繩索面拉 (Face Pull)",
        "name_en": "Cable Face Pull",
        "target_muscle_group": "SHOULDERS",
        "secondary_muscle_group": "BACK",
        "equipment": "CABLE",
        "instructions": "繩索高度設在面部，雙手將繩結拉向雙耳兩側同時外旋手臂，完美強化後束與肩胛健康。"
    },
    {
        "name": "俯身啞鈴飛鳥 (後束)",
        "name_en": "Bent-Over Rear Delt Fly",
        "target_muscle_group": "SHOULDERS",
        "secondary_muscle_group": "BACK",
        "equipment": "DUMBBELL",
        "instructions": "軀幹俯身平行地面，手臂微彎向兩側展開，專注三角肌後束發力。"
    },
    {
        "name": "槓鈴/啞鈴前平舉",
        "name_en": "Front Raise",
        "target_muscle_group": "SHOULDERS",
        "secondary_muscle_group": "",
        "equipment": "DUMBBELL",
        "instructions": "手臂微彎將重量垂直抬起至視線高度，控制下放速度。"
    },

    # ARMS (手臂 - 二頭與三頭)
    {
        "name": "站姿槓鈴二頭彎舉",
        "name_en": "Barbell Bicep Curl",
        "target_muscle_group": "ARMS",
        "secondary_muscle_group": "",
        "equipment": "BARBELL",
        "instructions": "大臂貼緊身體兩側不晃動，利用二頭肌收縮將槓鈴向上彎舉至胸前。"
    },
    {
        "name": "坐姿啞鈴斜板彎舉",
        "name_en": "Incline Dumbbell Curl",
        "target_muscle_group": "ARMS",
        "secondary_muscle_group": "",
        "equipment": "DUMBBELL",
        "instructions": "躺在約 60 度斜板上，手臂自然下垂拉長二頭肌長頭，發力向上彎舉。"
    },
    {
        "name": "啞鈴槌式彎舉",
        "name_en": "Hammer Curl",
        "target_muscle_group": "ARMS",
        "secondary_muscle_group": "",
        "equipment": "DUMBBELL",
        "instructions": "掌心相對持啞鈴向上彎舉，強化肱橈肌與手臂厚度。"
    },
    {
        "name": "三頭繩索高位下壓",
        "name_en": "Triceps Rope Pushdown",
        "target_muscle_group": "ARMS",
        "secondary_muscle_group": "",
        "equipment": "CABLE",
        "instructions": "大臂緊貼身體，手肘固定發力將繩索向下壓直並在底端微外展擠壓三頭肌。"
    },
    {
        "name": "仰臥槓鈴臂屈伸 (碎顱者)",
        "name_en": "Lying Triceps Extension (Skull Crusher)",
        "target_muscle_group": "ARMS",
        "secondary_muscle_group": "",
        "equipment": "BARBELL",
        "instructions": "仰躺於臥推椅，曲槓由額頭上方下放彎曲至 90 度後，純粹用三頭肌伸展推回。"
    },
    {
        "name": "窄握槓鈴臥推",
        "name_en": "Close-Grip Bench Press",
        "target_muscle_group": "ARMS",
        "secondary_muscle_group": "CHEST,SHOULDERS",
        "equipment": "BARBELL",
        "instructions": "雙手握距約與肩同寬，手肘貼緊軀幹下放，強烈刺激三頭肌外側頭與長頭。"
    },

    # CORE (核心與腹肌)
    {
        "name": "懸垂舉腿 (懸垂提膝)",
        "name_en": "Hanging Leg / Knee Raise",
        "target_muscle_group": "CORE",
        "secondary_muscle_group": "",
        "equipment": "BODYWEIGHT",
        "instructions": "雙手吊在單槓上，骨盆向後捲起帶動雙腿抬起至平行地面，強烈刺激下腹部。"
    },
    {
        "name": "健腹輪推拉",
        "name_en": "Ab Wheel Rollout",
        "target_muscle_group": "CORE",
        "secondary_muscle_group": "SHOULDERS,BACK",
        "equipment": "BODYWEIGHT",
        "instructions": "雙膝跪地，收緊腹部將滾輪向前推展至身體延伸，腹肌發力收回起始位置。"
    },
    {
        "name": "標準平板支撐 (棒式)",
        "name_en": "Plank",
        "target_muscle_group": "CORE",
        "secondary_muscle_group": "SHOULDERS",
        "equipment": "BODYWEIGHT",
        "instructions": "前臂與腳尖撐地，腹部與臀部用力夾緊維持脊椎中立，保持規律呼吸。"
    },
    {
        "name": "俄羅斯轉體",
        "name_en": "Russian Twist",
        "target_muscle_group": "CORE",
        "secondary_muscle_group": "",
        "equipment": "BODYWEIGHT",
        "instructions": "雙腳懸空或微觸地，上半身後傾約 45 度，雙手交替旋轉觸碰兩側地面，強化腹斜肌。"
    },
    {
        "name": "羅馬椅背部伸展 (挺身)",
        "name_en": "Hyperextension / Back Extension",
        "target_muscle_group": "CORE",
        "secondary_muscle_group": "LEGS,BACK",
        "equipment": "MACHINE",
        "instructions": "髖關節貼合羅馬椅墊，俯身向下至大腿拉伸後，利用豎脊肌與臀大肌發力將軀幹抬平。"
    },

    # CARDIO (有氧與心肺燃脂)
    {
        "name": "跑步機坡度快走 / 變速慢跑",
        "name_en": "Incline Treadmill Walk / Jog",
        "target_muscle_group": "CARDIO",
        "secondary_muscle_group": "LEGS,CORE",
        "equipment": "MACHINE",
        "instructions": "設定坡度 6-12%，速度 4.5-6.5 km/h，大步邁開擺臂，維持 Zone 2-3 燃脂心率 20-30 分鐘。"
    },
    {
        "name": "划船機高強度間歇 (HIIT)",
        "name_en": "Rowing Machine Intervals",
        "target_muscle_group": "CARDIO",
        "secondary_muscle_group": "BACK,LEGS,CORE",
        "equipment": "MACHINE",
        "instructions": "雙腿蹬腿發力帶動軀幹後傾，拉柄至上腹。進行衝刺 30 秒、慢划 60 秒的間歇循環。"
    },
    {
        "name": "飛輪間歇踩踏",
        "name_en": "Spin Bike Cardio",
        "target_muscle_group": "CARDIO",
        "secondary_muscle_group": "LEGS",
        "equipment": "MACHINE",
        "instructions": "保持核心穩定不晃動，交替進行高阻力站姿爬坡與高轉速平路衝刺。"
    },
    {
        "name": "戰繩交替波浪",
        "name_en": "Battle Ropes Alternating Waves",
        "target_muscle_group": "CARDIO",
        "secondary_muscle_group": "SHOULDERS,ARMS,CORE",
        "equipment": "BODYWEIGHT",
        "instructions": "微蹲鎖定核心，雙手握繩交替快速甩動製造持續波浪，全力衝刺爆發心肺。"
    },
    {
        "name": "橢圓機心肺耐力訓練",
        "name_en": "Elliptical Trainer Cardio",
        "target_muscle_group": "CARDIO",
        "secondary_muscle_group": "LEGS",
        "equipment": "MACHINE",
        "instructions": "雙手推拉把手配合腳步踏步，零關節衝擊持續燃脂 20-40 分鐘。"
    },
    {
        "name": "波比跳與登山者式循環",
        "name_en": "Burpees & Mountain Climbers",
        "target_muscle_group": "CARDIO",
        "secondary_muscle_group": "CHEST,LEGS,CORE",
        "equipment": "BODYWEIGHT",
        "instructions": "波比跳 10 次銜接登山者式 30 次，全身大肌群參與，極速拉高心率加速脂肪燃燒。"
    }
]

def seed_exercises(db: Session):
    for ex_data in GOLDEN_EXERCISES:
        existing = db.query(Exercise).filter(Exercise.name == ex_data["name"]).first()
        if not existing:
            new_ex = Exercise(
                name=ex_data["name"],
                name_en=ex_data.get("name_en"),
                target_muscle_group=ex_data["target_muscle_group"],
                secondary_muscle_group=ex_data.get("secondary_muscle_group"),
                equipment=ex_data.get("equipment", "BARBELL"),
                instructions=ex_data.get("instructions"),
                is_custom=False,
                created_by_user_id=None
            )
            db.add(new_ex)
    db.commit()
