<template>
  <div class="h-[calc(100dvh-3.5rem-4.5rem)] flex flex-col max-w-lg mx-auto px-3.5 pb-1 select-none overflow-hidden">
    <!-- Clean Sub-Toolbar (No Duplicate App Navbar) -->
    <div class="flex-shrink-0 flex items-center justify-between py-2 border-b border-slate-200/80 bg-slate-50">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-xl bg-gradient-to-br from-brand-500 to-teal-600 text-white flex items-center justify-center shadow-xs">
          <Bot class="w-4 h-4" />
        </div>
        <div>
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-black text-slate-900">Gemini AI 隨身健身顧問</span>
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <p class="text-[9px] text-slate-400">已即時連線你的體態與營養數據</p>
        </div>
      </div>
      <button
        @click="clearChat"
        class="text-[10px] font-bold text-slate-500 hover:text-slate-700 px-2 py-1 rounded-lg bg-slate-200/70 hover:bg-slate-200 transition-colors"
      >
        清空重開
      </button>
    </div>

    <!-- Chat Messages Scroll Area -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto space-y-3 pr-1 py-2 min-h-0 select-text">
      <!-- Welcome Intro Bubble -->
      <div class="flex items-start gap-2">
        <div class="w-7 h-7 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
          <Bot class="w-4 h-4" />
        </div>
        <div class="bg-white border border-slate-200/80 rounded-2xl rounded-tl-sm p-3.5 text-xs text-slate-700 leading-relaxed shadow-apple space-y-2 max-w-[85%]">
          <p>
            嗨，<strong>{{ authStore.user?.name || '朋友' }}</strong>！我是你的專屬健身 AI 教練。
          </p>
          <div class="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-xl border border-slate-100 space-y-0.5">
            <div class="font-bold text-slate-800">📊 即時體態掌握：</div>
            <div>· 目標：<span class="font-bold text-emerald-700">{{ getGoalText(authStore.profile?.fitness_goal) }}</span></div>
            <div>· 今日蛋白質已攝取：<span class="font-bold text-emerald-700">{{ nutritionStore.dailyProgress?.consumed_protein_g || 0 }}g</span> / {{ authStore.profile?.target_protein_g || 140 }}g</div>
            <div>· 聊完如果想要排課，可以直接點擊按鈕【👉 採用此課表並立即開練】！</div>
          </div>
        </div>
      </div>

      <!-- Messages list -->
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="flex items-start gap-2"
        :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
      >
        <!-- Avatar -->
        <div
          v-if="msg.role === 'assistant'"
          class="w-7 h-7 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs"
        >
          <Bot class="w-4 h-4" />
        </div>
        <div
          v-else
          class="w-7 h-7 rounded-xl bg-slate-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold shadow-2xs"
        >
          {{ (authStore.user?.name || 'U').charAt(0).toUpperCase() }}
        </div>

        <!-- Bubble -->
        <div
          class="p-3.5 rounded-2xl text-xs leading-relaxed max-w-[85%] space-y-2"
          :class="msg.role === 'user' ? 'bg-brand-500 text-white rounded-tr-sm shadow-sm' : 'bg-white border border-slate-200/80 text-slate-800 rounded-tl-sm shadow-apple'"
        >
          <div class="whitespace-pre-wrap">{{ cleanMessageText(msg.content) }}</div>

          <!-- Structured Routine Card with 1-Click Adopt Button -->
          <div
            v-if="msg.suggested_routine"
            class="p-3 rounded-xl bg-emerald-50/90 border border-emerald-200 space-y-2.5 text-slate-800"
          >
            <div class="flex items-center gap-1.5 font-black text-emerald-900 text-xs">
              <Sparkles class="w-3.5 h-3.5 text-emerald-600" />
              <span>{{ msg.suggested_routine.routine_title }}</span>
            </div>

            <div class="space-y-1">
              <div
                v-for="(ex, i) in msg.suggested_routine.exercises"
                :key="i"
                class="text-[11px] bg-white p-2 rounded-lg border border-emerald-100 flex items-center justify-between"
              >
                <div>
                  <span class="font-bold text-slate-900">{{ i + 1 }}. {{ ex.exercise_name }}</span>
                  <span class="text-[10px] text-slate-400 ml-1">({{ ex.target_sets }}組 × {{ ex.target_reps }}次)</span>
                </div>
                <span class="badge-emerald text-[9px]">{{ ex.target_muscle_group }}</span>
              </div>
            </div>

            <button
              @click="adoptRoutine(msg.suggested_routine)"
              class="w-full py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-black shadow-sm active:scale-95 transition-all flex items-center justify-center gap-1"
            >
              <Flame class="w-3.5 h-3.5" />
              <span>👉 採用此課表並立即開練</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="flex items-start gap-2">
        <div class="w-7 h-7 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0">
          <Bot class="w-4 h-4 animate-spin" />
        </div>
        <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-3 text-xs text-slate-400 shadow-apple flex items-center gap-1.5">
          <span>AI 教練正在思考並規劃中...</span>
        </div>
      </div>
    </div>

    <!-- Quick Prompt Pills & Message Input Bar (Fixed cleanly at bottom of chat area) -->
    <div class="flex-shrink-0 pt-1.5 pb-2 bg-slate-50 space-y-1.5 border-t border-slate-200/80">
      <!-- Quick Prompt Pills -->
      <div class="flex gap-1.5 overflow-x-auto scrollbar-none py-0.5">
        <button
          v-for="pill in promptPills"
          :key="pill"
          @click="sendMessageWithText(pill)"
          :disabled="loading"
          class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-200/80 text-slate-700 hover:bg-emerald-100 hover:text-emerald-800 whitespace-nowrap border border-slate-300/50 active:scale-95 transition-all"
        >
          {{ pill }}
        </button>
      </div>

      <!-- Message Input Bar -->
      <div class="flex items-center gap-2">
        <input
          v-model="inputMessage"
          type="text"
          placeholder="向 AI 詢問訓練菜單、換動作或飲食建議..."
          @keyup.enter="sendMessage"
          :disabled="loading"
          class="flex-1 px-3.5 py-2.5 bg-white border border-slate-300/80 rounded-xl text-xs font-semibold focus:outline-none focus:border-brand-500 shadow-2xs"
        />
        <button
          @click="sendMessage"
          :disabled="loading || !inputMessage.trim()"
          class="w-10 h-10 rounded-xl bg-brand-500 hover:bg-brand-600 text-white flex items-center justify-center shadow-md shadow-brand-500/20 active:scale-95 transition-all disabled:opacity-40 flex-shrink-0"
        >
          <Send class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Bot, Send, Sparkles, Flame } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useWorkoutStore } from '@/stores/workout'
import { useNutritionStore } from '@/stores/nutrition'
import { aiAPI, exercisesAPI } from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()
const workoutStore = useWorkoutStore()
const nutritionStore = useNutritionStore()

const chatContainer = ref(null)
const inputMessage = ref('')
const loading = ref(false)
const messages = ref([])

const promptPills = [
  '今天只有啞鈴，幫我排一套 45 分鐘推胸三頭課表',
  '深蹲時下背微痠，可以換成什麼腿部動作？',
  '我今天蛋白質還差 35g，超商推薦買什麼？',
  '減脂期卡關一週該怎麼微調熱量？'
]

function getGoalText(goal) {
  if (goal === 'BULKING') return '增肌期'
  if (goal === 'CUTTING') return '減脂緊實期'
  return '體態維持'
}

function cleanMessageText(text) {
  if (!text) return ''
  return text.replace(/```(?:json)?\s*[\s\S]*?```/g, '').trim()
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function clearChat() {
  messages.value = []
}

async function sendMessageWithText(text) {
  inputMessage.value = text
  await sendMessage()
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const history = messages.value.slice(-4).map(m => ({ role: m.role, content: m.content }))
    const res = await aiAPI.chat(text, history)
    messages.value.push({
      role: 'assistant',
      content: res.data.reply,
      suggested_routine: res.data.suggested_routine || null
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: 'AI 連線暫時中斷，請確認網路或 API Key 設定。',
      suggested_routine: null
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function adoptRoutine(routine) {
  if (!routine) return

  try {
    const exRes = await exercisesAPI.list()
    const allEx = exRes.data

    workoutStore.startWorkout(routine.routine_title || 'AI 教練推薦課表')
    
    for (const item of routine.exercises) {
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
        timerStatus: 'IDLE',
        elapsedSeconds: 0,
        sets
      })
    }

    router.push('/active-workout')
  } catch (err) {
    console.error('Error adopting routine:', err)
  }
}

onMounted(() => {
  nutritionStore.fetchTodayProgress()
})
</script>
