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

    <!-- TDEE & BMR Summary Banner -->
    <div class="card-apple bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white border-0 shadow-lg p-4 space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-emerald-400" />
          <span class="text-xs font-bold text-slate-300">Mifflin-St Jeor 動態代謝評估</span>
        </div>
        <span class="text-[10px] bg-white/10 px-2 py-0.5 rounded-full text-emerald-300 font-semibold">
          {{ getGoalText(form.fitness_goal) }}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-3 pt-1">
        <div class="p-2.5 rounded-xl bg-white/10">
          <div class="text-[10px] text-slate-400">基礎代謝 (BMR)</div>
          <div class="text-lg font-black text-white">{{ authStore.profile?.bmr || '--' }} <span class="text-xs font-normal text-slate-400">kcal</span></div>
        </div>
        <div class="p-2.5 rounded-xl bg-white/10">
          <div class="text-[10px] text-slate-400">每日總消耗 (TDEE)</div>
          <div class="text-lg font-black text-emerald-400">{{ authStore.profile?.tdee || '--' }} <span class="text-xs font-normal text-slate-400">kcal</span></div>
        </div>
      </div>

      <div class="p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between text-xs">
        <span class="text-slate-300">系統建議每日攝取目標</span>
        <span class="font-black text-amber-400 text-sm">{{ form.target_calories }} kcal</span>
      </div>
    </div>

    <!-- Profile Form -->
    <div class="card-apple space-y-4">
      <h3 class="font-bold text-slate-900 text-xs flex items-center gap-1.5 pb-1 border-b border-slate-100">
        <User class="w-4 h-4 text-slate-500" />
        身體基礎數據
      </h3>

      <!-- Gender & Age -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">生理性別</label>
          <select
            v-model="form.gender"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500"
          >
            <option value="MALE">男性 (Male)</option>
            <option value="FEMALE">女性 (Female)</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">年齡</label>
          <input
            v-model.number="form.age"
            type="number"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      <!-- Height, Weight, Target Weight -->
      <div class="grid grid-cols-3 gap-2">
        <div>
          <label class="block text-[10px] font-bold text-slate-600 mb-1">身高 (cm)</label>
          <input
            v-model.number="form.height_cm"
            type="number"
            step="0.5"
            class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500 text-center"
          />
        </div>
        <div>
          <label class="block text-[10px] font-bold text-slate-600 mb-1">目前體重 (kg)</label>
          <input
            v-model.number="form.current_weight_kg"
            type="number"
            step="0.1"
            class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500 text-center"
          />
        </div>
        <div>
          <label class="block text-[10px] font-bold text-slate-600 mb-1">目標體重 (kg)</label>
          <input
            v-model.number="form.target_weight_kg"
            type="number"
            step="0.1"
            class="w-full px-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500 text-center"
          />
        </div>
      </div>

      <!-- Fitness Goal & Experience -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">體態目標</label>
          <select
            v-model="form.fitness_goal"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500"
          >
            <option value="BULKING">增肌期 (Bulking +250kcal)</option>
            <option value="CUTTING">減脂期 (Cutting -400kcal)</option>
            <option value="MAINTENANCE">體態維持 (Maintenance)</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 mb-1">訓練年資</label>
          <select
            v-model="form.experience_level"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500"
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
          class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500"
        >
          <option value="SEDENTARY">久坐少動 (辦公室/極少運動)</option>
          <option value="LIGHT">輕度活動 (每週運動 1~3 天)</option>
          <option value="MODERATE">中度活動 (每週重訓 3~5 天)</option>
          <option value="ACTIVE">高度活動 (每週高強度 6~7 天)</option>
          <option value="VERY_ACTIVE">極高強度 (體力工作/雙練)</option>
        </select>
      </div>

      <!-- Macros Targets Override (Optional) -->
      <div class="pt-2 border-t border-slate-100 space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-700">每日宏觀目標 (可自訂微調)</span>
        </div>

        <div class="grid grid-cols-4 gap-2 text-center">
          <div>
            <span class="text-[10px] text-slate-400 font-bold">熱量 (kcal)</span>
            <input
              v-model.number="form.target_calories"
              type="number"
              class="w-full text-center py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold"
            />
          </div>
          <div>
            <span class="text-[10px] text-emerald-600 font-bold">蛋白質 (g)</span>
            <input
              v-model.number="form.target_protein_g"
              type="number"
              class="w-full text-center py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-emerald-700"
            />
          </div>
          <div>
            <span class="text-[10px] text-blue-600 font-bold">碳水 (g)</span>
            <input
              v-model.number="form.target_carbs_g"
              type="number"
              class="w-full text-center py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-blue-700"
            />
          </div>
          <div>
            <span class="text-[10px] text-amber-600 font-bold">脂肪 (g)</span>
            <input
              v-model.number="form.target_fat_g"
              type="number"
              class="w-full text-center py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-amber-700"
            />
          </div>
        </div>
      </div>

      <button
        @click="saveProfile"
        :disabled="saving"
        class="w-full py-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-1.5"
      >
        <Save class="w-4 h-4" />
        <span>{{ saving ? '正在更新體態設定...' : '儲存體態設定並重新計算 TDEE' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Sparkles, Save, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)

const form = reactive({
  gender: 'MALE',
  age: 26,
  height_cm: 175,
  current_weight_kg: 70,
  target_weight_kg: 72,
  fitness_goal: 'BULKING',
  experience_level: 'INTERMEDIATE',
  activity_level: 'MODERATE',
  target_calories: 2400,
  target_protein_g: 140,
  target_carbs_g: 280,
  target_fat_g: 65
})

function getGoalText(goal) {
  if (goal === 'BULKING') return '增肌期'
  if (goal === 'CUTTING') return '減脂期'
  return '體態維持'
}

function syncProfile() {
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
  form.target_calories = p.target_calories || 2400
  form.target_protein_g = p.target_protein_g || 140
  form.target_carbs_g = p.target_carbs_g || 280
  form.target_fat_g = p.target_fat_g || 65
}

async function saveProfile() {
  saving.value = true
  try {
    const updated = await authStore.updateProfile(form)
    syncProfile()
    alert('體態設定與 TDEE 已更新！')
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
