<template>
  <div class="pb-36 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header: Quick Mode / Session Info -->
    <div class="card-apple bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white border-0 shadow-xl p-4.5 space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-black">
            <ClipboardList class="w-4 h-4" />
          </div>
          <div>
            <h1 class="text-base font-black text-white">訓練打卡與數據記錄</h1>
            <p class="text-[11px] text-slate-400">組間隨手記 · 練完事後補填 · 自動試算 1RM/PR</p>
          </div>
        </div>
        <button
          @click="handleCancelWorkout"
          class="text-xs text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          title="清空並離開"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Quick Session Controls -->
      <div class="grid grid-cols-2 gap-2 pt-2 border-t border-slate-700/60">
        <div>
          <label class="block text-[10px] font-bold text-slate-400 mb-1">📅 訓練日期</label>
          <input
            v-model="workoutStore.sessionDate"
            type="date"
            class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white font-medium focus:outline-none focus:border-emerald-500"
          />
        </div>
        <div>
          <label class="block text-[10px] font-bold text-slate-400 mb-1">⏱️ 總時長 (分鐘)</label>
          <input
            v-model.number="workoutStore.durationMinutes"
            type="number"
            min="5"
            step="5"
            class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white font-medium focus:outline-none focus:border-emerald-500"
          />
        </div>
      </div>

      <!-- Summary Stats Bar -->
      <div class="flex items-center justify-between pt-1 text-xs">
        <div class="flex items-center gap-1.5">
          <span class="text-slate-400">累積總容量:</span>
          <span class="font-black text-emerald-400">{{ currentTotalVolume }} kg</span>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-slate-400">已記錄動作:</span>
          <span class="font-bold text-white">{{ workoutStore.activeExercises.length }} 項</span>
        </div>
      </div>
    </div>

    <!-- Empty State if no exercises added -->
    <div v-if="workoutStore.activeExercises.length === 0" class="card-apple text-center py-10 space-y-3">
      <Dumbbell class="w-12 h-12 text-slate-300 mx-auto" />
      <div class="text-sm font-bold text-slate-800">尚未加入任何訓練動作</div>
      <p class="text-xs text-slate-400">點擊下方按鈕，挑選今天練習的動作並填寫重量與次數！</p>
      <button
        @click="showAddExerciseModal = true"
        class="py-2.5 px-5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-extrabold text-xs shadow-sm active:scale-95 transition-all"
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
                @click="workoutStore.toggleExerciseTimer(exIdx)"
                class="px-2.5 py-1 rounded-lg text-xs font-bold flex items-center gap-1 transition-all"
                :class="ex.timerStatus === 'RUNNING' ? 'bg-amber-100 text-amber-800 hover:bg-amber-200' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'"
              >
                <component :is="ex.timerStatus === 'RUNNING' ? Pause : Play" class="w-3.5 h-3.5" />
                <span>{{ ex.timerStatus === 'RUNNING' ? '暫停計時' : (ex.elapsedSeconds > 0 ? '繼續計時' : '單項計時') }}</span>
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

        <!-- PR Banner & Progressive Overload Hint -->
        <div v-if="previousHints[ex.exercise_id]" class="space-y-1.5">
          <!-- PR Stats Box -->
          <div class="grid grid-cols-2 gap-2 p-2 rounded-xl bg-amber-50/70 border border-amber-200/80 text-amber-950 text-xs">
            <div class="flex items-center gap-1.5">
              <Trophy class="w-4 h-4 text-amber-600 flex-shrink-0" />
              <div>
                <div class="text-[10px] text-amber-700/80 font-bold">歷史最大負重 PR</div>
                <div class="font-black text-amber-900">
                  {{ previousHints[ex.exercise_id].pr_max_weight_kg > 0 ? `${previousHints[ex.exercise_id].pr_max_weight_kg} kg` : '尚無紀錄' }}
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <Crown class="w-4 h-4 text-amber-600 flex-shrink-0" />
              <div>
                <div class="text-[10px] text-amber-700/80 font-bold">最佳預估 1RM</div>
                <div class="font-black text-amber-900">
                  {{ previousHints[ex.exercise_id].pr_max_1rm > 0 ? `${previousHints[ex.exercise_id].pr_max_1rm} kg` : '尚無紀錄' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Suggestion -->
          <div class="text-[11px] p-2 bg-slate-50 rounded-xl text-slate-600 flex items-start gap-1.5 border border-slate-100">
            <Lightbulb class="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div class="leading-relaxed">
              <span v-if="previousHints[ex.exercise_id].last_weight_kg > 0" class="font-bold text-slate-700">
                上次做功：{{ previousHints[ex.exercise_id].last_weight_kg }}kg × {{ previousHints[ex.exercise_id].last_reps }}次
                ·
              </span>
              <span>{{ previousHints[ex.exercise_id].suggestion }}</span>
            </div>
          </div>
        </div>

        <!-- Table Header -->
        <div class="grid grid-cols-12 gap-1.5 text-center text-[10px] font-bold text-slate-400 pt-1">
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
            class="grid grid-cols-12 gap-1.5 items-center p-1.5 rounded-xl transition-all"
            :class="set.is_completed ? 'bg-emerald-50/70 border border-emerald-200/60' : 'bg-slate-50 border border-slate-100'"
          >
            <!-- Set number -->
            <div class="col-span-2 text-center text-xs font-bold text-slate-700 flex items-center justify-center gap-1">
              <span>{{ set.set_number }}</span>
              <button
                v-if="ex.sets.length > 1 && !set.is_completed"
                @click="workoutStore.removeSet(exIdx, setIdx)"
                class="text-slate-300 hover:text-rose-400"
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
                class="w-full text-center py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-black text-slate-900 focus:outline-none focus:border-brand-500"
                placeholder="kg"
              />
            </div>

            <!-- Reps input -->
            <div class="col-span-3">
              <input
                v-model.number="set.reps"
                type="number"
                class="w-full text-center py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-black text-slate-900 focus:outline-none focus:border-brand-500"
                placeholder="次"
              />
            </div>

            <!-- 1RM live display & PR Badge -->
            <div class="col-span-2 text-center">
              <div class="text-[11px] font-black text-slate-700">
                {{ calculate1RM(set.weight_kg, set.reps) }}
              </div>
              <div
                v-if="isNewPR(ex.exercise_id, set.weight_kg, set.reps)"
                class="text-[9px] font-black text-amber-600 bg-amber-100 px-1 py-0.2 rounded-full animate-bounce"
              >
                🔥 PR!
              </div>
            </div>

            <!-- Complete checkmark button -->
            <div class="col-span-2 flex justify-center">
              <button
                @click="workoutStore.toggleSetComplete(exIdx, setIdx, 90)"
                class="w-8 h-8 rounded-lg flex items-center justify-center transition-all active:scale-90"
                :class="set.is_completed ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-500/30' : 'bg-slate-200 text-slate-400 hover:bg-slate-300'"
              >
                <Check class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Add Set Button -->
        <button
          @click="workoutStore.addSet(exIdx)"
          class="w-full py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 font-bold text-xs border border-dashed border-slate-300 flex items-center justify-center gap-1 active:scale-95 transition-all"
        >
          <Plus class="w-3.5 h-3.5" />
          <span>增加一組 (第 {{ ex.sets.length + 1 }} 組)</span>
        </button>
      </div>

      <!-- Add Another Exercise Button -->
      <button
        @click="showAddExerciseModal = true"
        class="w-full py-3 rounded-2xl bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs border border-slate-200 shadow-sm flex items-center justify-center gap-1.5 active:scale-98 transition-all"
      >
        <Plus class="w-4 h-4 text-brand-600" />
        <span>+ 新增其他訓練動作</span>
      </button>
    </div>

    <!-- Bottom Fixed Actions: Clean & Easy Save -->
    <div class="fixed bottom-0 left-0 right-0 p-4 bg-white/95 backdrop-blur-md border-t border-slate-200/80 z-30 max-w-lg mx-auto">
      <div class="flex items-center gap-2">
        <button
          @click="handleFinishWorkout"
          :disabled="submitting"
          class="flex-1 py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          <Save class="w-4 h-4" />
          <span>{{ submitting ? '正在儲存日誌...' : '💾 儲存今日訓練紀錄' }}</span>
        </button>
        <button
          @click="handleCancelWorkout"
          class="py-3.5 px-4 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 font-bold text-xs active:scale-95 transition-all"
        >
          取消離開
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
          class="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import confetti from 'canvas-confetti'
import {
  ClipboardList, Dumbbell, Trash2, Lightbulb, Plus, X, Check, Save, Trophy, Crown, Play, Pause
} from 'lucide-vue-next'
import { useWorkoutStore } from '@/stores/workout'
import { exercisesAPI } from '@/api/client'

const router = useRouter()
const workoutStore = useWorkoutStore()

const exerciseLibrary = ref([])
const showAddExerciseModal = ref(false)
const exerciseSearch = ref('')
const previousHints = ref({})
const submitting = ref(false)

let exerciseTimerInterval = null

// Calculate Live Epley 1RM: weight * (1 + reps / 30)
function calculate1RM(weight, reps) {
  const w = Number(weight) || 0
  const r = Number(reps) || 0
  if (w <= 0 || r <= 0) return '-'
  const est = Math.round(w * (1 + r / 30.0) * 10) / 10
  return `${est} kg`
}

// Check if current set breaks personal record
function isNewPR(exerciseId, weight, reps) {
  const w = Number(weight) || 0
  const r = Number(reps) || 0
  if (w <= 0 || r <= 0) return false
  const hint = previousHints.value[exerciseId]
  if (!hint || !hint.pr_max_1rm) return false
  const current1rm = w * (1 + r / 30.0)
  return current1rm > hint.pr_max_1rm + 0.5
}

function formatSeconds(secs) {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

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

async function handleFinishWorkout() {
  const hasData = workoutStore.activeExercises.some(ex => ex.sets.some(s => s.weight_kg > 0 || s.reps > 0 || s.is_completed))
  if (!hasData) {
    alert('請至少填寫 1 組動作的重量或次數！')
    return
  }

  submitting.value = true
  try {
    await workoutStore.finishWorkout(workoutStore.durationMinutes, workoutStore.sessionDate)
    
    // Confetti celebration!
    confetti({
      particleCount: 90,
      spread: 70,
      origin: { y: 0.6 }
    })

    alert('🎉 儲存成功！已寫入訓練日誌並同步更新肌肉修復狀態。')
    router.push('/')
  } catch (err) {
    alert(err.message || '儲存失敗，請稍後再試')
  } finally {
    submitting.value = false
  }
}

function handleCancelWorkout() {
  if (workoutStore.activeExercises.length === 0) {
    workoutStore.cancelWorkout()
    router.push('/workout')
    return
  }

  if (confirm('確定要離開嗎？未儲存的輸入內容將會被清空。')) {
    workoutStore.cancelWorkout()
    router.push('/workout')
  }
}

onMounted(() => {
  if (!workoutStore.isWorkoutActive) {
    workoutStore.startWorkout('今日自訂訓練')
  }

  fetchExerciseLibrary()

  // Per-exercise stopwatch ticker
  exerciseTimerInterval = setInterval(() => {
    workoutStore.activeExercises.forEach(ex => {
      if (ex.timerStatus === 'RUNNING') {
        ex.elapsedSeconds = (ex.elapsedSeconds || 0) + 1
      }
    })
  }, 1000)
})

onUnmounted(() => {
  clearInterval(exerciseTimerInterval)
})
</script>
