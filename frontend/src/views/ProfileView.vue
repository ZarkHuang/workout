<template>
  <div class="pb-28 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-black text-slate-900">個人體態中心</h1>
        <p class="text-xs text-slate-400">動態 TDEE 計算 · 宏觀目標與身體設定</p>
      </div>
      <button
        @click="handleLogout"
        class="py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-600 font-bold text-xs active:scale-95 transition-all flex items-center gap-1"
      >
        <LogOut class="w-3.5 h-3.5" />
        <span>登出</span>
      </button>
    </div>

    <!-- TDEE & BMR Summary Live Banner -->
    <div class="card-apple bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white border-0 shadow-lg p-4 space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-emerald-400" />
          <span class="text-xs font-bold text-slate-300">Mifflin-St Jeor 即時代謝試算</span>
        </div>
        <span class="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 rounded-full font-bold">
          {{ getGoalText(form.fitness_goal) }} · {{ form.gender === 'FEMALE' ? '女性' : '男性' }}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-3 pt-1">
        <div class="p-2.5 rounded-xl bg-white/10">
          <div class="text-[10px] text-slate-400">基礎代謝 (BMR)</div>
          <div class="text-lg font-black text-white">
            {{ liveStats.bmr }} <span class="text-xs font-normal text-slate-400">kcal</span>
          </div>
        </div>
        <div class="p-2.5 rounded-xl bg-white/10">
          <div class="text-[10px] text-slate-400">每日總消耗 (TDEE)</div>
          <div class="text-lg font-black text-emerald-400">
            {{ liveStats.tdee }} <span class="text-xs font-normal text-slate-400">kcal</span>
          </div>
        </div>
      </div>

      <div class="p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
        <div class="flex items-center gap-1.5">
          <Flame class="w-4 h-4 text-amber-400" />
          <span class="text-slate-300">建議每日攝取熱量</span>
        </div>
        <span class="font-black text-amber-400 text-base">{{ form.target_calories }} kcal</span>
      </div>
    </div>

    <!-- Profile Form -->
    <div class="card-apple space-y-4">
      <h3 class="font-bold text-slate-900 text-xs flex items-center gap-1.5 pb-1 border-b border-slate-100">
        <User class="w-4 h-4 text-slate-500" />
        個人暱稱與身體基礎數據
      </h3>

      <!-- Name / Nickname -->
      <div>
        <label class="block text-[11px] font-bold text-slate-600 mb-1">教練稱呼 / 會員暱稱</label>
        <div class="relative">
          <input
            v-model="form.name"
            type="text"
            placeholder="例如：健身勇士、Alice"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      <!-- Gender & Age -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">生理性別 (影響 BMR 計算)</label>
          <select
            v-model="form.gender"
            @change="handleFormChange"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500"
          >
            <option value="MALE">男性 (Male)</option>
            <option value="FEMALE">女性 (Female)</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">年齡 (歲)</label>
          <input
            v-model.number="form.age"
            @input="handleFormChange"
            type="number"
            min="10"
            max="100"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      <!-- Height, Weight, Target Weight -->
      <div class="grid grid-cols-3 gap-2">
        <div>
          <label class="block text-[10px] font-bold text-slate-600 mb-1">身高 (cm)</label>
          <input
            v-model.number="form.height_cm"
            @input="handleFormChange"
            type="number"
            step="0.5"
            class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500 text-center"
          />
        </div>
        <div>
          <label class="block text-[10px] font-bold text-slate-600 mb-1">目前體重 (kg)</label>
          <input
            v-model.number="form.current_weight_kg"
            @input="handleFormChange"
            type="number"
            step="0.1"
            class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500 text-center"
          />
        </div>
        <div>
          <label class="block text-[10px] font-bold text-slate-600 mb-1">目標體重 (kg)</label>
          <input
            v-model.number="form.target_weight_kg"
            type="number"
            step="0.1"
            class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500 text-center"
          />
        </div>
      </div>

      <!-- Fitness Goal & Experience -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">體態目標</label>
          <select
            v-model="form.fitness_goal"
            @change="handleFormChange"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500"
          >
            <option value="CUTTING">減脂緊實期 (Cutting)</option>
            <option value="BULKING">增肌期 (Bulking)</option>
            <option value="MAINTENANCE">體態維持 (Maintenance)</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">訓練年資</label>
          <select
            v-model="form.experience_level"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500"
          >
            <option value="BEGINNER">新手訓練者 (&lt; 1年)</option>
            <option value="INTERMEDIATE">中階訓練者 (1~3年)</option>
            <option value="ADVANCED">進階訓練者 (&gt; 3年)</option>
          </select>
        </div>
      </div>

      <!-- Activity Level -->
      <div>
        <label class="block text-[11px] font-bold text-slate-600 mb-1">日常活動量級別</label>
        <select
          v-model="form.activity_level"
          @change="handleFormChange"
          class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:border-brand-500"
        >
          <option value="SEDENTARY">久坐少動 (辦公室工作 / 極少運動) [×1.20]</option>
          <option value="LIGHT">輕度活動 (每週運動 1~3 天) [×1.375]</option>
          <option value="MODERATE">中度活動 (每週重訓 3~5 天) [×1.55]</option>
          <option value="ACTIVE">高度活動 (每週高強度 6~7 天) [×1.725]</option>
          <option value="VERY_ACTIVE">極高強度 (體力工作 / 每日雙練) [×1.90]</option>
        </select>
      </div>

      <!-- Macros Mode Selector & Targets -->
      <div class="pt-3 border-t border-slate-100 space-y-2.5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-700">每日三大營養素目標 (Macros)</span>
          <div class="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-[10px]">
            <button
              type="button"
              @click="setAutoRecalc(true)"
              class="px-2 py-1 rounded-md font-bold transition-all"
              :class="isAutoRecalc ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
            >
              ✨ 智慧自動計算
            </button>
            <button
              type="button"
              @click="setAutoRecalc(false)"
              class="px-2 py-1 rounded-md font-bold transition-all"
              :class="!isAutoRecalc ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-800'"
            >
              ✏️ 手動微調
            </button>
          </div>
        </div>

        <div v-if="isAutoRecalc" class="text-[11px] text-emerald-800 bg-emerald-50 p-2.5 rounded-xl border border-emerald-100 leading-relaxed">
          💡 已依據<strong>{{ form.gender === 'FEMALE' ? '女性' : '男性' }}</strong>體質、{{ form.current_weight_kg }}kg 體重與<strong>{{ getGoalText(form.fitness_goal) }}</strong>目標自動調配最佳三大營養素！
        </div>

        <div class="grid grid-cols-4 gap-2 text-center">
          <div>
            <span class="text-[10px] text-slate-500 font-bold">熱量 (kcal)</span>
            <input
              v-model.number="form.target_calories"
              :disabled="isAutoRecalc"
              type="number"
              class="w-full text-center py-2 border rounded-xl text-xs font-black shadow-2xs"
              :class="isAutoRecalc ? 'bg-slate-100 text-slate-700 border-slate-200' : 'bg-white text-slate-900 border-brand-400 ring-2 ring-brand-100'"
            />
          </div>
          <div>
            <span class="text-[10px] text-emerald-600 font-bold">蛋白質 (g)</span>
            <input
              v-model.number="form.target_protein_g"
              :disabled="isAutoRecalc"
              type="number"
              class="w-full text-center py-2 border rounded-xl text-xs font-black shadow-2xs"
              :class="isAutoRecalc ? 'bg-slate-100 text-emerald-700 border-slate-200' : 'bg-white text-emerald-700 border-emerald-400 ring-2 ring-emerald-100'"
            />
          </div>
          <div>
            <span class="text-[10px] text-blue-600 font-bold">碳水 (g)</span>
            <input
              v-model.number="form.target_carbs_g"
              :disabled="isAutoRecalc"
              type="number"
              class="w-full text-center py-2 border rounded-xl text-xs font-black shadow-2xs"
              :class="isAutoRecalc ? 'bg-slate-100 text-blue-700 border-slate-200' : 'bg-white text-blue-700 border-blue-400 ring-2 ring-blue-100'"
            />
          </div>
          <div>
            <span class="text-[10px] text-amber-600 font-bold">脂肪 (g)</span>
            <input
              v-model.number="form.target_fat_g"
              :disabled="isAutoRecalc"
              type="number"
              class="w-full text-center py-2 border rounded-xl text-xs font-black shadow-2xs"
              :class="isAutoRecalc ? 'bg-slate-100 text-amber-700 border-slate-200' : 'bg-white text-amber-700 border-amber-400 ring-2 ring-amber-100'"
            />
          </div>
        </div>
      </div>

      <button
        @click="saveProfile"
        :disabled="saving"
        class="w-full py-3.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-1.5"
      >
        <Save class="w-4 h-4" />
        <span>{{ saving ? '正在儲存體態設定...' : '儲存體態設定並同步更新 TDEE' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Sparkles, Save, LogOut, Flame } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)
const isAutoRecalc = ref(true)

const form = reactive({
  name: '',
  gender: 'FEMALE',
  age: 26,
  height_cm: 160,
  current_weight_kg: 52,
  target_weight_kg: 50,
  fitness_goal: 'CUTTING',
  experience_level: 'INTERMEDIATE',
  activity_level: 'MODERATE',
  target_calories: 1450,
  target_protein_g: 94,
  target_carbs_g: 170,
  target_fat_g: 45
})

function getGoalText(goal) {
  if (goal === 'BULKING') return '增肌期'
  if (goal === 'CUTTING') return '減脂緊實期'
  return '體態維持'
}

// Live client-side Mifflin-St Jeor equation calculation
const liveStats = computed(() => {
  const isFemale = (form.gender === 'FEMALE')
  const w = Number(form.current_weight_kg) || 50
  const h = Number(form.height_cm) || 160
  const a = Number(form.age) || 25
  
  let bmr = isFemale
    ? 10 * w + 6.25 * h - 5 * a - 161
    : 10 * w + 6.25 * h - 5 * a + 5
  bmr = Math.max(800, Math.round(bmr * 10) / 10)

  const mults = {
    SEDENTARY: 1.2,
    LIGHT: 1.375,
    MODERATE: 1.55,
    ACTIVE: 1.725,
    VERY_ACTIVE: 1.9
  }
  const mult = mults[form.activity_level] || 1.55
  const tdee = Math.round(bmr * mult * 10) / 10

  // Goal & Macros calculation
  let targetCals = tdee
  let proteinG = 0
  let fatG = 0
  let carbsG = 0

  if (form.fitness_goal === 'BULKING') {
    const surplus = isFemale ? 200 : 300
    targetCals = Math.round(tdee + surplus)
    proteinG = Math.round(w * (isFemale ? 1.8 : 2.0) * 10) / 10
    const fatPct = isFemale ? 0.28 : 0.25
    fatG = Math.round((targetCals * fatPct / 9) * 10) / 10
    carbsG = Math.max(0, Math.round(((targetCals - proteinG * 4 - fatG * 9) / 4) * 10) / 10)
  } else if (form.fitness_goal === 'CUTTING') {
    const deficit = isFemale ? Math.min(Math.round(tdee * 0.20), 350) : 400
    const minCals = isFemale ? 1200 : 1500
    targetCals = Math.max(minCals, Math.round(tdee - deficit))
    proteinG = Math.round(w * (isFemale ? 1.8 : 2.2) * 10) / 10
    const fatPct = isFemale ? 0.28 : 0.22
    fatG = Math.round((targetCals * fatPct / 9) * 10) / 10
    carbsG = Math.max(0, Math.round(((targetCals - proteinG * 4 - fatG * 9) / 4) * 10) / 10)
  } else {
    targetCals = Math.round(tdee)
    proteinG = Math.round(w * (isFemale ? 1.6 : 1.8) * 10) / 10
    const fatPct = isFemale ? 0.28 : 0.25
    fatG = Math.round((targetCals * fatPct / 9) * 10) / 10
    carbsG = Math.max(0, Math.round(((targetCals - proteinG * 4 - fatG * 9) / 4) * 10) / 10)
  }

  return {
    bmr,
    tdee,
    targetCals,
    proteinG,
    carbsG,
    fatG
  }
})

function handleFormChange() {
  if (isAutoRecalc.value) {
    form.target_calories = liveStats.value.targetCals
    form.target_protein_g = liveStats.value.proteinG
    form.target_carbs_g = liveStats.value.carbsG
    form.target_fat_g = liveStats.value.fatG
  }
}

function setAutoRecalc(val) {
  isAutoRecalc.value = val
  if (val) {
    handleFormChange()
  }
}

function syncProfile() {
  form.name = authStore.user?.name || ''
  const p = authStore.profile
  if (!p) return
  form.gender = p.gender || 'MALE'
  form.age = p.age || 26
  form.height_cm = p.height_cm || 175
  form.current_weight_kg = p.current_weight_kg || 70
  form.target_weight_kg = p.target_weight_kg || 72
  form.fitness_goal = p.fitness_goal || 'BULKING'
  form.experience_level = p.experience_level || 'INTERMEDIATE'
  form.activity_level = p.activity_level || 'MODERATE'
  
  form.target_calories = p.target_calories || liveStats.value.targetCals
  form.target_protein_g = p.target_protein_g || liveStats.value.proteinG
  form.target_carbs_g = p.target_carbs_g || liveStats.value.carbsG
  form.target_fat_g = p.target_fat_g || liveStats.value.fatG
}

async function saveProfile() {
  saving.value = true
  try {
    handleFormChange()
    const payload = {
      ...form,
      auto_recalculate: isAutoRecalc.value
    }
    const updated = await authStore.updateProfile(payload)
    syncProfile()
    alert('🎉 體態設定與 TDEE 已成功更新！')
  } catch (err) {
    alert('儲存失敗，請稍後重試')
  } finally {
    saving.value = false
  }
}

function handleLogout() {
  if (confirm('確定要登出 FitPulse 嗎？')) {
    authStore.logout()
    router.push('/auth')
  }
}

onMounted(() => {
  syncProfile()
})
</script>
