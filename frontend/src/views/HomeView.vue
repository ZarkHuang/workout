<template>
  <div class="pb-24 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- 1. Header Greeting Banner -->
    <div class="flex items-center justify-between">
      <div>
        <div class="text-xs font-semibold text-slate-400">{{ todayFormatted }}</div>
        <h1 class="text-xl font-black text-slate-900 flex items-center gap-1.5">
          嗨，{{ authStore.user?.name || '健身勇士' }}
          <span class="text-lg">👋</span>
        </h1>
      </div>
      <div class="flex flex-col items-end">
        <span class="text-[11px] font-bold px-2 py-0.5 rounded-full" :class="getGoalBadgeClass">
          {{ getGoalText(authStore.profile?.fitness_goal) }}
        </span>
        <span class="text-[10px] text-slate-400 mt-0.5">體重: {{ authStore.profile?.current_weight_kg || '--' }} kg</span>
      </div>
    </div>

    <!-- 2. Ongoing Workout Draft Alert Banner (if active) -->
    <div
      v-if="workoutStore.activeExercises.length > 0"
      class="p-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-float flex items-center justify-between transition-all"
    >
      <div
        @click="$router.push('/active-workout')"
        class="flex items-center gap-3 cursor-pointer flex-1"
      >
        <div class="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center">
          <Flame class="w-5 h-5 text-white" />
        </div>
        <div>
          <div class="text-[11px] font-medium text-emerald-100">訓練日誌草稿 ({{ workoutStore.activeExercises.length }} 個動作)</div>
          <div class="text-sm font-bold">{{ workoutStore.sessionName }}</div>
        </div>
      </div>
      <div class="flex items-center gap-1.5">
        <button
          @click="$router.push('/active-workout')"
          class="text-xs font-bold bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-xl"
        >
          繼續填寫
        </button>
        <button
          @click.stop="workoutStore.cancelWorkout()"
          class="p-1.5 rounded-lg bg-white/10 hover:bg-rose-500 text-white transition-colors"
          title="清空草稿"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 3. AI Smart Workout Recommendation Hero Button -->
    <div class="p-4 rounded-2xl bg-gradient-to-br from-brand-500 via-emerald-600 to-teal-700 text-white shadow-float relative overflow-hidden">
      <div class="absolute -right-6 -bottom-6 w-32 h-32 rounded-full bg-white/10 blur-2xl pointer-events-none"></div>
      
      <div class="flex items-start justify-between mb-2">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <Sparkles class="w-4 h-4 text-white" />
          </div>
          <span class="text-xs font-bold uppercase tracking-wider text-emerald-100">Gemini AI 今日排課</span>
        </div>
        <span class="text-[10px] bg-white/20 px-2 py-0.5 rounded-full font-medium">即時修復評估</span>
      </div>

      <h2 class="text-lg font-black mb-1">今天不知道要練什麼？</h2>
      <p class="text-xs text-emerald-100/90 leading-relaxed mb-3">
        嚴格採用單一部位分化（胸/背/肩/腿），AI 依據肌群修復度一鍵排課。
      </p>

      <!-- Split selector pills -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1.5 scrollbar-none">
        <button
          v-for="s in splitOptions"
          :key="s.key"
          @click="selectSplit(s.key)"
          class="text-[11px] font-bold px-2.5 py-1 rounded-lg whitespace-nowrap transition-all"
          :class="selectedSplit === s.key ? 'bg-white text-emerald-900 shadow-sm' : 'bg-white/15 text-emerald-100 hover:bg-white/25'"
        >
          {{ s.label }}
        </button>
      </div>

      <!-- Sub-Focus pills (e.g. Lat Width vs Back Thickness) -->
      <div v-if="currentSubFocusList.length > 0" class="pt-2 pb-1 border-t border-white/15 space-y-1">
        <div class="text-[10px] font-bold text-emerald-200">🎯 細部維度客製（點選偏好）：</div>
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          <button
            v-for="sf in currentSubFocusList"
            :key="sf.key"
            @click="selectedSubFocus = sf.key"
            class="text-[10px] font-bold px-2 py-0.8 rounded-md whitespace-nowrap transition-all"
            :class="selectedSubFocus === sf.key ? 'bg-emerald-300 text-emerald-950 shadow-sm' : 'bg-white/10 text-emerald-100 hover:bg-white/20'"
          >
            {{ sf.label }}
          </button>
        </div>
      </div>
      <!-- Custom Note / Wish input -->
      <div class="pt-1.5 mb-3.5 relative">
        <input
          v-model="customNotes"
          type="text"
          placeholder="💬 客製偏好（例如：想多做啞鈴、加入引體向上）..."
          class="w-full bg-black/20 placeholder-emerald-200/60 border border-white/20 rounded-xl pl-3 pr-8 py-1.5 text-xs text-white focus:outline-none focus:bg-black/30 focus:border-white/40"
        />
        <button
          v-if="customNotes"
          @click="customNotes = ''"
          class="absolute right-2.5 top-3 text-emerald-200/70 hover:text-white"
          title="清空文字"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="openAIRecommendModal()"
          :disabled="loadingAI"
          class="flex-1 py-2.5 px-4 rounded-xl bg-white text-emerald-800 text-xs font-extrabold shadow-sm active:scale-95 transition-all flex items-center justify-center gap-1.5"
        >
          <Sparkles class="w-4 h-4 text-emerald-600" :class="{ 'animate-spin': loadingAI }" />
          <span>{{ loadingAI ? 'AI 正在規劃客製課表...' : '✨ 一鍵推薦今日客製課表' }}</span>
        </button>
        <button
          @click="startEmptyWorkout"
          class="py-2.5 px-3 rounded-xl bg-white/20 hover:bg-white/30 text-white text-xs font-bold active:scale-95 transition-all flex items-center gap-1"
        >
          <Play class="w-3.5 h-3.5" />
          <span>自由記訓練</span>
        </button>
      </div>
    </div>

    <!-- 4. Muscle Recovery Heatmap Card -->
    <MuscleRecoveryCard
      :overview="recoveryOverview"
      :loading="loadingRecovery"
      @refresh="fetchRecovery"
    />

    <!-- 5. Nutrition Macro Progress Card -->
    <NutritionRingCard :progress="nutritionStore.dailyProgress" />

    <!-- 6. Quick Action Grid -->
    <div class="grid grid-cols-2 gap-3">
      <!-- Diet text logging -->
      <div
        @click="$router.push('/diet')"
        class="card-apple-interactive flex items-center gap-3"
      >
        <div class="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center flex-shrink-0">
          <Utensils class="w-5 h-5" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-800">純文字記飲食</div>
          <div class="text-[10px] text-slate-400">AI 秒算卡路里</div>
        </div>
      </div>

      <!-- Ask AI Coach -->
      <div
        @click="$router.push('/ai-coach')"
        class="card-apple-interactive flex items-center gap-3"
      >
        <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
          <Bot class="w-5 h-5" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-800">隨身 AI 教練</div>
          <div class="text-[10px] text-slate-400">無狀態即問即用</div>
        </div>
      </div>
    </div>

    <!-- 7. Recent Sessions -->
    <div class="card-apple">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
          <Dumbbell class="w-4 h-4 text-slate-500" />
          近期訓練紀錄
        </h3>
        <router-link to="/workout" class="text-xs font-semibold text-brand-600 hover:text-brand-700">全部</router-link>
      </div>

      <div v-if="recentSessions.length === 0" class="text-center py-6 text-slate-400 text-xs">
        尚無訓練紀錄，今天就開始第一堂課吧！
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="s in recentSessions.slice(0, 3)"
          :key="s.id"
          class="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between"
        >
          <div>
            <div class="text-xs font-bold text-slate-800">{{ s.session_name }}</div>
            <div class="text-[10px] text-slate-400">{{ formatDate(s.created_at) }} · {{ s.duration_minutes }} 分鐘</div>
          </div>
          <div class="flex items-center gap-2">
            <div class="text-right">
              <div class="text-xs font-black text-brand-700">{{ s.total_volume_kg }} kg</div>
              <div class="text-[10px] text-slate-400">{{ s.sets?.length || 0 }} 組動作</div>
            </div>
            <button
              @click="handleDeleteRecentSession(s.id)"
              class="text-slate-300 hover:text-rose-500 p-1 rounded-lg hover:bg-rose-50 transition-colors"
              title="刪除紀錄"
            >
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Routine Recommendation Modal -->
    <div
      v-if="showAIModal && recommendedRoutine"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 max-h-[85vh] overflow-y-auto space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
              <Sparkles class="w-4 h-4" />
            </div>
            <h3 class="font-black text-slate-900 text-base">{{ recommendedRoutine.routine_title }}</h3>
          </div>
          <button @click="showAIModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Split switcher inside modal -->
        <div class="space-y-1.5">
          <div class="text-[10px] font-bold text-slate-400">切換分化部位：</div>
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            <button
              v-for="s in splitOptions"
              :key="s.key"
              @click="openAIRecommendModal(s.key)"
              :disabled="loadingAI"
              class="text-[11px] font-bold px-2.5 py-1 rounded-lg whitespace-nowrap transition-all"
              :class="selectedSplit === s.key ? 'bg-brand-500 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            >
              {{ s.label }}
            </button>
          </div>

          <!-- Sub-focus switcher inside modal -->
          <div v-if="currentSubFocusList.length > 0" class="pt-1 flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            <button
              v-for="sf in currentSubFocusList"
              :key="sf.key"
              @click="openAIRecommendModal(selectedSplit, sf.key)"
              :disabled="loadingAI"
              class="text-[10px] font-bold px-2 py-0.8 rounded-md whitespace-nowrap transition-all"
              :class="selectedSubFocus === sf.key ? 'bg-emerald-600 text-white shadow-sm' : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200'"
            >
              {{ sf.label }}
            </button>
          </div>
        </div>

        <!-- Rationale -->
        <div class="p-3 rounded-2xl bg-brand-50/70 border border-brand-100 text-xs text-brand-900 leading-relaxed">
          <span class="font-bold text-brand-800">💡 專家排課理由：</span>
          {{ recommendedRoutine.rationale }}
        </div>

        <!-- Warmup tips -->
        <div v-if="recommendedRoutine.warmup_tips?.length" class="space-y-1">
          <div class="text-[11px] font-bold text-slate-500">🔥 建議熱身激活：</div>
          <div class="text-xs text-slate-600 pl-2 space-y-0.5">
            <div v-for="(w, i) in recommendedRoutine.warmup_tips" :key="i">· {{ w }}</div>
          </div>
        </div>

        <!-- Exercises List -->
        <div class="space-y-2">
          <div class="text-[11px] font-bold text-slate-500">🏋️ 今日推薦動作清單：</div>
          <div
            v-for="(ex, i) in recommendedRoutine.exercises"
            :key="i"
            class="p-3 rounded-xl bg-slate-50 border border-slate-200/70 flex items-start justify-between"
          >
            <div>
              <div class="text-xs font-bold text-slate-800">{{ i + 1 }}. {{ ex.exercise_name }}</div>
              <div class="text-[10px] text-slate-500 mt-0.5">
                {{ ex.target_sets }} 組 × {{ ex.target_reps }} 次
                <span v-if="ex.suggested_weight_kg"> · 建議 {{ ex.suggested_weight_kg }}kg</span>
              </div>
              <div v-if="ex.notes" class="text-[10px] text-brand-700 mt-1 italic">{{ ex.notes }}</div>
            </div>
            <span class="badge-emerald text-[10px]">{{ ex.target_muscle_group }}</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="pt-2 flex items-center gap-2">
          <button
            @click="adoptAIRoutine"
            class="flex-1 py-3 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            <ClipboardList class="w-4 h-4" />
            <span>👉 帶入此課表填寫紀錄</span>
          </button>
          <button
            @click="showAIModal = false"
            class="py-3 px-4 rounded-xl bg-slate-100 text-slate-600 font-bold text-xs hover:bg-slate-200 active:scale-95"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Activity, Flame, Sparkles, Play, Utensils, Bot, Dumbbell, ChevronRight, X, ClipboardList, Trash2
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useWorkoutStore } from '@/stores/workout'
import { useNutritionStore } from '@/stores/nutrition'
import { workoutsAPI, aiAPI, exercisesAPI } from '@/api/client'
import MuscleRecoveryCard from '@/components/MuscleRecoveryCard.vue'
import NutritionRingCard from '@/components/NutritionRingCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const workoutStore = useWorkoutStore()
const nutritionStore = useNutritionStore()

const recoveryOverview = ref(null)
const loadingRecovery = ref(false)
const recentSessions = ref([])

const showAIModal = ref(false)
const recommendedRoutine = ref(null)
const loadingAI = ref(false)

const selectedSplit = ref('AUTO')
const selectedSubFocus = ref('DEFAULT')
const customNotes = ref('')

const splitOptions = [
  { key: 'AUTO', label: '⚡ 智慧推薦' },
  { key: 'CHEST', label: '💪 胸部專攻' },
  { key: 'BACK', label: '🦅 背部專攻' },
  { key: 'SHOULDERS', label: '🛡️ 肩部專攻' },
  { key: 'LEGS', label: '🦵 臀腿突破' },
  { key: 'PUSH', label: '🔥 推力日' },
  { key: 'PULL', label: '⚡ 拉力日' },
  { key: 'CARDIO', label: '🏃 有氧燃脂' }
]

const currentSubFocusList = computed(() => {
  if (selectedSplit.value === 'BACK') {
    return [
      { key: 'DEFAULT', label: '⚖️ 全背均衡' },
      { key: 'WIDTH', label: '📐 闊背寬度 (垂直拉)' },
      { key: 'THICKNESS', label: '🧱 上背厚度 (水平划船)' }
    ]
  }
  if (selectedSplit.value === 'CHEST') {
    return [
      { key: 'DEFAULT', label: '⚖️ 全胸均衡' },
      { key: 'UPPER', label: '📐 鎖骨上胸' },
      { key: 'LOWER', label: '🧱 下胸輪廓' }
    ]
  }
  if (selectedSplit.value === 'SHOULDERS') {
    return [
      { key: 'DEFAULT', label: '⚖️ 全肩立體' },
      { key: 'LATERAL', label: '📐 側平舉 (肩寬)' },
      { key: 'REAR', label: '🧱 後束與上背' }
    ]
  }
  if (selectedSplit.value === 'LEGS') {
    return [
      { key: 'DEFAULT', label: '⚖️ 全腿均衡' },
      { key: 'QUADS', label: '🦵 股四頭 (深蹲)' },
      { key: 'GLUTES', label: '🍑 臀肌/後鏈 (RDL)' }
    ]
  }
  if (selectedSplit.value === 'CARDIO') {
    return [
      { key: 'DEFAULT', label: '⚖️ 綜合有氧' },
      { key: 'LISS', label: '🏃 穩態燃脂 (Zone 2)' },
      { key: 'HIIT', label: '⚡ 高強度間歇 (HIIT)' }
    ]
  }
  return []
})

function selectSplit(splitKey) {
  selectedSplit.value = splitKey
  selectedSubFocus.value = 'DEFAULT'
  customNotes.value = '' // Auto-clear input to enhance UX when switching tags
}

const todayFormatted = computed(() => {
  const d = new Date()
  const options = { month: 'short', day: 'numeric', weekday: 'short' }
  return d.toLocaleDateString('zh-TW', options)
})

const getGoalBadgeClass = computed(() => {
  const g = authStore.profile?.fitness_goal
  if (g === 'BULKING') return 'bg-orange-50 text-orange-700 border border-orange-200'
  if (g === 'CUTTING') return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  return 'bg-blue-50 text-blue-700 border border-blue-200'
})

function getGoalText(goal) {
  if (goal === 'BULKING') return '🎯 增肌期 (Bulking)'
  if (goal === 'CUTTING') return '🔥 減脂期 (Cutting)'
  return '⚖️ 體態維持 (Maintenance)'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

async function fetchRecovery() {
  loadingRecovery.value = true
  try {
    const res = await workoutsAPI.getRecoveryStatus()
    recoveryOverview.value = res.data
  } catch (err) {
    console.error('Failed to fetch recovery:', err)
  } finally {
    loadingRecovery.value = false
  }
}

async function fetchRecentSessions() {
  try {
    const res = await workoutsAPI.getSessions({ limit: 5 })
    recentSessions.value = res.data
  } catch (err) {
    console.error('Failed to fetch sessions:', err)
  }
}

async function handleDeleteRecentSession(id) {
  if (!confirm('確定要刪除這筆訓練紀錄嗎？刪除後無法復原。')) return
  try {
    await workoutsAPI.deleteSession(id)
    alert('已成功刪除該筆紀錄！')
    await fetchRecentSessions()
    await fetchRecovery()
  } catch (err) {
    alert('刪除失敗，請稍後重試')
  }
}

async function openAIRecommendModal(customSplit = null, customSubFocus = null) {
  if (customSplit) {
    selectedSplit.value = customSplit
    if (customSubFocus) {
      selectedSubFocus.value = customSubFocus
    } else if (customSplit !== selectedSplit.value) {
      selectedSubFocus.value = 'DEFAULT'
    }
  } else if (customSubFocus) {
    selectedSubFocus.value = customSubFocus
  }

  loadingAI.value = true
  try {
    const res = await aiAPI.recommendWorkout({
      duration_minutes: 60,
      focus_preference: selectedSplit.value === 'AUTO' ? null : selectedSplit.value,
      sub_focus: selectedSubFocus.value === 'DEFAULT' ? null : selectedSubFocus.value,
      custom_notes: customNotes.value || null
    })
    recommendedRoutine.value = res.data
    showAIModal.value = true
  } catch (err) {
    alert('AI 推薦排課暫時無法取得，請稍後重試')
  } finally {
    loadingAI.value = false
  }
}

function startEmptyWorkout() {
  workoutStore.startWorkout('今日自由訓練')
  router.push('/active-workout')
}

async function adoptAIRoutine() {
  if (!recommendedRoutine.value) return
  showAIModal.value = false

  // Fetch all exercises to map names to exercise IDs
  try {
    const exRes = await exercisesAPI.list()
    const allEx = exRes.data

    workoutStore.startWorkout(recommendedRoutine.value.routine_title)
    
    for (const item of recommendedRoutine.value.exercises) {
      // Find matching exercise or first match
      let match = allEx.find(e => e.name === item.exercise_name || item.exercise_name.includes(e.name))
      if (!match) {
        match = allEx.find(e => e.target_muscle_group === item.target_muscle_group) || allEx[0]
      }
      
      const numSets = Number(item.target_sets) || 3
      const numReps = parseInt(item.target_reps) || 10
      const sets = []
      for (let i = 1; i <= numSets; i++) {
        sets.push({
          set_number: i,
          weight_kg: item.suggested_weight_kg || 0,
          reps: numReps,
          rpe: 8.0,
          is_completed: false,
          prev_weight: null,
          prev_reps: null
        })
      }

      workoutStore.activeExercises.push({
        exercise_id: match.id,
        name: item.exercise_name,
        target_muscle_group: item.target_muscle_group,
        sets
      })
    }

    router.push('/active-workout')
  } catch (err) {
    console.error('Error adopting routine:', err)
    startEmptyWorkout()
  }
}

onMounted(() => {
  fetchRecovery()
  fetchRecentSessions()
  nutritionStore.fetchTodayProgress()
})
</script>
