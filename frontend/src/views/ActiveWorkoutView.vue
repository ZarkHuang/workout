<template>
  <div class="pb-36 pt-3 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header: Immersive Live Session Card -->
    <div class="card-apple bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white border-0 shadow-2xl p-4.5 space-y-3.5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-black">
            <Flame class="w-5 h-5 text-emerald-400 animate-pulse" />
          </div>
          <div>
            <h1 class="text-base font-black text-white">{{ workoutStore.sessionName }}</h1>
            <p class="text-[11px] text-slate-400">即時打卡 · 自動試算 1RM · 突破提示</p>
          </div>
        </div>
        <button
          @click="handleCancelWorkout"
          class="text-xs text-slate-400 hover:text-rose-400 p-1.5 rounded-xl hover:bg-white/10 transition-colors flex items-center gap-1"
          title="放棄並清空"
        >
          <X class="w-4 h-4" />
          <span class="text-[10px]">放棄</span>
        </button>
      </div>

      <!-- Live Session Stopwatch & Date Selector (Clean Grid, No Overlap) -->
      <div class="grid grid-cols-2 gap-2.5 pt-1">
        <!-- Live Stopwatch Box (Manual Start / Pause / Smart Auto-start) -->
        <div class="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-3 flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold text-slate-400">⏱️ 訓練計時</span>
            <button
              @click="toggleSessionTimer"
              class="px-2 py-0.5 rounded-lg text-[10px] font-black flex items-center gap-1 active:scale-95 transition-all shadow-xs"
              :class="workoutStore.sessionTimerRunning ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : (sessionElapsedSeconds > 0 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-emerald-500/20')"
            >
              <component :is="workoutStore.sessionTimerRunning ? Pause : Play" class="w-2.5 h-2.5" />
              <span>{{ workoutStore.sessionTimerRunning ? '暫停' : (sessionElapsedSeconds > 0 ? '繼續' : '開始') }}</span>
            </button>
          </div>
          <div class="mt-1 flex items-baseline gap-1.5">
            <div
              class="text-xl font-black font-mono tracking-wider"
              :class="workoutStore.sessionTimerRunning ? 'text-emerald-400 animate-pulse' : (sessionElapsedSeconds > 0 ? 'text-white' : 'text-slate-400')"
            >
              {{ formattedSessionTime }}
            </div>
            <span class="text-[9px] font-bold" :class="workoutStore.sessionTimerRunning ? 'text-emerald-400' : 'text-slate-500'">
              {{ workoutStore.sessionTimerRunning ? '計時中' : (sessionElapsedSeconds > 0 ? '已暫停' : '準備就緒') }}
            </span>
          </div>
          <div class="text-[10px] text-slate-400 mt-0.5">
            {{ workoutStore.sessionTimerRunning ? `累計約 ${Math.max(1, Math.round(sessionElapsedSeconds / 60))} 分鐘` : (sessionElapsedSeconds > 0 ? '點擊繼續' : '點擊開始開練') }}
          </div>
        </div>

        <!-- Date Picker Box (Clean, responsive, never overflows) -->
        <div class="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-3 flex flex-col justify-between relative overflow-hidden group cursor-pointer hover:border-emerald-500/50 transition-colors">
          <div class="text-[10px] font-bold text-slate-400 flex items-center justify-between">
            <span>📅 訓練日期</span>
            <Calendar class="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div class="text-sm font-black text-white mt-1 truncate">
            {{ formattedDateDisplay }}
          </div>
          <div class="text-[10px] text-slate-400 mt-0.5">點擊更換日期</div>
          <!-- Transparent native date picker overlay -->
          <input
            v-model="workoutStore.sessionDate"
            type="date"
            class="absolute inset-0 opacity-0 w-full h-full cursor-pointer z-10"
          />
        </div>
      </div>

      <!-- Rest Timer Quick Setting Pill Selector -->
      <div class="pt-2 border-t border-slate-700/80 flex items-center justify-between">
        <div class="flex items-center gap-1.5 text-[11px] font-bold text-slate-300">
          <Timer class="w-3.5 h-3.5 text-emerald-400" />
          <span>組間休息預設：</span>
        </div>
        <div class="flex items-center gap-1 overflow-x-auto scrollbar-none">
          <button
            v-for="secs in [30, 45, 60, 90, 120, 180]"
            :key="secs"
            @click="workoutStore.setDefaultRestSeconds(secs)"
            class="px-2 py-0.5 rounded-lg text-[10px] font-black transition-all"
            :class="workoutStore.defaultRestSeconds === secs ? 'bg-emerald-500 text-slate-950 shadow-sm font-black' : 'bg-slate-800/90 text-slate-400 hover:bg-slate-700 hover:text-white'"
          >
            {{ secs }}s
          </button>
        </div>
      </div>

      <!-- Live Summary Metric Counters -->
      <div class="flex items-center justify-between pt-1 border-t border-slate-700/60 text-xs">
        <div class="flex items-center gap-1.5">
          <span class="text-slate-400 text-[11px]">累積總容量:</span>
          <span class="font-black text-emerald-400 text-sm">{{ currentTotalVolume }} kg</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-slate-400 text-[11px]">完成進度:</span>
          <span class="font-bold text-white text-xs">{{ completedSetsCount }} / {{ totalSetsCount }} 組</span>
        </div>
      </div>
    </div>

    <!-- Empty State if no exercises added -->
    <div v-if="workoutStore.activeExercises.length === 0" class="card-apple text-center py-12 space-y-3">
      <Dumbbell class="w-12 h-12 text-slate-300 mx-auto" />
      <div class="text-sm font-bold text-slate-800">尚未加入任何訓練動作</div>
      <p class="text-xs text-slate-400">點擊下方按鈕，從 40+ 黃金動作庫挑選今天想練的動作！</p>
      <button
        @click="showAddExerciseModal = true"
        class="py-2.5 px-6 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-extrabold text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all"
      >
        + 選擇第一個動作
      </button>
    </div>

    <!-- Active Exercises List -->
    <div v-else class="space-y-4">
      <div
        v-for="(ex, exIdx) in workoutStore.activeExercises"
        :key="ex.exercise_id"
        class="card-apple space-y-3 relative overflow-hidden"
      >
        <!-- Exercise Header & Per-Exercise Stopwatch -->
        <div class="flex items-start justify-between pb-2 border-b border-slate-100">
          <div>
            <div class="flex items-center gap-2">
              <span class="w-5 h-5 rounded-md bg-emerald-100 text-emerald-800 font-black text-xs flex items-center justify-center">
                {{ exIdx + 1 }}
              </span>
              <h3 class="text-sm font-black text-slate-900">{{ ex.name }}</h3>
              <span class="badge-emerald text-[10px]">{{ ex.target_muscle_group }}</span>
            </div>

            <!-- Single Exercise Stopwatch Controls -->
            <div class="flex items-center gap-2 mt-2">
              <button
                @click="handleToggleExerciseTimer(exIdx)"
                class="px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all"
                :class="ex.timerStatus === 'RUNNING' ? 'bg-amber-100 text-amber-800 hover:bg-amber-200' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'"
              >
                <component :is="ex.timerStatus === 'RUNNING' ? Pause : Play" class="w-3.5 h-3.5" />
                <span>{{ ex.timerStatus === 'RUNNING' ? '暫停單項' : (ex.elapsedSeconds > 0 ? '繼續單項' : '單項計時') }}</span>
              </button>
              <span v-if="ex.elapsedSeconds > 0" class="text-xs font-mono font-bold text-slate-700 bg-slate-50 px-2 py-1 rounded-md border border-slate-200">
                ⏱️ {{ formatSeconds(ex.elapsedSeconds) }}
              </span>
              <button
                v-if="ex.elapsedSeconds > 0"
                @click="workoutStore.resetExerciseTimer(exIdx)"
                class="text-[10px] text-slate-400 hover:text-slate-600 underline"
              >
                重設
              </button>
            </div>
          </div>

          <button
            @click="workoutStore.removeExercise(exIdx)"
            class="text-slate-300 hover:text-rose-500 p-1"
            title="移除此動作"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>

        <!-- Previous Set Performance Hint & Overload Suggestion -->
        <div v-if="previousHints[ex.exercise_id]" class="text-[11px] p-2.5 bg-gradient-to-r from-slate-50 to-emerald-50/40 rounded-xl text-slate-700 flex items-start gap-2 border border-slate-100">
          <Lightbulb class="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div class="leading-relaxed">
            <span class="font-bold text-slate-800">上次表現：</span>
            <span class="text-emerald-700 font-semibold">{{ previousHints[ex.exercise_id].last_weight_kg }}kg × {{ previousHints[ex.exercise_id].last_reps }}次 (1RM: {{ previousHints[ex.exercise_id].last_estimated_1rm }}kg)</span>
            <div class="text-[10px] text-slate-500 mt-0.5">{{ previousHints[ex.exercise_id].suggestion }}</div>
          </div>
        </div>

        <!-- Table Columns Header -->
        <div class="grid grid-cols-12 gap-1 text-center text-[10px] font-bold text-slate-400">
          <span class="col-span-2">組別</span>
          <span class="col-span-3">重量 (kg)</span>
          <span class="col-span-3">次數 (reps)</span>
          <span class="col-span-2">預估 1RM</span>
          <span class="col-span-2">打卡</span>
        </div>

        <!-- Sets Rows -->
        <div class="space-y-2">
          <div
            v-for="(set, setIdx) in ex.sets"
            :key="set.set_number"
            class="grid grid-cols-12 gap-1.5 items-center p-2 rounded-xl transition-all"
            :class="set.is_completed ? 'bg-emerald-50/80 border border-emerald-300/80 shadow-xs' : 'bg-slate-50 border border-slate-200/60'"
          >
            <!-- Set number -->
            <div class="col-span-2 text-center text-xs font-bold text-slate-700 flex items-center justify-center gap-1">
              <span>{{ set.set_number }}</span>
              <button
                v-if="ex.sets.length > 1 && !set.is_completed"
                @click="workoutStore.removeSet(exIdx, setIdx)"
                class="text-slate-300 hover:text-rose-400"
                title="刪除此組"
              >
                <X class="w-3 h-3" />
              </button>
            </div>

            <!-- Weight input -->
            <div class="col-span-3">
              <input
                v-model.number="set.weight_kg"
                type="number"
                step="0.5"
                class="w-full text-center py-2 bg-white border border-slate-200 rounded-lg text-xs font-black text-slate-900 focus:outline-none focus:border-brand-500 shadow-2xs"
                placeholder="kg"
              />
            </div>

            <!-- Reps input -->
            <div class="col-span-3">
              <input
                v-model.number="set.reps"
                type="number"
                class="w-full text-center py-2 bg-white border border-slate-200 rounded-lg text-xs font-black text-slate-900 focus:outline-none focus:border-brand-500 shadow-2xs"
                placeholder="次"
              />
            </div>

            <!-- Estimated 1RM display & PR indicator -->
            <div class="col-span-2 text-center text-[10px] font-bold text-slate-600 flex flex-col items-center justify-center">
              <span>{{ calculate1RM(set.weight_kg, set.reps) }}</span>
              <span v-if="isNewPR(ex.exercise_id, set.weight_kg, set.reps)" class="text-[9px] text-amber-600 font-extrabold flex items-center gap-0.5 animate-pulse">
                👑 PR!
              </span>
            </div>

            <!-- Complete checkmark button -->
            <div class="col-span-2 flex justify-center">
              <button
                @click="handleToggleSetComplete(exIdx, setIdx)"
                class="w-8 h-8 rounded-xl flex items-center justify-center transition-all active:scale-90"
                :class="set.is_completed ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/30 ring-2 ring-emerald-300' : 'bg-slate-200 text-slate-400 hover:bg-slate-300'"
                title="標記完成並啟動休息計時"
              >
                <Check class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Add Set Button -->
        <button
          @click="workoutStore.addSet(exIdx)"
          class="w-full py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs border border-dashed border-slate-300 flex items-center justify-center gap-1 active:scale-95 transition-all"
        >
          <Plus class="w-3.5 h-3.5 text-emerald-600" />
          <span>增加一組 (第 {{ ex.sets.length + 1 }} 組)</span>
        </button>
      </div>

      <!-- Add Another Exercise Button -->
      <button
        @click="showAddExerciseModal = true"
        class="w-full py-3.5 rounded-2xl bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs border border-slate-200 shadow-apple flex items-center justify-center gap-2 active:scale-98 transition-all"
      >
        <Plus class="w-4 h-4 text-brand-600" />
        <span>+ 新增其他訓練動作</span>
      </button>

      <!-- In-Flow Large Finish Button at Bottom of Page -->
      <div class="pt-2">
        <button
          @click="openSettlementModal"
          class="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-700 hover:from-emerald-600 hover:to-teal-800 text-white font-black text-sm shadow-float active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          <Trophy class="w-5 h-5 text-amber-300" />
          <span>🏁 完成並結束本次訓練</span>
        </button>
      </div>
    </div>

    <!-- Add Exercise Modal -->
    <div
      v-if="showAddExerciseModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 max-h-[85vh] overflow-y-auto space-y-3 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-black text-slate-900 text-base">選擇訓練動作</h3>
          <button @click="showAddExerciseModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <input
          v-model="exerciseSearch"
          type="text"
          placeholder="搜尋動作（如：臥推、深蹲、划船）..."
          class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
        />

        <div class="max-h-60 overflow-y-auto space-y-1.5">
          <div
            v-for="ex in filteredExerciseLibrary"
            :key="ex.id"
            @click="selectExerciseToAdd(ex)"
            class="p-2.5 rounded-xl bg-slate-50 hover:bg-brand-50 border border-slate-100 hover:border-brand-200 cursor-pointer flex items-center justify-between transition-colors"
          >
            <div>
              <div class="text-xs font-bold text-slate-900">{{ ex.name }}</div>
              <div class="text-[10px] text-slate-400">{{ ex.equipment }}</div>
            </div>
            <span class="badge-emerald text-[10px]">{{ ex.target_muscle_group }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Settlement / Completion Confirmation Modal -->
    <div
      v-if="showSettlementModal"
      class="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-6 max-h-[90vh] overflow-y-auto space-y-4 shadow-2xl animate-fade-in">
        <div class="text-center space-y-1">
          <div class="w-14 h-14 rounded-3xl bg-gradient-to-br from-amber-400 to-amber-600 text-white flex items-center justify-center mx-auto shadow-float">
            <Trophy class="w-7 h-7 text-white animate-bounce" />
          </div>
          <h2 class="text-lg font-black text-slate-900 pt-1">🎉 本次訓練結算</h2>
          <p class="text-xs text-slate-500">太棒了！確認數據後即可寫入歷史日誌並更新修復時鐘</p>
        </div>

        <!-- Metric Cards Grid in Settlement -->
        <div class="grid grid-cols-2 gap-2.5">
          <div class="p-3 rounded-2xl bg-slate-50 border border-slate-100 text-center">
            <div class="text-[10px] font-bold text-slate-400">總耗時</div>
            <div class="text-base font-black text-slate-900 mt-0.5">
              {{ finalDurationMinutes }} 分鐘
            </div>
            <div class="text-[9px] text-slate-400 mt-0.5">日期：{{ workoutStore.sessionDate }}</div>
          </div>
          <div class="p-3 rounded-2xl bg-emerald-50 border border-emerald-100 text-center">
            <div class="text-[10px] font-bold text-emerald-700">累積總容量</div>
            <div class="text-base font-black text-emerald-700 mt-0.5">
              {{ currentTotalVolume }} kg
            </div>
            <div class="text-[9px] text-emerald-600 mt-0.5">完成 {{ completedSetsCount }} 組動作</div>
          </div>
        </div>

        <!-- Exercises summary list -->
        <div class="space-y-1.5 max-h-44 overflow-y-auto bg-slate-50 p-2.5 rounded-2xl border border-slate-100">
          <div class="text-[11px] font-bold text-slate-600 px-1">📝 本次動作摘要：</div>
          <div
            v-for="(ex, i) in workoutStore.activeExercises"
            :key="ex.exercise_id"
            class="text-xs bg-white p-2 rounded-xl border border-slate-100 flex items-center justify-between"
          >
            <div>
              <span class="font-bold text-slate-800">{{ i + 1 }}. {{ ex.name }}</span>
              <span class="text-[10px] text-slate-400 ml-1.5">({{ getCompletedSetsForExercise(ex) }} 組)</span>
            </div>
            <span class="text-[11px] font-black text-emerald-700">
              最高 {{ getMaxWeightForExercise(ex) }}kg
            </span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-2 pt-2">
          <button
            @click="confirmFinishWorkout"
            :disabled="submitting"
            class="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            <Check class="w-4 h-4" />
            <span>{{ submitting ? '正在寫入日誌...' : '✅ 確認結算入庫' }}</span>
          </button>
          <button
            @click="showSettlementModal = false"
            class="py-3.5 px-4 rounded-xl bg-slate-100 text-slate-600 font-bold text-xs hover:bg-slate-200 active:scale-95"
          >
            返回繼續練
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import confetti from 'canvas-confetti'
import {
  Flame, Dumbbell, Trash2, Lightbulb, Plus, X, Check, Trophy, Play, Pause, Calendar
} from 'lucide-vue-next'
import { useWorkoutStore } from '@/stores/workout'
import { exercisesAPI } from '@/api/client'

const router = useRouter()
const workoutStore = useWorkoutStore()

const exerciseLibrary = ref([])
const showAddExerciseModal = ref(false)
const showSettlementModal = ref(false)
const exerciseSearch = ref('')
const previousHints = ref({})
const submitting = ref(false)

// Session live stopwatch state
const sessionElapsedSeconds = ref(workoutStore.getSessionElapsedSeconds())
let sessionTicker = null
let exerciseTimerInterval = null

const formattedDateDisplay = computed(() => {
  if (!workoutStore.sessionDate) return '今日訓練'
  try {
    const d = new Date(workoutStore.sessionDate + 'T00:00:00')
    if (isNaN(d.getTime())) return workoutStore.sessionDate
    const isCurrent = workoutStore.sessionDate === new Date().toISOString().substring(0, 10)
    const weekdays = ['週日', '週一', '週二', '週三', '週四', '週五', '週六']
    return `${d.getMonth() + 1}月${d.getDate()}日 (${weekdays[d.getDay()]})${isCurrent ? ' 📍' : ''}`
  } catch (e) {
    return workoutStore.sessionDate
  }
})

const formattedSessionTime = computed(() => {
  const secs = sessionElapsedSeconds.value
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = secs % 60
  if (h > 0) {
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const finalDurationMinutes = computed(() => {
  return Math.max(1, Math.round(sessionElapsedSeconds.value / 60))
})

const totalSetsCount = computed(() => {
  return workoutStore.activeExercises.reduce((acc, ex) => acc + ex.sets.length, 0)
})

const completedSetsCount = computed(() => {
  return workoutStore.activeExercises.reduce((acc, ex) => acc + ex.sets.filter(s => s.is_completed || s.weight_kg > 0).length, 0)
})

const currentTotalVolume = computed(() => {
  let vol = 0
  workoutStore.activeExercises.forEach(ex => {
    ex.sets.forEach(s => {
      if (s.is_completed || s.weight_kg > 0) {
        vol += (Number(s.weight_kg) || 0) * (Number(s.reps) || 0)
      }
    })
  })
  return vol.toLocaleString()
})

const filteredExerciseLibrary = computed(() => {
  if (!exerciseSearch.value) return exerciseLibrary.value
  const q = exerciseSearch.value.toLowerCase()
  return exerciseLibrary.value.filter(e => e.name.toLowerCase().includes(q) || (e.name_en && e.name_en.toLowerCase().includes(q)))
})

function toggleSessionTimer() {
  workoutStore.toggleSessionTimer()
  sessionElapsedSeconds.value = workoutStore.getSessionElapsedSeconds()
}

function handleToggleExerciseTimer(exIdx) {
  workoutStore.toggleExerciseTimer(exIdx)
  sessionElapsedSeconds.value = workoutStore.getSessionElapsedSeconds()
}

function handleToggleSetComplete(exIdx, setIdx) {
  workoutStore.toggleSetComplete(exIdx, setIdx, 90)
  sessionElapsedSeconds.value = workoutStore.getSessionElapsedSeconds()
}

function formatSeconds(secs) {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function calculate1RM(weight, reps) {
  const w = Number(weight) || 0
  const r = Number(reps) || 0
  if (w <= 0 || r <= 0) return '-'
  const est = Math.round(w * (1 + r / 30.0) * 10) / 10
  return `${est}kg`
}

function isNewPR(exerciseId, weight, reps) {
  const w = Number(weight) || 0
  const r = Number(reps) || 0
  if (w <= 0 || r <= 0) return false
  const hint = previousHints.value[exerciseId]
  if (!hint || !hint.last_estimated_1rm) return false
  const current1rm = w * (1 + r / 30.0)
  return current1rm > hint.last_estimated_1rm + 0.5
}

function getCompletedSetsForExercise(ex) {
  return ex.sets.filter(s => s.is_completed || s.weight_kg > 0).length
}

function getMaxWeightForExercise(ex) {
  let maxW = 0
  ex.sets.forEach(s => {
    if (s.weight_kg > maxW) maxW = s.weight_kg
  })
  return maxW
}

async function fetchExerciseLibrary() {
  try {
    const res = await exercisesAPI.list()
    exerciseLibrary.value = res.data
    for (const ex of workoutStore.activeExercises) {
      loadHint(ex.exercise_id)
    }
  } catch (err) {
    console.error('Failed to fetch exercises:', err)
  }
}

async function loadHint(exerciseId) {
  if (previousHints.value[exerciseId]) return
  try {
    const res = await exercisesAPI.getPreviousHint(exerciseId)
    previousHints.value[exerciseId] = res.data
  } catch (err) {}
}

function selectExerciseToAdd(ex) {
  workoutStore.addExerciseToActive(ex)
  loadHint(ex.id)
  showAddExerciseModal.value = false
  exerciseSearch.value = ''
}

function openSettlementModal() {
  const hasData = workoutStore.activeExercises.some(ex => ex.sets.some(s => s.weight_kg > 0 || s.reps > 0 || s.is_completed))
  if (!hasData) {
    alert('請至少填寫 1 組動作的重量或次數再結算！')
    return
  }
  showSettlementModal.value = true
}

async function confirmFinishWorkout() {
  submitting.value = true
  try {
    await workoutStore.finishWorkout(finalDurationMinutes.value, workoutStore.sessionDate)
    showSettlementModal.value = false
    
    // Confetti celebration
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    })

    alert('🎉 恭喜完成訓練！已成功寫入日誌並更新肌肉修復時鐘。')
    router.push('/')
  } catch (err) {
    alert(err.message || '儲存失敗，請稍後再試')
  } finally {
    submitting.value = false
  }
}

function handleCancelWorkout() {
  if (confirm('確定要放棄當前訓練嗎？未儲存的輸入內容將會被清空。')) {
    workoutStore.cancelWorkout()
    router.push('/workout')
  }
}

onMounted(() => {
  if (!workoutStore.isWorkoutActive) {
    workoutStore.startWorkout('今日自訂訓練')
  }

  fetchExerciseLibrary()

  sessionElapsedSeconds.value = workoutStore.getSessionElapsedSeconds()

  sessionTicker = setInterval(() => {
    sessionElapsedSeconds.value = workoutStore.getSessionElapsedSeconds()
  }, 500)

  // Per-exercise stopwatch ticker
  exerciseTimerInterval = setInterval(() => {
    workoutStore.syncExerciseTimers()
  }, 500)
})

onUnmounted(() => {
  clearInterval(sessionTicker)
  clearInterval(exerciseTimerInterval)
})
</script>
