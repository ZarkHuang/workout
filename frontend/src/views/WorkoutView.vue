<template>
  <div class="pb-24 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-black text-slate-900">訓練中樞</h1>
        <p class="text-xs text-slate-400">課表管理、黃金動作庫與歷史日誌</p>
      </div>
      <button
        @click="startBlankWorkout"
        class="py-2 px-3.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-black shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center gap-1.5"
      >
        <Plus class="w-4 h-4" />
        <span>記錄今日訓練</span>
      </button>
    </div>

    <!-- Active Draft Banner (if active) -->
    <div
      v-if="workoutStore.activeExercises.length > 0"
      @click="$router.push('/active-workout')"
      class="p-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white flex items-center justify-between cursor-pointer active:scale-[0.98] transition-all shadow-float"
    >
      <div class="flex items-center gap-2.5">
        <Flame class="w-5 h-5 text-white" />
        <span class="text-xs font-bold">{{ workoutStore.sessionName }} 草稿編輯中 ({{ workoutStore.activeExercises.length }} 個動作)</span>
      </div>
      <span class="text-xs font-bold bg-white/20 px-2.5 py-1 rounded-lg">繼續填寫</span>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex bg-slate-200/70 p-1 rounded-xl">
      <button
        @click="activeTab = 'routines'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="activeTab === 'routines' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
      >
        我的課表
      </button>
      <button
        @click="activeTab = 'library'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="activeTab === 'library' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
      >
        黃金動作庫
      </button>
      <button
        @click="activeTab = 'history'"
        class="flex-1 py-1.5 text-xs font-bold rounded-lg transition-all"
        :class="activeTab === 'history' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
      >
        歷史日誌
      </button>
    </div>

    <!-- TAB 1: Routines -->
    <div v-if="activeTab === 'routines'" class="space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-slate-500">已儲存課表 ({{ routines.length }})</span>
        <button
          @click="showCreateRoutineModal = true"
          class="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>建立自訂課表</span>
        </button>
      </div>

      <div v-if="routines.length === 0" class="card-apple text-center py-8">
        <Dumbbell class="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <div class="text-xs font-bold text-slate-700 mb-1">尚未建立任何課表</div>
        <div class="text-[11px] text-slate-400 mb-3">可以自訂推拉腿或全身體態課表！</div>
        <button
          @click="showCreateRoutineModal = true"
          class="py-2 px-4 rounded-xl bg-brand-50 text-brand-700 font-bold text-xs border border-brand-200"
        >
          立即建立第一套課表
        </button>
      </div>

      <div
        v-for="r in routines"
        :key="r.id"
        class="card-apple space-y-3"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-bold text-slate-900">{{ r.title }}</h3>
              <span class="badge-emerald text-[10px]">{{ r.target_split }}</span>
            </div>
            <p v-if="r.description" class="text-xs text-slate-500 mt-0.5">{{ r.description }}</p>
          </div>
          <button
            @click="deleteRoutine(r.id)"
            class="text-slate-300 hover:text-rose-500 p-1"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>

        <!-- Exercise preview list -->
        <div class="space-y-1.5 pt-1">
          <div
            v-for="(re, idx) in r.exercises"
            :key="re.id"
            class="text-xs text-slate-600 flex items-center justify-between bg-slate-50 px-2.5 py-1.5 rounded-lg"
          >
            <span>{{ idx + 1 }}. {{ re.exercise?.name || '動作' }}</span>
            <span class="text-[10px] font-bold text-slate-400">{{ re.target_sets }} 組 × {{ re.target_reps }} 次</span>
          </div>
        </div>

        <button
          @click="startRoutine(r)"
          class="w-full py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs shadow-sm active:scale-95 transition-all flex items-center justify-center gap-1.5"
        >
          <Play class="w-3.5 h-3.5" />
          <span>開始此課表訓練</span>
        </button>
      </div>
    </div>

    <!-- TAB 2: Exercise Library -->
    <div v-if="activeTab === 'library'" class="space-y-3">
      <!-- Search & Filters -->
      <div class="space-y-2">
        <div class="relative">
          <Search class="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜尋動作名稱（例如：臥推、深蹲）..."
            class="w-full pl-9 pr-4 py-2 bg-white rounded-xl border border-slate-200 text-xs focus:outline-none focus:border-brand-500"
          />
        </div>

        <!-- Muscle filter pills -->
        <div class="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          <button
            v-for="f in muscleFilters"
            :key="f.key"
            @click="selectedMuscleFilter = f.key"
            class="px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap transition-all"
            :class="selectedMuscleFilter === f.key ? 'bg-slate-900 text-white shadow-sm' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <!-- Exercise Items -->
      <div class="space-y-2">
        <div
          v-for="ex in filteredExercises"
          :key="ex.id"
          class="card-apple space-y-2"
        >
          <div class="flex items-start justify-between">
            <div>
              <div class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                {{ ex.name }}
                <span v-if="ex.name_en" class="text-[10px] font-normal text-slate-400">({{ ex.name_en }})</span>
              </div>
              <div class="flex items-center gap-1.5 mt-1">
                <span class="badge-emerald text-[10px]">{{ ex.target_muscle_group }}</span>
                <span class="badge-gray text-[10px]">{{ ex.equipment }}</span>
              </div>
            </div>
            <button
              v-if="workoutStore.isWorkoutActive"
              @click="addExerciseToActive(ex)"
              class="px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 font-bold text-xs hover:bg-brand-100 active:scale-95"
            >
              + 加入訓練
            </button>
          </div>
          <p v-if="ex.instructions" class="text-[11px] text-slate-500 bg-slate-50 p-2 rounded-lg leading-relaxed">
            💡 {{ ex.instructions }}
          </p>
        </div>
      </div>
    </div>

    <!-- TAB 3: History Logs & Weekly Comparison -->
    <div v-if="activeTab === 'history'" class="space-y-3.5">
      <!-- Weekly Comparison Highlight Banner -->
      <div v-if="weeklyStats" class="card-apple bg-gradient-to-br from-slate-900 to-slate-800 text-white border-0 shadow-lg p-4 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm font-black text-white">📊 本週 vs 上週訓練對比</span>
          </div>
          <span
            class="text-[10px] font-black px-2 py-0.5 rounded-full"
            :class="weeklyStats.volume_change_pct >= 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'"
          >
            容量 {{ weeklyStats.volume_change_pct >= 0 ? `+${weeklyStats.volume_change_pct}% 🔥` : `${weeklyStats.volume_change_pct}% 📉` }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 pt-1">
          <div class="bg-white/10 rounded-xl p-2.5">
            <div class="text-[10px] text-slate-400 font-medium">本週 ({{ weeklyStats.this_week.start_date }} 起)</div>
            <div class="text-base font-black text-emerald-400 mt-0.5">
              {{ weeklyStats.this_week.volume_kg.toLocaleString() }} <span class="text-[10px] font-normal text-slate-400">kg</span>
            </div>
            <div class="text-[10px] text-slate-300 mt-0.5">
              練 {{ weeklyStats.this_week.sessions_count }} 天 · {{ weeklyStats.this_week.duration_minutes }} 分鐘
            </div>
          </div>

          <div class="bg-white/10 rounded-xl p-2.5">
            <div class="text-[10px] text-slate-400 font-medium">上週 ({{ weeklyStats.last_week.start_date }} 起)</div>
            <div class="text-base font-black text-slate-300 mt-0.5">
              {{ weeklyStats.last_week.volume_kg.toLocaleString() }} <span class="text-[10px] font-normal text-slate-400">kg</span>
            </div>
            <div class="text-[10px] text-slate-300 mt-0.5">
              練 {{ weeklyStats.last_week.sessions_count }} 天 · {{ weeklyStats.last_week.duration_minutes }} 分鐘
            </div>
          </div>
        </div>
      </div>

      <div v-if="historySessions.length === 0" class="card-apple text-center py-8 text-slate-400 text-xs">
        尚無訓練歷史紀錄，點擊上方按鈕開始第一堂訓練！
      </div>

      <div
        v-for="s in historySessions"
        :key="s.id"
        class="card-apple space-y-2.5"
      >
        <div class="flex items-start justify-between">
          <div>
            <h3 class="text-xs font-bold text-slate-900">{{ s.session_name }}</h3>
            <div class="text-[10px] text-slate-400">{{ formatFullDate(s.created_at) }} · {{ s.duration_minutes }} 分鐘</div>
          </div>
          <div class="flex items-center gap-2">
            <div class="text-right">
              <div class="text-xs font-black text-brand-700">總容量 {{ s.total_volume_kg }} kg</div>
              <div class="text-[10px] text-slate-400">{{ s.sets?.length || 0 }} 組動作</div>
            </div>
            <button
              @click="handleDeleteSession(s.id)"
              class="text-slate-300 hover:text-rose-500 p-1 rounded-lg hover:bg-rose-50 transition-colors"
              title="刪除此筆日誌"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Sets breakdown -->
        <div class="bg-slate-50 rounded-xl p-2.5 space-y-1.5">
          <div
            v-for="(st, idx) in s.sets"
            :key="st.id"
            class="text-[11px] text-slate-700 flex items-center justify-between border-b border-slate-200/50 pb-1 last:border-0 last:pb-0"
          >
            <span>{{ st.exercise_name }} (第 {{ st.set_number }} 組)</span>
            <span class="font-bold text-slate-900">
              {{ st.weight_kg }}kg × {{ st.reps }}次
              <span v-if="st.estimated_1rm" class="text-[10px] text-brand-600 font-semibold ml-1">(1RM: {{ st.estimated_1rm }}kg)</span>
            </span>
          </div>
        </div>
      </div>

      <!-- 90-Day Rolling Cleanup Banner -->
      <div class="p-3 rounded-2xl bg-slate-100/80 border border-slate-200/60 flex items-center justify-between mt-2">
        <div class="text-[11px] text-slate-500">
          <span class="font-bold text-slate-700">90 天滾動歸檔：</span>
          保留近 3 個月完整組數，1RM 永久保留。
        </div>
        <button
          @click="handle90dCleanup"
          class="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-200 text-slate-700 text-[10px] font-bold border border-slate-200 shadow-2xs active:scale-95 whitespace-nowrap"
        >
          清理舊日誌
        </button>
      </div>
    </div>

    <!-- Create Routine Modal -->
    <div
      v-if="showCreateRoutineModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 max-h-[85vh] overflow-y-auto space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-black text-slate-900 text-base">建立新課表</h3>
          <button @click="showCreateRoutineModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">課表名稱</label>
            <input
              v-model="newRoutineTitle"
              type="text"
              placeholder="例如：週一推胸課表 / PPL-Push"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">分化類型</label>
            <select
              v-model="newRoutineSplit"
              class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
            >
              <option value="PUSH">推日 (PUSH - 胸/肩/三頭)</option>
              <option value="PULL">拉日 (PULL - 背/二頭)</option>
              <option value="LEGS">腿日 (LEGS - 腿/臀/小腿)</option>
              <option value="CARDIO">有氧日 (CARDIO - 心肺/HIIT/燃脂)</option>
              <option value="UPPER">上半身 (UPPER)</option>
              <option value="LOWER">下半身 (LOWER)</option>
              <option value="FULL_BODY">全身綜合 (FULL BODY)</option>
            </select>
          </div>

          <!-- Select Exercises for routine -->
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">選擇包含動作 ({{ selectedRoutineExercises.length }})</label>
            <div class="max-h-48 overflow-y-auto space-y-1.5 border border-slate-200 rounded-xl p-2 bg-slate-50">
              <div
                v-for="ex in allExercises"
                :key="ex.id"
                @click="toggleExerciseForRoutine(ex)"
                class="p-2 rounded-lg text-xs cursor-pointer flex items-center justify-between transition-colors"
                :class="isExerciseInNewRoutine(ex.id) ? 'bg-brand-500 text-white font-bold' : 'bg-white text-slate-700 hover:bg-slate-100'"
              >
                <span>{{ ex.name }}</span>
                <span class="text-[10px]" :class="isExerciseInNewRoutine(ex.id) ? 'text-white' : 'text-slate-400'">{{ ex.target_muscle_group }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2">
          <button
            @click="submitCreateRoutine"
            class="flex-1 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-extrabold shadow-sm active:scale-95"
          >
            確定儲存課表
          </button>
          <button
            @click="showCreateRoutineModal = false"
            class="py-2.5 px-4 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200 active:scale-95"
          >
            取消
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
  Plus, Dumbbell, Flame, Play, Trash2, Search, X
} from 'lucide-vue-next'
import { useWorkoutStore } from '@/stores/workout'
import { workoutsAPI, exercisesAPI } from '@/api/client'

const router = useRouter()
const workoutStore = useWorkoutStore()

const activeTab = ref('routines')
const routines = ref([])
const allExercises = ref([])
const historySessions = ref([])
const weeklyStats = ref(null)

const searchQuery = ref('')
const selectedMuscleFilter = ref('ALL')

const showCreateRoutineModal = ref(false)
const newRoutineTitle = ref('')
const newRoutineSplit = ref('PUSH')
const selectedRoutineExercises = ref([])

const muscleFilters = [
  { key: 'ALL', label: '全部' },
  { key: 'CHEST', label: '胸部' },
  { key: 'BACK', label: '背部' },
  { key: 'LEGS', label: '腿部' },
  { key: 'SHOULDERS', label: '肩部' },
  { key: 'ARMS', label: '手臂' },
  { key: 'CORE', label: '核心' },
  { key: 'CARDIO', label: '有氧' }
]

const filteredExercises = computed(() => {
  return allExercises.value.filter(e => {
    const matchMuscle = selectedMuscleFilter.value === 'ALL' || e.target_muscle_group === selectedMuscleFilter.value
    const matchQuery = !searchQuery.value || e.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || (e.name_en && e.name_en.toLowerCase().includes(searchQuery.value.toLowerCase()))
    return matchMuscle && matchQuery
  })
})

function formatFullDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

async function fetchRoutines() {
  try {
    const res = await workoutsAPI.getRoutines()
    routines.value = res.data
  } catch (err) {
    console.error('Failed to fetch routines:', err)
  }
}

async function fetchExercises() {
  try {
    const res = await exercisesAPI.list()
    allExercises.value = res.data
  } catch (err) {
    console.error('Failed to fetch exercises:', err)
  }
}

async function fetchHistory() {
  try {
    const res = await workoutsAPI.getSessions({ limit: 20 })
    historySessions.value = res.data
  } catch (err) {
    console.error('Failed to fetch history:', err)
  }
}

async function handleDeleteSession(id) {
  if (!confirm('確定要刪除這筆訓練紀錄嗎？刪除後無法復原。')) return
  try {
    await workoutsAPI.deleteSession(id)
    alert('已成功刪除該筆紀錄！')
    await fetchHistory()
    await fetchWeeklyStats()
  } catch (err) {
    alert('刪除失敗，請稍後重試')
  }
}

function startBlankWorkout() {
  workoutStore.startWorkout('今日自由訓練')
  router.push('/active-workout')
}

function startRoutine(routine) {
  workoutStore.startWorkout(routine.title, routine)
  router.push('/active-workout')
}

async function deleteRoutine(id) {
  if (!confirm('確定要刪除此課表嗎？')) return
  try {
    await workoutsAPI.deleteRoutine(id)
    await fetchRoutines()
  } catch (err) {
    alert('刪除失敗')
  }
}

function isExerciseInNewRoutine(id) {
  return selectedRoutineExercises.value.some(e => e.exercise_id === id)
}

function toggleExerciseForRoutine(ex) {
  const idx = selectedRoutineExercises.value.findIndex(e => e.exercise_id === ex.id)
  if (idx > -1) {
    selectedRoutineExercises.value.splice(idx, 1)
  } else {
    selectedRoutineExercises.value.push({
      exercise_id: ex.id,
      target_sets: 3,
      target_reps: 10
    })
  }
}

async function submitCreateRoutine() {
  if (!newRoutineTitle.value.trim()) {
    alert('請輸入課表名稱')
    return
  }
  if (selectedRoutineExercises.value.length === 0) {
    alert('請至少選擇 1 個動作')
    return
  }

  try {
    await workoutsAPI.createRoutine({
      title: newRoutineTitle.value,
      target_split: newRoutineSplit.value,
      exercises: selectedRoutineExercises.value
    })
    showCreateRoutineModal.value = false
    newRoutineTitle.value = ''
    selectedRoutineExercises.value = []
    await fetchRoutines()
  } catch (err) {
    alert('建立失敗，請稍後重試')
  }
}

function addExerciseToActive(ex) {
  workoutStore.addExerciseToActive(ex)
  router.push('/active-workout')
}

async function fetchWeeklyStats() {
  try {
    const res = await workoutsAPI.getWeeklyComparison()
    weeklyStats.value = res.data
  } catch (err) {
    console.error('Failed to fetch weekly stats:', err)
  }
}

async function handle90dCleanup() {
  if (!confirm('確定要執行 90 天滾動歸檔嗎？超過 3 個月的訓練日誌將會被清理以釋放資料庫空間，但 1RM 歷史最高紀錄將會永久保留。')) return
  try {
    const res = await workoutsAPI.cleanup90d()
    alert(res.data.message || '90 天滾動清理完成！')
    await fetchHistory()
    await fetchWeeklyStats()
  } catch (err) {
    alert('清理失敗，請稍後重試')
  }
}

onMounted(() => {
  fetchRoutines()
  fetchExercises()
  fetchHistory()
  fetchWeeklyStats()
})
</script>
