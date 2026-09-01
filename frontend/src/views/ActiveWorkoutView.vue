<template>
  <div class="pb-32 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Active Workout Header Banner -->
    <div class="card-apple bg-gradient-to-r from-slate-900 to-slate-800 text-white border-0 shadow-lg p-4">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <Flame class="w-5 h-5 text-emerald-400 animate-pulse" />
          <span class="text-xs font-bold text-slate-300">實戰訓練中</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="text-xs font-mono font-bold bg-white/10 px-2.5 py-1 rounded-lg text-emerald-400">
            ⏱️ {{ formattedDuration }}
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between">
        <h1 class="text-lg font-black text-white truncate mr-2">{{ workoutStore.sessionName }}</h1>
        <div class="text-right flex-shrink-0">
          <div class="text-[10px] text-slate-400">當前累積總容量</div>
          <div class="text-sm font-black text-emerald-400">{{ currentTotalVolume }} kg</div>
        </div>
      </div>
    </div>

    <!-- Empty State if no exercises added -->
    <div v-if="workoutStore.activeExercises.length === 0" class="card-apple text-center py-10 space-y-3">
      <Dumbbell class="w-10 h-10 text-slate-300 mx-auto" />
      <div class="text-sm font-bold text-slate-800">尚未加入任何訓練動作</div>
      <p class="text-xs text-slate-400">點擊下方按鈕從 40+ 黃金動作庫挑選動作！</p>
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
        class="card-apple space-y-3"
      >
        <!-- Exercise Header -->
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-lg bg-emerald-50 text-emerald-700 font-black text-xs flex items-center justify-center">
              {{ exIdx + 1 }}
            </span>
            <div>
              <h3 class="text-sm font-black text-slate-900">{{ ex.name }}</h3>
              <div class="text-[10px] text-slate-400">{{ ex.target_muscle_group }}</div>
            </div>
          </div>
          <button
            @click="workoutStore.removeExercise(exIdx)"
            class="text-slate-300 hover:text-rose-500 p-1"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>

        <!-- Previous Set Performance Hint -->
        <div v-if="previousHints[ex.exercise_id]" class="text-[11px] p-2 bg-slate-50 rounded-xl text-slate-600 flex items-start gap-1.5 border border-slate-100">
          <Lightbulb class="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <span>{{ previousHints[ex.exercise_id].suggestion }}</span>
        </div>

        <!-- Table Header -->
        <div class="grid grid-cols-12 gap-1.5 text-center text-[10px] font-bold text-slate-400">
          <span class="col-span-2">組別</span>
          <span class="col-span-3">重量 (kg)</span>
          <span class="col-span-3">次數 (reps)</span>
          <span class="col-span-2">RPE</span>
          <span class="col-span-2">完成</span>
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

            <!-- RPE input -->
            <div class="col-span-2">
              <input
                v-model.number="set.rpe"
                type="number"
                step="0.5"
                min="6"
                max="10"
                class="w-full text-center py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:border-brand-500"
                placeholder="RPE"
              />
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
          <span>增加一組 (Set {{ ex.sets.length + 1 }})</span>
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

    <!-- Bottom Fixed Actions -->
    <div class="fixed bottom-0 left-0 right-0 p-4 bg-white/95 backdrop-blur-md border-t border-slate-200/80 z-30 max-w-lg mx-auto">
      <div class="flex items-center gap-2">
        <button
          @click="handleFinishWorkout"
          :disabled="submitting"
          class="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          <CheckCircle2 class="w-4 h-4" />
          <span>{{ submitting ? '正在儲存日誌...' : '🎉 結束並儲存訓練' }}</span>
        </button>
        <button
          @click="handleCancelWorkout"
          class="py-3 px-4 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-500 hover:text-rose-600 font-bold text-xs active:scale-95 transition-all"
        >
          放棄
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
          placeholder="搜尋動作（如：臥推、深蹲）..."
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
  Flame, Dumbbell, Trash2, Lightbulb, Plus, X, Check, CheckCircle2
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

const durationSeconds = ref(0)
let durationTimer = null

const formattedDuration = computed(() => {
  const m = Math.floor(durationSeconds.value / 60)
  const s = durationSeconds.value % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const currentTotalVolume = computed(() => {
  let vol = 0
  workoutStore.activeExercises.forEach(ex => {
    ex.sets.forEach(s => {
      if (s.is_completed) {
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
    // Fetch previous set hints for active exercises
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
  const completedSetsCount = workoutStore.activeExercises.reduce((acc, ex) => acc + ex.sets.filter(s => s.is_completed).length, 0)
  if (completedSetsCount === 0) {
    alert('請至少完成並勾選 1 組動作！')
    return
  }

  submitting.value = true
  try {
    await workoutStore.finishWorkout()
    
    // Confetti celebration!
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    })

    alert('🎉 恭喜完成今日訓練！已紀錄至歷史日誌並更新肌肉修復時鐘。')
    router.push('/')
  } catch (err) {
    alert('儲存失敗，請稍後再試')
  } finally {
    submitting.value = false
  }
}

function handleCancelWorkout() {
  if (confirm('確定要放棄當前訓練嗎？所有已填寫資料將被清除。')) {
    workoutStore.cancelWorkout()
    router.push('/workout')
  }
}

onMounted(() => {
  if (!workoutStore.isWorkoutActive) {
    workoutStore.startWorkout('今日自由訓練')
  }

  fetchExerciseLibrary()

  // Calculate elapsed time from start
  if (workoutStore.startTime) {
    const elapsed = Math.floor((new Date() - new Date(workoutStore.startTime)) / 1000)
    durationSeconds.value = Math.max(0, elapsed)
  }

  durationTimer = setInterval(() => {
    durationSeconds.value++
  }, 1000)
})

onUnmounted(() => {
  clearInterval(durationTimer)
})
</script>
