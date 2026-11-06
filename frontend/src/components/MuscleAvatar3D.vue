<template>
  <div class="rounded-2xl overflow-hidden bg-white border border-slate-200/90 shadow-sm relative select-none">
    <!-- Top Bar: Character Identity + Aura Switcher (Row 1) & 360° Camera Controls (Row 2) -->
    <div class="px-3 pt-2.5 pb-2 space-y-2 border-b border-slate-100 bg-slate-50/80">
      <!-- Row 1: Automatic Character Badge + Fixed-Height Non-Wrapping Aura Switch Button -->
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-white border border-slate-200/90 shadow-2xs shrink-0 whitespace-nowrap">
          <span class="text-sm leading-none">{{ isFemale ? '👧' : '👦' }}</span>
          <span class="text-xs font-black text-slate-800 whitespace-nowrap">
            {{ isFemale ? '活力馬尾女' : '熱血格鬥肌霸' }}
          </span>
          <span class="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-500 whitespace-nowrap">
            3D 體態
          </span>
        </div>

        <!-- Streak Aura Power Badge (Clickable to switch Aura / Sloth Mode!) -->
        <button
          type="button"
          @click="cycleAura"
          class="flex items-center justify-center gap-1 px-2.5 py-1 rounded-xl text-[10px] font-black transition-all border cursor-pointer active:scale-95 shadow-2xs whitespace-nowrap shrink-0"
          :class="getAuraBadgeClass(currentAura.key)"
          :title="currentAura.desc + '（點擊切換下個光環狀態）'"
        >
          <span>{{ currentAuraBadgeText }}</span>
          <span class="text-[9px] opacity-75">⇄</span>
        </button>
      </div>

      <!-- Row 2: 3D View Angle, Thermal Glow Toggle & Auto-Spin Controls (4-column grid, never wraps!) -->
      <div class="grid grid-cols-4 gap-1.5">
        <button
          type="button"
          @click="rotateToAngle(-0.55)"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all whitespace-nowrap text-center"
          :class="!autoRotate && Math.cos(yaw) >= 0 ? 'bg-slate-900 text-white shadow-2xs' : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'"
        >
          正面
        </button>
        <button
          type="button"
          @click="rotateToAngle(Math.PI - 0.55)"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all whitespace-nowrap text-center"
          :class="!autoRotate && Math.cos(yaw) < 0 ? 'bg-slate-900 text-white shadow-2xs' : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'"
        >
          背面(背/臀)
        </button>
        <button
          type="button"
          @click="toggleAutoRotate"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all border whitespace-nowrap text-center"
          :class="autoRotate
            ? 'bg-emerald-50 text-emerald-700 border-emerald-300 shadow-2xs'
            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
        >
          {{ autoRotate ? '🔄 轉圈中' : '🔄 360°轉圈' }}
        </button>
        <button
          type="button"
          @click="showHotspotGlow = !showHotspotGlow"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all border whitespace-nowrap text-center"
          :class="showHotspotGlow
            ? 'bg-rose-50 text-rose-700 border-rose-200'
            : 'bg-white text-slate-500 border-slate-200'"
          title="切換公仔身上的肌肉熱點發光顯示"
        >
          {{ showHotspotGlow ? '🔥 熱點:開' : '🔥 熱點:關' }}
        </button>
      </div>
    </div>

    <!-- Second Bar: Cute 3D Clay Workout Animations -->
    <div class="px-3 py-1.5 bg-white border-b border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
      <span class="text-[10px] font-bold text-slate-400 whitespace-nowrap shrink-0">🎬 動作：</span>
      <div class="flex items-center gap-1 shrink-0">
        <button
          v-for="act in workoutActions"
          :key="act.key"
          type="button"
          @click="currentAction = act.key"
          class="px-2.5 py-1 rounded-lg text-[10px] font-extrabold whitespace-nowrap shrink-0 transition-all"
          :class="currentAction === act.key
            ? 'bg-slate-900 text-white shadow-2xs'
            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          {{ act.icon }} {{ act.label }}
        </button>
      </div>
    </div>

    <!-- Main WebGL Raymarched 3D Soft-Clay Studio Stage -->
    <div
      class="relative w-full h-80 sm:h-88 flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing"
      style="background: radial-gradient(circle at 50% 45%, #ffffff 0%, #f8fafc 65%, #eef2f6 100%);"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointerleave="onPointerUp"
    >
      <!-- Real-Time WebGL 3D SDF Soft-Clay Shader Canvas -->
      <canvas
        ref="glCanvasRef"
        class="w-full h-full object-contain"
      ></canvas>

      <!-- Floating Interactive Reaction Speech Bubble (When Character is Clicked or in Sloth Mode!) -->
      <transition name="reaction-pop">
        <div
          v-if="showReactionBubble || currentAction === 'SLOTH'"
          class="absolute top-11 sm:top-12 left-1/2 -translate-x-1/2 z-30 pointer-events-none flex items-center gap-1.5 backdrop-blur-md px-3.5 py-1.5 rounded-2xl shadow-xl border text-xs font-black whitespace-nowrap"
          :class="currentAction === 'SLOTH'
            ? 'bg-indigo-950/95 text-indigo-100 border-indigo-400/40 animate-pulse'
            : 'bg-slate-900/95 text-white border-white/20 animate-bounce'"
        >
          <span class="text-base">{{ currentAction === 'SLOTH' ? '💤' : reactionEmoji }}</span>
          <span>{{ currentAction === 'SLOTH' ? '呼... 偷懶好舒服... 快帶我去運動點燃光環！' : reactionMessage }}</span>
          <div
            class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rotate-45 border-r border-b"
            :class="currentAction === 'SLOTH' ? 'bg-indigo-950/95 border-indigo-400/40' : 'bg-slate-900/95 border-white/20'"
          ></div>
        </div>
      </transition>

      <!-- Top-Center Compact Legend Overlay (Unobtrusive) -->
      <div class="absolute top-2 left-1/2 -translate-x-1/2 flex items-center gap-2 sm:gap-3 bg-white/95 backdrop-blur-xs px-2.5 py-0.5 rounded-full border border-slate-200/80 shadow-2xs z-20 text-[9px] font-bold text-slate-600 whitespace-nowrap">
        <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>疲勞(&lt;45%)</span>
        <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>修復中</span>
        <span class="flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>滿血待命</span>
      </div>

      <!-- SVG Dynamic Leader Lines (Connects left/right cards directly to 3D character body points) -->
      <svg
        class="absolute inset-0 w-full h-full pointer-events-none z-10"
        :viewBox="`0 0 ${stageSize.w} ${stageSize.h}`"
      >
        <g v-for="line in leaderLines" :key="line.key">
          <!-- Connecting curved leader line -->
          <path
            :d="line.path"
            :stroke="line.stroke"
            :stroke-width="line.isSelected ? 2.0 : 1.2"
            :stroke-dasharray="line.visible ? 'none' : '3,3'"
            :opacity="line.isSelected ? 0.95 : (line.visible ? 0.55 : 0.22)"
            fill="none"
          />
          <!-- Anchor dot at side card -->
          <circle
            :cx="line.cardX"
            :cy="line.cardY"
            :r="line.isSelected ? 3.0 : 2.0"
            :fill="line.stroke"
            :opacity="line.visible ? 0.9 : 0.35"
          />
          <!-- Target indicator dot on 3D body -->
          <circle
            :cx="line.bodyX"
            :cy="line.bodyY"
            :r="line.isSelected ? 4.2 : 2.8"
            :fill="line.stroke"
            :opacity="line.visible ? 1.0 : 0.35"
          />
          <!-- Pulsing ping ring on body for fatigued or selected muscle -->
          <circle
            v-if="(line.isSelected || line.status === 'FATIGUED') && line.visible"
            :cx="line.bodyX"
            :cy="line.bodyY"
            r="6.5"
            :stroke="line.stroke"
            fill="none"
            class="animate-ping"
          />
        </g>
      </svg>

      <!-- Left Column Cards: SHOULDERS, CHEST, CORE (Placed on the left, clear of character!) -->
      <div class="absolute left-2 inset-y-6 w-20 sm:w-26 flex flex-col justify-around z-20 pointer-events-auto">
        <button
          v-for="m in leftMuscles"
          :key="m.muscle_group"
          type="button"
          @pointerdown.stop
          @click.stop="selectMuscle(m.muscle_group)"
          class="group flex items-center gap-1 sm:gap-1.5 p-1 sm:p-1.5 rounded-xl border transition-all duration-150 active:scale-95 text-left shadow-2xs backdrop-blur-xs select-none cursor-pointer"
          :class="[
            selectedMuscleGroup === m.muscle_group
              ? 'bg-slate-900 text-white border-slate-900 shadow-sm ring-2 ring-slate-900/20 scale-105'
              : getSideCardClass(m.status)
          ]"
        >
          <span
            class="w-1.5 h-1.5 rounded-full flex-shrink-0"
            :class="selectedMuscleGroup === m.muscle_group ? 'bg-emerald-400 animate-pulse' : getDotClass(m.status)"
          ></span>
          <div class="flex flex-col min-w-0">
            <div class="flex items-center justify-between gap-1">
              <span
                class="text-[10px] sm:text-[11px] font-black tracking-tight whitespace-nowrap"
                :class="selectedMuscleGroup === m.muscle_group ? 'text-white' : 'text-slate-800'"
              >
                {{ m.shortLabel }}
              </span>
              <span
                class="text-[9px] font-black whitespace-nowrap px-1 py-0.2 rounded"
                :class="selectedMuscleGroup === m.muscle_group ? 'bg-white/20 text-emerald-300' : getPctBadgeClass(m.status)"
              >
                {{ m.recovery_percentage }}%
              </span>
            </div>
            <span
              class="text-[8px] sm:text-[9px] font-medium truncate"
              :class="selectedMuscleGroup === m.muscle_group ? 'text-slate-300' : 'text-slate-500'"
            >
              {{ getSideCardStatusHint(m) }}
            </span>
          </div>
        </button>
      </div>

      <!-- Right Column Cards: BACK, ARMS, LEGS (Placed on the right, clear of character!) -->
      <div class="absolute right-2 inset-y-6 w-20 sm:w-26 flex flex-col justify-around z-20 pointer-events-auto">
        <button
          v-for="m in rightMuscles"
          :key="m.muscle_group"
          type="button"
          @pointerdown.stop
          @click.stop="selectMuscle(m.muscle_group)"
          class="group flex items-center gap-1 sm:gap-1.5 p-1 sm:p-1.5 rounded-xl border transition-all duration-150 active:scale-95 text-left shadow-2xs backdrop-blur-xs select-none cursor-pointer"
          :class="[
            selectedMuscleGroup === m.muscle_group
              ? 'bg-slate-900 text-white border-slate-900 shadow-sm ring-2 ring-slate-900/20 scale-105'
              : getSideCardClass(m.status)
          ]"
        >
          <span
            class="w-1.5 h-1.5 rounded-full flex-shrink-0"
            :class="selectedMuscleGroup === m.muscle_group ? 'bg-emerald-400 animate-pulse' : getDotClass(m.status)"
          ></span>
          <div class="flex flex-col min-w-0">
            <div class="flex items-center justify-between gap-1">
              <span
                class="text-[10px] sm:text-[11px] font-black tracking-tight whitespace-nowrap"
                :class="selectedMuscleGroup === m.muscle_group ? 'text-white' : 'text-slate-800'"
              >
                {{ m.shortLabel }}
              </span>
              <span
                class="text-[9px] font-black whitespace-nowrap px-1 py-0.2 rounded"
                :class="selectedMuscleGroup === m.muscle_group ? 'bg-white/20 text-emerald-300' : getPctBadgeClass(m.status)"
              >
                {{ m.recovery_percentage }}%
              </span>
            </div>
            <span
              class="text-[8px] sm:text-[9px] font-medium truncate"
              :class="selectedMuscleGroup === m.muscle_group ? 'text-slate-300' : 'text-slate-500'"
            >
              {{ getSideCardStatusHint(m) }}
            </span>
          </div>
        </button>
      </div>

      <!-- Bottom Drag Hint -->
      <div class="absolute bottom-1.5 left-1/2 -translate-x-1/2 pointer-events-none bg-slate-900/75 backdrop-blur-xs px-3 py-0.5 rounded-full text-[10px] text-white font-medium whitespace-nowrap shadow-xs z-20">
        👆 點擊人物可即時互動打氣 · ↔️ 拖曳可 360° 旋轉
      </div>
    </div>

    <!-- Bottom Interactive Muscle Selector Bar & Selected Muscle Detail HUD -->
    <div class="p-3 bg-slate-50 border-t border-slate-200/80 space-y-2.5">
      <div class="flex items-center gap-1.5 overflow-x-auto pb-0.5 no-scrollbar">
        <button
          v-for="m in normalizedMuscles"
          :key="m.muscle_group"
          type="button"
          @click="selectMuscle(m.muscle_group)"
          class="px-2.5 py-1 rounded-xl text-[10px] font-extrabold whitespace-nowrap transition-all flex items-center gap-1 border"
          :class="selectedMuscleGroup === m.muscle_group
            ? 'bg-slate-900 text-white border-slate-900 shadow-xs scale-105'
            : getBottomPillClass(m.status)"
        >
          <span class="w-1.5 h-1.5 rounded-full" :class="getDotClass(m.status)"></span>
          <span>{{ m.shortLabel }}</span>
          <span class="opacity-80">{{ m.recovery_percentage }}%</span>
        </button>
      </div>

      <div
        v-if="activeMuscleDetail"
        class="p-2.5 rounded-xl border transition-all flex items-center justify-between gap-2"
        :class="getDetailHudClass(activeMuscleDetail.status)"
      >
        <div class="space-y-0.5 min-w-0 flex-1">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-xs font-black text-slate-900 whitespace-nowrap">{{ activeMuscleDetail.label_zh }}</span>
            <span
              class="text-[10px] font-black px-2 py-0.5 rounded-full whitespace-nowrap shrink-0"
              :class="getHudBadgeClass(activeMuscleDetail.status)"
            >
              {{ getHotspotStatusLabel(activeMuscleDetail.status) }} · {{ activeMuscleDetail.recovery_percentage }}%
            </span>
          </div>
          <div class="text-[11px] text-slate-600 flex items-center gap-x-2 gap-y-0.5 flex-wrap">
            <span v-if="activeMuscleDetail.hours_since_last_trained !== null" class="whitespace-nowrap">
              🕒 上次訓練：{{ activeMuscleDetail.hours_since_last_trained }}h 前
            </span>
            <span v-else class="whitespace-nowrap">🕒 近期尚未訓練此部位</span>

            <span
              v-if="activeMuscleDetail.hours_until_recovered > 0"
              class="text-rose-600 font-bold whitespace-nowrap"
            >
              ⏳ 建議再休 {{ activeMuscleDetail.hours_until_recovered }}h
            </span>
            <span v-else class="text-emerald-700 font-bold whitespace-nowrap">
              ✅ 已達超補償巔峰，可安排訓練
            </span>
          </div>
        </div>

        <button
          v-if="canRecommendSplit(activeMuscleDetail.muscle_group)"
          type="button"
          @click="$emit('recommend-split', activeMuscleDetail.muscle_group)"
          class="px-3 py-2 rounded-xl text-[11px] font-black whitespace-nowrap shrink-0 transition-all active:scale-95 shadow-sm"
          :class="activeMuscleDetail.status === 'FATIGUED'
            ? 'bg-rose-100 hover:bg-rose-200 text-rose-800 border border-rose-300'
            : 'bg-emerald-600 hover:bg-emerald-700 text-white'"
        >
          {{ activeMuscleDetail.status === 'FATIGUED' ? '輕量恢復排課' : '排練此部位' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { triggerVibration } from '@/utils/notifications'

const props = defineProps({
  muscles: {
    type: Array,
    default: () => []
  },
  activeWorkoutMuscles: {
    type: Array,
    default: () => []
  },
  suggestedAura: {
    type: String,
    default: null
  },
  streakDays: {
    type: Number,
    default: 0
  }
})

defineEmits(['recommend-split'])

const authStore = useAuthStore()

// Gender is automatically derived from the user's profile settings (no manual toggle needed)
const isFemale = computed(() => {
  return authStore.profile?.gender === 'FEMALE'
})
const gender = computed(() => (isFemale.value ? 'FEMALE' : 'MALE'))

// 7 Cute 3D Clay Workout Animations
const workoutActions = [
  { key: 'STAND', id: 5, icon: '🧍', label: '直立站姿' },
  { key: 'RUN', id: 1, icon: '🏃', label: '活力慢跑' },
  { key: 'HURDLE', id: 0, icon: '👟', label: '飛躍跨欄' },
  { key: 'CURL', id: 2, icon: '💪', label: '啞鈴彎舉' },
  { key: 'SQUAT', id: 3, icon: '🏋️', label: '深蹲訓練' },
  { key: 'PRESS', id: 4, icon: '🙌', label: '活力肩推' },
  { key: 'SLOTH', id: 6, icon: '💤', label: '瞌睡偷懶' }
]
const currentAction = ref('STAND')
const showHotspotGlow = ref(true)

// Feature 6: Super Saiyan Energy Aura & Evolution Modes
const AURA_MODES = [
  { key: 'LV2', level: 2.0, icon: '🔥', label: '超級賽亞人', desc: '金黃烈焰氣場與爆裂衝擊光波', badge: '🔥 連勝中 · 超級賽亞人爆氣' },
  { key: 'LV3', level: 3.0, icon: '⚡', label: '極意神境', desc: '紫金極致神域氣場', badge: '⚡ 狂暴紫金極意神境' },
  { key: 'LV1', level: 1.0, icon: '✨', label: '晨曦微光', desc: '金色能量微粒', badge: '✨ 初醒金色微光' },
  { key: 'OFF', level: 0.0, icon: '⚪', label: '純淨模式', desc: '清爽無光環', badge: '⚪ 純淨無光環' },
  { key: 'SLOTH', level: -1.0, icon: '💤', label: '瞌睡偷懶', desc: '好幾天沒動的慵懶模式', badge: '💤 偷懶中 · 光環熄滅' }
]
const currentAuraIndex = ref(4) // Defaults to SLOTH until backend suggestedAura arrives
const currentAura = computed(() => AURA_MODES[currentAuraIndex.value])

const currentAuraBadgeText = computed(() => {
  const m = currentAura.value
  const streak = props.streakDays || 0
  if (m.key === 'LV3') return `⚡ ${streak > 0 ? streak + '天 · ' : ''}極意神境`
  if (m.key === 'LV2') return `🔥 ${streak > 0 ? streak + '天 · ' : ''}超級賽亞人`
  if (m.key === 'LV1') return `✨ ${streak > 0 ? streak + '天 · ' : ''}晨曦微光`
  if (m.key === 'SLOTH') return '💤 偷懶瞌睡模式'
  return '⚪ 純淨無光環'
})

function applySuggestedAura(key) {
  let targetKey = key
  if (!targetKey) {
    const hasAnyTrained = props.muscles?.some(m => m.hours_since_last_trained !== null && m.hours_since_last_trained !== undefined)
    targetKey = hasAnyTrained ? 'LV1' : 'SLOTH'
  }
  const idx = AURA_MODES.findIndex(m => m.key === targetKey)
  if (idx !== -1) {
    currentAuraIndex.value = idx
    if (targetKey === 'SLOTH') {
      currentAction.value = 'SLOTH'
    } else if (currentAction.value === 'SLOTH') {
      currentAction.value = 'STAND'
    }
  }
}

watch(
  () => [props.suggestedAura, props.muscles],
  () => {
    applySuggestedAura(props.suggestedAura)
  },
  { immediate: true }
)

function cycleAura() {
  currentAuraIndex.value = (currentAuraIndex.value + 1) % AURA_MODES.length
  const mode = AURA_MODES[currentAuraIndex.value]
  if (mode.key === 'SLOTH') {
    currentAction.value = 'SLOTH'
    reactionMessage.value = '好幾天沒運動了... 體能光環熄滅啦！快帶我去鍛鍊～🥺'
    reactionEmoji.value = '💤'
    showReactionBubble.value = true
    triggerVibration([30, 40, 30])
  } else {
    if (currentAction.value === 'SLOTH') currentAction.value = 'STAND'
    if (mode.key === 'LV2') {
      reactionMessage.value = '喝啊啊！超級賽亞人模式全開！金色衝擊波爆裂！💥'
      reactionEmoji.value = '🔥'
    } else {
      reactionMessage.value = `光環切換：${mode.label}！能量充沛，隨時開練！`
      reactionEmoji.value = mode.icon
    }
    showReactionBubble.value = true
    triggerVibration([20, 30, 20])
  }
}

function getAuraBadgeClass(key) {
  if (key === 'LV2') return 'bg-gradient-to-r from-amber-500 via-yellow-400 to-amber-600 text-slate-950 font-black border-yellow-300 ring-2 ring-yellow-400/50 shadow-xs'
  if (key === 'LV3') return 'bg-gradient-to-r from-purple-600 via-pink-500 to-amber-400 text-white border-purple-300 ring-2 ring-purple-400/30 shadow-xs'
  if (key === 'LV1') return 'bg-amber-100 text-amber-900 border-amber-300'
  if (key === 'SLOTH') return 'bg-indigo-100 text-indigo-900 border-indigo-300'
  return 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
}

// Interactive Character Click Reaction States
const reactionMessage = ref('')
const reactionEmoji = ref('💪')
const showReactionBubble = ref(false)
const clickBounceTime = ref(-999)
let reactionTimer = null

const BOY_QUOTES = [
  { text: '衝啊！每一組訓練都在突破極限！', emoji: '🔥' },
  { text: '肌肉線條越來越雕刻了，保持專注！', emoji: '💪' },
  { text: '背打直、核心收緊，穩定輸出！', emoji: '🏋️' },
  { text: '休息也是超補償的重要一環，吃夠蛋白質！', emoji: '🍗' },
  { text: '熱血不滅，今天的汗水是明天強大的養分！', emoji: '⚡' }
]

const GIRL_QUOTES = [
  { text: '活力滿滿！今天的運動狀態太棒了～', emoji: '✨' },
  { text: '核心收緊，體態線條越來越漂亮！', emoji: '💃' },
  { text: '堅持下去，妳比想像中更強大！', emoji: '💖' },
  { text: '步伐輕盈，保持呼吸節奏向前衝！', emoji: '🏃‍♀️' },
  { text: '練完記得充分拉伸與補水唷！', emoji: '🥤' }
]

const MUSCLE_QUOTES = {
  CHEST: { text: '胸肌發力感受度超棒，頂峰收縮！', emoji: '💥' },
  BACK: { text: '背闊肌展開，厚度與線條全都要！', emoji: '🦅' },
  SHOULDERS: { text: '南瓜肩打造中，推舉動作超標準！', emoji: '🎃' },
  ARMS: { text: '手臂充血膨脹，二三頭肌力爆棚！', emoji: '💪' },
  CORE: { text: '腹部核心如鋼鐵般緊繃穩固！', emoji: '🛡️' },
  LEGS: { text: '深蹲無所畏懼，強大下盤是一切基礎！', emoji: '🦵' }
}

function triggerCharacterReaction(clickedMuscle = null) {
  triggerVibration([25, 35, 25])
  clickBounceTime.value = performance.now() * 0.001

  if (clickedMuscle) {
    const m = normalizedMuscles.value.find(item => item.muscle_group === clickedMuscle)
    if (m && m.status === 'FATIGUED') {
      reactionMessage.value = `${m.shortLabel}部位剛苦練完，正在超補償修復中！`
      reactionEmoji.value = '💆'
    } else if (MUSCLE_QUOTES[clickedMuscle]) {
      reactionMessage.value = MUSCLE_QUOTES[clickedMuscle].text
      reactionEmoji.value = MUSCLE_QUOTES[clickedMuscle].emoji
    }
  } else {
    const pool = isFemale.value ? GIRL_QUOTES : BOY_QUOTES
    const pick = pool[Math.floor(Math.random() * pool.length)]
    reactionMessage.value = pick.text
    reactionEmoji.value = pick.emoji
  }

  showReactionBubble.value = true
  if (reactionTimer) clearTimeout(reactionTimer)
  reactionTimer = setTimeout(() => {
    showReactionBubble.value = false
  }, 2600)
}

// 360° Camera Yaw (Default -0.55 rad = 3/4 side-front angle matching the reference images!)
const yaw = ref(-0.55)
const targetYaw = ref(null)
const autoRotate = ref(true)
const userDisabledAutoRotate = ref(false)
const isDragging = ref(false)
const lastPointerX = ref(0)
const dragMoved = ref(false)

function toggleAutoRotate() {
  autoRotate.value = !autoRotate.value
  userDisabledAutoRotate.value = !autoRotate.value
}

const selectedMuscleGroup = ref('LEGS')
const glCanvasRef = ref(null)
const projectedMusclePins = ref([])
let animFrameId = null
let gl = null
let program = null
let uniforms = {}

const MUSCLE_INDEX = {
  CHEST: 1,
  BACK: 2,
  SHOULDERS: 3,
  ARMS: 4,
  CORE: 5,
  LEGS: 6
}

const DEFAULT_MUSCLES = [
  { muscle_group: 'CHEST', label_zh: '胸大肌 (Chest)', recovery_percentage: 100, status: 'RECOVERED', hours_since_last_trained: null, hours_until_recovered: 0, target_recovery_hours: 48 },
  { muscle_group: 'BACK', label_zh: '背部肌群 (Back)', recovery_percentage: 100, status: 'RECOVERED', hours_since_last_trained: null, hours_until_recovered: 0, target_recovery_hours: 48 },
  { muscle_group: 'LEGS', label_zh: '腿部與臀部 (Legs)', recovery_percentage: 100, status: 'RECOVERED', hours_since_last_trained: null, hours_until_recovered: 0, target_recovery_hours: 72 },
  { muscle_group: 'SHOULDERS', label_zh: '肩部三角肌 (Shoulders)', recovery_percentage: 100, status: 'RECOVERED', hours_since_last_trained: null, hours_until_recovered: 0, target_recovery_hours: 36 },
  { muscle_group: 'ARMS', label_zh: '手臂二三頭肌 (Arms)', recovery_percentage: 100, status: 'RECOVERED', hours_since_last_trained: null, hours_until_recovered: 0, target_recovery_hours: 36 },
  { muscle_group: 'CORE', label_zh: '核心與腹肌 (Core)', recovery_percentage: 100, status: 'RECOVERED', hours_since_last_trained: null, hours_until_recovered: 0, target_recovery_hours: 24 }
]

const SHORT_LABELS = {
  CHEST: '胸肌',
  BACK: '背肌',
  LEGS: '臀腿',
  SHOULDERS: '肩部',
  ARMS: '手臂',
  CORE: '核心'
}

const normalizedMuscles = computed(() => {
  const source = props.muscles?.length ? props.muscles : DEFAULT_MUSCLES
  return source.map(m => {
    const isActivelyTraining = props.activeWorkoutMuscles.includes(m.muscle_group)
    return {
      ...m,
      shortLabel: SHORT_LABELS[m.muscle_group] || m.label_zh?.split(' ')[0] || m.muscle_group,
      status: isActivelyTraining ? 'FATIGUED' : m.status,
      recovery_percentage: isActivelyTraining ? Math.min(m.recovery_percentage, 20) : m.recovery_percentage
    }
  })
})

watch(
  normalizedMuscles,
  (list) => {
    if (!list.length) return
    const lowest = [...list].sort((a, b) => a.recovery_percentage - b.recovery_percentage)[0]
    if (lowest && lowest.recovery_percentage < 85) {
      selectedMuscleGroup.value = lowest.muscle_group
    }
  },
  { immediate: true }
)

const activeMuscleDetail = computed(() => {
  return normalizedMuscles.value.find(m => m.muscle_group === selectedMuscleGroup.value) || normalizedMuscles.value[0]
})

function canRecommendSplit(muscleGroup) {
  return ['CHEST', 'BACK', 'SHOULDERS', 'LEGS'].includes(muscleGroup)
}

const stageSize = ref({ w: 400, h: 330 })

const LEFT_KEYS = ['SHOULDERS', 'CHEST', 'CORE']
const RIGHT_KEYS = ['BACK', 'ARMS', 'LEGS']

const leftMuscles = computed(() => {
  return LEFT_KEYS.map(k => normalizedMuscles.value.find(m => m.muscle_group === k)).filter(Boolean)
})

const rightMuscles = computed(() => {
  return RIGHT_KEYS.map(k => normalizedMuscles.value.find(m => m.muscle_group === k)).filter(Boolean)
})

function getStatusColor(status) {
  if (status === 'FATIGUED') return '#f43f5e'
  if (status === 'RECOVERING') return '#f59e0b'
  return '#10b981'
}

const leaderLines = computed(() => {
  const sw = stageSize.value.w || 400
  const sh = stageSize.value.h || 330
  const leftCardX = Math.min(Math.max(sw * 0.22, 76), 104)
  const rightCardX = sw - Math.min(Math.max(sw * 0.22, 76), 104)
  const usableH = Math.max(sh - 48, 180)

  const leftSlots = { SHOULDERS: 0, CHEST: 1, CORE: 2 }
  const rightSlots = { BACK: 0, ARMS: 1, LEGS: 2 }

  const lines = []
  normalizedMuscles.value.forEach(m => {
    const isLeft = m.muscle_group in leftSlots
    const slot = isLeft ? leftSlots[m.muscle_group] : rightSlots[m.muscle_group]
    if (slot === undefined) return

    const cardY = 24 + usableH * ((slot * 2 + 1) / 6)
    const cardX = isLeft ? leftCardX : rightCardX

    const pin = projectedMusclePins.value.find(p => p.muscle_group === m.muscle_group)
    const bodyX = pin ? (pin.xPct / 100) * sw : sw * 0.5
    const bodyY = pin ? (pin.yPct / 100) * sh : cardY
    const visible = pin ? pin.visible : true
    const isSelected = selectedMuscleGroup.value === m.muscle_group

    const midX = cardX + (bodyX - cardX) * 0.45
    const path = `M ${cardX.toFixed(1)} ${cardY.toFixed(1)} C ${midX.toFixed(1)} ${cardY.toFixed(1)}, ${midX.toFixed(1)} ${bodyY.toFixed(1)}, ${bodyX.toFixed(1)} ${bodyY.toFixed(1)}`

    lines.push({
      key: m.muscle_group,
      muscle_group: m.muscle_group,
      cardX,
      cardY,
      bodyX,
      bodyY,
      path,
      stroke: getStatusColor(m.status),
      status: m.status,
      visible,
      isSelected
    })
  })
  return lines
})

function rotateToAngle(angleRad) {
  autoRotate.value = false
  targetYaw.value = angleRad
}

function selectMuscle(muscleGroup) {
  selectedMuscleGroup.value = muscleGroup
  // When in standing posture, keep the standing posture so user can inspect any muscle 360°
  if (currentAction.value === 'STAND') {
    if (!autoRotate.value) {
      if (muscleGroup === 'BACK' && Math.cos(yaw.value) > -0.2) {
        rotateToAngle(Math.PI - 0.45)
      } else if (['CHEST', 'CORE'].includes(muscleGroup) && Math.cos(yaw.value) < 0.2) {
        rotateToAngle(-0.45)
      }
    }
    return
  }
  if (muscleGroup === 'ARMS') {
    currentAction.value = 'CURL'
  } else if (muscleGroup === 'LEGS') {
    currentAction.value = 'SQUAT'
  } else if (muscleGroup === 'SHOULDERS') {
    currentAction.value = 'PRESS'
  } else if (muscleGroup === 'CORE') {
    currentAction.value = 'HURDLE'
  } else if (muscleGroup === 'BACK') {
    currentAction.value = 'PRESS'
    if (!autoRotate.value && Math.cos(yaw.value) > -0.2) {
      rotateToAngle(Math.PI - 0.45)
    }
  } else if (muscleGroup === 'CHEST') {
    currentAction.value = 'RUN'
    if (!autoRotate.value && Math.cos(yaw.value) < 0.2) {
      rotateToAngle(-0.45)
    }
  }
}

function onPointerDown(e) {
  isDragging.value = true
  dragMoved.value = false
  // Retain autoRotate state: during drag isDragging is true so yaw doesn't auto-increment.
  targetYaw.value = null
  lastPointerX.value = e.clientX
}

function onPointerMove(e) {
  if (!isDragging.value) return
  const dx = e.clientX - lastPointerX.value
  if (Math.abs(dx) > 3) dragMoved.value = true
  yaw.value -= dx * 0.014
  lastPointerX.value = e.clientX
}

function onPointerUp(e) {
  if (!isDragging.value) return
  isDragging.value = false
  // Automatically resume rotating unless user explicitly toggled it off via the button!
  if (!userDisabledAutoRotate.value) {
    autoRotate.value = true
  }
  if (!dragMoved.value && glCanvasRef.value) {
    const rect = glCanvasRef.value.getBoundingClientRect()
    const xPct = ((e.clientX - rect.left) / rect.width) * 100
    const yPct = ((e.clientY - rect.top) / rect.height) * 100
    let bestPin = null
    let bestDist = 22
    for (const pin of projectedMusclePins.value) {
      if (!pin.visible) continue
      const d = Math.hypot(xPct - pin.xPct, yPct - pin.yPct)
      if (d < bestDist) {
        bestDist = d
        bestPin = pin
      }
    }
    if (bestPin) {
      selectMuscle(bestPin.muscle_group)
      triggerCharacterReaction(bestPin.muscle_group)
    } else if (xPct >= 18 && xPct <= 82 && yPct >= 8 && yPct <= 92) {
      triggerCharacterReaction(null)
    }
  }
}

// ============================================================================
// REAL-TIME WEBGL SDF RAYMARCHING 3D SOFT-CLAY SHADER ENGINE
// Uses Smooth Minimum (smin) Metaball Clay Modeling + Subsurface Scattering
// + Studio Ambient Occlusion + Soft Penumbra Shadows (Blender Cycles Clay Look)
// ============================================================================
const VERTEX_SHADER_SRC = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = aPosition;
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`

const FRAGMENT_SHADER_SRC = `
precision highp float;
varying vec2 vUv;

uniform vec2 uResolution;
uniform float uTime;
uniform float uYaw;
uniform float uGender;      // 0.0 = Boy, 1.0 = Girl
uniform int uAction;        // 0 = HURDLE, 1 = RUN, 2 = CURL, 3 = SQUAT, 4 = PRESS, 5 = STAND
uniform float uShowGlow;
uniform int uSelectedMuscle;
uniform vec3 uMuscleStatus123; // x=CHEST(1), y=BACK(2), z=SHOULDERS(3)
uniform vec3 uMuscleStatus456; // x=ARMS(4), y=CORE(5), z=LEGS(6)
uniform vec3 uHeadCenter;
uniform float uClickTime;
uniform float uAuraLevel;

// Smooth Minimum (Polynomial smin for seamless Blender 3D Clay blending!)
float smin(float a, float b, float k) {
  float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
  return mix(b, a, h) - k * h * (1.0 - h);
}

// Smooth Maximum (for soft clay carving / dimples)
float smax(float a, float b, float k) {
  return -smin(-a, -b, k);
}

// Signed Distance to a 3D Capsule between point a and point b
float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
  vec3 pa = p - a, ba = b - a;
  float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
  return length(pa - ba * h) - r;
}

// Signed Distance to a 3D Tapered Capsule (Round Cone) between a (radius r1) and b (radius r2)
float sdRoundCone(vec3 p, vec3 a, vec3 b, float r1, float r2) {
  vec3 ba = b - a;
  float l2 = dot(ba, ba);
  float rr = r1 - r2;
  float a2 = l2 - rr * rr;
  float il2 = 1.0 / l2;

  vec3 pa = p - a;
  float y = dot(pa, ba);
  float z = y - l2;
  vec3 x2p = pa * l2 - ba * y;
  float x2 = dot(x2p, x2p);
  float y2 = y * y * l2;
  float z2 = z * z * l2;

  float k = sign(rr) * rr * rr * x2;
  if (sign(z) * a2 * z2 > k) return sqrt(x2 + z2) * il2 - r2;
  if (sign(y) * a2 * y2 < k) return sqrt(x2 + y2) * il2 - r1;
  return (sqrt(x2 * a2 * il2) + y * rr) * il2 - r1;
}

// Signed Distance to an Ellipsoid
float sdEllipsoid(vec3 p, vec3 r) {
  float k0 = length(p / r);
  float k1 = length(p / (r * r));
  return k0 * (k0 - 1.0) / k1;
}

// Signed Distance to a Rounded Box
float sdRoundBox(vec3 p, vec3 b, float r) {
  vec3 q = abs(p) - b;
  return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

// Material IDs:
// 1.0 = Skin (Soft warm peach clay)
// 2.0 = Hair (Dark Charcoal for Boy, Warm Chocolate Brown for Girl)
// 3.0 = Eyes / Brows / Smile
// 4.0 = Top (Boy Orange T-Shirt / Girl Lavender Tank)
// 5.0 = Shorts (Boy Royal Blue Shorts / Girl Coral-Orange Shorts)
// 6.0 = White Clay (Waistband Drawstrings / Wristbands / Socks / Shoe Soles / Hurdle Top)
// 7.0 = Shoe Colored Upper
// 8.0 = Dark Grey Prop (Hurdle Frame / Dumbbells)

struct HitInfo {
  float d;
  float mat;
  int muscle;
};

HitInfo opU(HitInfo a, HitInfo b) {
  if (a.d < b.d) return a;
  return b;
}

HitInfo opSmoothSkin(HitInfo a, HitInfo b, float k) {
  float d = smin(a.d, b.d, k);
  float mat = (a.d < b.d) ? a.mat : b.mat;
  int mus = (a.d < b.d) ? a.muscle : b.muscle;
  return HitInfo(d, mat, mus);
}

// Evaluate complete 3D Clay Character Scene (Slender 6-Head Proportions & High-Detail Sculpt)
HitInfo mapScene(vec3 p) {
  // Animation kinematics
  float t = uTime * 3.2;
  float bounceY = 0.0;
  float leanZ = 0.0;

  // Interactive Click Elastic Spring Bounce
  if (uClickTime < 1.4) {
    float ct = uClickTime;
    float spring = exp(-ct * 4.2) * sin(ct * 16.0) * 0.065;
    bounceY += spring;
  }

  // Slender, long-limbed athletic proportions matching Reference Images 1 & 2
  vec3 lHip = vec3(-0.095, -0.05, 0.0);
  vec3 rHip = vec3( 0.095, -0.05, 0.0);
  vec3 lKnee = vec3(-0.10, -0.43, 0.02);
  vec3 rKnee = vec3( 0.10, -0.43, 0.02);
  vec3 lAnkle = vec3(-0.105, -0.77, 0.0);
  vec3 rAnkle = vec3( 0.105, -0.77, 0.0);

  vec3 lShoulder = vec3(-0.165, 0.34, 0.0);
  vec3 rShoulder = vec3( 0.165, 0.34, 0.0);
  vec3 lElbow = vec3(-0.23, 0.14, -0.02);
  vec3 rElbow = vec3( 0.23, 0.14, -0.02);
  vec3 lWrist = vec3(-0.24, -0.05, 0.12);
  vec3 rWrist = vec3( 0.24, -0.05, 0.12);

  bool showHurdle = false;
  bool showDumbbells = false;

  if (uAction == 5) {
    // ACTION 5: NATURAL STANDING STRAIGHT (直立站姿 - 修長體態 360° 檢視)
    float breath = sin(t * 0.8) * 0.010;
    bounceY += breath;
    leanZ = 0.0;

    lHip = vec3(-0.095, -0.05 + bounceY, 0.0);
    rHip = vec3( 0.095, -0.05 + bounceY, 0.0);

    lKnee = vec3(-0.098, -0.43 + bounceY, 0.01);
    rKnee = vec3( 0.098, -0.43 + bounceY, 0.01);
    lAnkle = vec3(-0.10, -0.77, 0.0);
    rAnkle = vec3( 0.10, -0.77, 0.0);

    lShoulder = vec3(-0.165, 0.34 + bounceY, 0.0);
    rShoulder = vec3( 0.165, 0.34 + bounceY, 0.0);

    lElbow = vec3(-0.215, 0.11 + bounceY, 0.01);
    rElbow = vec3( 0.215, 0.11 + bounceY, 0.01);
    lWrist = vec3(-0.205, -0.12 + bounceY + breath * 0.5, 0.04);
    rWrist = vec3( 0.205, -0.12 + bounceY + breath * 0.5, 0.04);
  } else if (uAction == 0) {
    // ACTION 0: HURDLE JUMP
    showHurdle = true;
    float jw = 0.5 + 0.5 * sin(t * 0.9);
    bounceY += 0.14 + jw * 0.09;
    leanZ = 0.07;

    rHip = vec3(0.095, -0.05 + bounceY, 0.03);
    rKnee = vec3(0.10, -0.02 + bounceY, 0.30);
    rAnkle = vec3(0.10, -0.16 + bounceY, 0.58);

    lHip = vec3(-0.095, -0.05 + bounceY, -0.03);
    lKnee = vec3(-0.10, -0.38 + bounceY, -0.14);
    lAnkle = vec3(-0.10, -0.34 + bounceY, -0.44);

    lShoulder = vec3(-0.165, 0.34 + bounceY, leanZ);
    rShoulder = vec3( 0.165, 0.34 + bounceY, leanZ);
    lElbow = vec3(-0.23, 0.22 + bounceY, 0.22);
    lWrist = vec3(-0.16, 0.32 + bounceY, 0.40);
    rElbow = vec3( 0.25, 0.26 + bounceY, -0.18);
    rWrist = vec3( 0.30, 0.08 + bounceY, -0.24);
  } else if (uAction == 1) {
    // ACTION 1: ENERGETIC RUN (Exact dynamic stride from uploaded Reference Image 1!)
    float s = sin(t * 1.35);
    bounceY += abs(cos(t * 1.35)) * 0.055;
    leanZ = 0.045;

    lHip = vec3(-0.095, -0.05 + bounceY, 0.0);
    rHip = vec3( 0.095, -0.05 + bounceY, 0.0);

    lKnee = vec3(-0.10, -0.37 + bounceY + max(0.0, s) * 0.13, s * 0.25 + 0.04);
    lAnkle = vec3(-0.10, -0.73 + bounceY + max(0.0, -s) * 0.18, s * 0.38 - 0.06);

    rKnee = vec3( 0.10, -0.37 + bounceY + max(0.0, -s) * 0.13, -s * 0.25 + 0.04);
    rAnkle = vec3( 0.10, -0.73 + bounceY + max(0.0, s) * 0.18, -s * 0.38 - 0.06);

    lShoulder = vec3(-0.165, 0.34 + bounceY, leanZ);
    rShoulder = vec3( 0.165, 0.34 + bounceY, leanZ);
    lElbow = vec3(-0.23, 0.15 + bounceY, -s * 0.18);
    lWrist = vec3(-0.19, 0.21 + bounceY + max(0.0, -s) * 0.10, -s * 0.26 + 0.15);

    rElbow = vec3( 0.23, 0.15 + bounceY, s * 0.18);
    rWrist = vec3( 0.19, 0.21 + bounceY + max(0.0, s) * 0.10, s * 0.26 + 0.15);
  } else if (uAction == 2) {
    // ACTION 2: DUMBBELL BICEP CURL
    showDumbbells = true;
    float cw = 0.5 + 0.5 * sin(t * 1.3);
    bounceY += sin(t * 1.3) * 0.012;
    lShoulder = vec3(-0.165, 0.34 + bounceY, 0.0);
    rShoulder = vec3( 0.165, 0.34 + bounceY, 0.0);
    lElbow = vec3(-0.22, 0.13 + bounceY, 0.03);
    rElbow = vec3( 0.22, 0.13 + bounceY, 0.03);
    lWrist = vec3(-0.22, -0.03 + cw * 0.26 + bounceY, 0.13 + sin(cw * 3.1415) * 0.13);
    rWrist = vec3( 0.22, -0.03 + cw * 0.26 + bounceY, 0.13 + sin(cw * 3.1415) * 0.13);
  } else if (uAction == 3) {
    // ACTION 3: SQUAT
    float sq = 0.5 + 0.5 * sin(t * 1.1);
    bounceY += -sq * 0.22;
    leanZ = sq * 0.07;
    lHip = vec3(-0.105, -0.05 + bounceY, -sq * 0.13);
    rHip = vec3( 0.105, -0.05 + bounceY, -sq * 0.13);
    lKnee = vec3(-0.12, -0.43 + bounceY * 0.35, 0.05 + sq * 0.17);
    rKnee = vec3( 0.12, -0.43 + bounceY * 0.35, 0.05 + sq * 0.17);
    lShoulder = vec3(-0.165, 0.34 + bounceY, leanZ);
    rShoulder = vec3( 0.165, 0.34 + bounceY, leanZ);
    lElbow = vec3(-0.19, 0.18 + bounceY, 0.13 + sq * 0.11);
    rElbow = vec3( 0.19, 0.18 + bounceY, 0.13 + sq * 0.11);
    lWrist = vec3(-0.10, 0.23 + bounceY, 0.28 + sq * 0.14);
    rWrist = vec3( 0.10, 0.23 + bounceY, 0.28 + sq * 0.14);
  } else if (uAction == 4) {
    // ACTION 4: OVERHEAD SHOULDER PRESS
    showDumbbells = true;
    float pw = 0.5 + 0.5 * sin(t * 1.2);
    bounceY += pw * 0.018;
    lShoulder = vec3(-0.165, 0.34 + bounceY, 0.0);
    rShoulder = vec3( 0.165, 0.34 + bounceY, 0.0);
    lElbow = vec3(-0.26 + pw * 0.04, 0.28 + pw * 0.20 + bounceY, 0.02);
    rElbow = vec3( 0.26 - pw * 0.04, 0.28 + pw * 0.20 + bounceY, 0.02);
    lWrist = vec3(-0.22 + pw * 0.05, 0.48 + pw * 0.25 + bounceY, 0.03);
    rWrist = vec3( 0.22 - pw * 0.05, 0.48 + pw * 0.25 + bounceY, 0.03);
  } else {
    // ACTION 6: SLOTH / SLEEPY POSTURE (瞌睡偷懶)
    float breath = sin(t * 0.5) * 0.012;
    bounceY += -0.16 + breath;
    leanZ = -0.05;
    lHip = vec3(-0.11, -0.05 + bounceY, -0.02);
    rHip = vec3( 0.11, -0.05 + bounceY, -0.02);
    lKnee = vec3(-0.16, -0.32 + bounceY, 0.16);
    rKnee = vec3( 0.16, -0.32 + bounceY, 0.16);
    lAnkle = vec3(-0.06, -0.56 + bounceY, 0.18);
    rAnkle = vec3( 0.06, -0.56 + bounceY, 0.18);
    lShoulder = vec3(-0.16, 0.30 + bounceY, leanZ);
    rShoulder = vec3( 0.16, 0.30 + bounceY, leanZ);
    lElbow = vec3(-0.18, 0.10 + bounceY, 0.10);
    rElbow = vec3( 0.18, 0.10 + bounceY, 0.10);
    lWrist = vec3(-0.06, 0.04 + bounceY, 0.16);
    rWrist = vec3( 0.06, 0.04 + bounceY, 0.16);
  }

  // Interactive flex gesture on tap/click
  if (uClickTime < 0.9) {
    float cheerBlend = smoothstep(0.0, 0.15, uClickTime) * smoothstep(0.9, 0.4, uClickTime);
    lElbow = mix(lElbow, vec3(-0.25, 0.20 + bounceY, 0.06), cheerBlend * 0.8);
    rElbow = mix(rElbow, vec3( 0.25, 0.20 + bounceY, 0.06), cheerBlend * 0.8);
    lWrist = mix(lWrist, vec3(-0.19, 0.34 + bounceY, 0.16), cheerBlend * 0.88);
    rWrist = mix(rWrist, vec3( 0.19, 0.34 + bounceY, 0.16), cheerBlend * 0.88);
  }

  vec3 pelvisCenter = (lHip + rHip) * 0.5 + vec3(0.0, 0.03, 0.0);
  vec3 chestCenter = vec3(0.0, 0.30 + bounceY, leanZ);
  vec3 neckTop = vec3(0.0, 0.44 + bounceY, leanZ + 0.005);
  vec3 headCenter = vec3(0.0, 0.575 + bounceY, leanZ + 0.015);

  // ========================================================================
  // 1. REFINED HEAD, SCULPTED JAWLINE, EARS, 3D NOSE & SLENDER NECK
  // ========================================================================
  vec3 hp = p - headCenter;
  // Sleek oval cranium + tapered lower jaw/cheeks (matches Reference Image 1!)
  float dCranium = sdEllipsoid(hp - vec3(0.0, 0.022, 0.0), vec3(0.132, 0.145, 0.134));
  float dJaw = sdEllipsoid(hp - vec3(0.0, -0.042, 0.014), vec3(0.116, 0.102, 0.116));
  float dHead = smin(dCranium, dJaw, 0.042);

  // Delicate 3D Sculpted Nose Bridge & Tip
  float dNose = sdRoundCone(
    hp,
    vec3(0.0, 0.004, 0.122),
    vec3(0.0, -0.016, 0.142),
    0.014,
    0.020
  );
  dHead = smin(dHead, dNose, 0.014);

  // Refined C-Shaped Ears with inner concha hollow
  vec3 earP = vec3(abs(hp.x) - 0.128, hp.y + 0.008, hp.z + 0.006);
  float dEar = sdEllipsoid(earP, vec3(0.030, 0.044, 0.025));
  float dEarHole = length(earP - vec3(0.006, 0.0, 0.016)) - 0.017;
  dEar = smax(dEar, -dEarHole, 0.009);
  dHead = smin(dHead, dEar, 0.012);

  // Slender Athletic Neck
  float dNeck = sdRoundCone(p, chestCenter + vec3(0.0, 0.05, 0.0), neckTop, 0.050, 0.044);
  float dSkinHeadNeck = smin(dHead, dNeck, 0.016);
  HitInfo res = HitInfo(dSkinHeadNeck, 1.0, 0);

  // ========================================================================
  // 2. SLENDER ARMS & ARTICULATED 5-FINGER HANDS (4 Fingers + Thumb!)
  // ========================================================================
  float dArmL = smin(
    sdRoundCone(p, lShoulder, lElbow, 0.048, 0.042),
    sdRoundCone(p, lElbow, lWrist, 0.041, 0.035),
    0.014
  );
  // Articulated Left Hand: Palm + 4 Curled Fingers + Thumb
  vec3 lHandDir = normalize(lWrist - lElbow);
  vec3 lPalmCenter = lWrist + lHandDir * 0.032;
  float dPalmL = sdEllipsoid(p - lPalmCenter, vec3(0.036, 0.042, 0.034));
  vec3 lp = p - lPalmCenter;
  float dFingersL = min(
    min(
      sdCapsule(lp, vec3(0.012,  0.022,  0.012), vec3(0.026,  0.022, -0.014), 0.0115),
      sdCapsule(lp, vec3(0.014,  0.007,  0.015), vec3(0.028,  0.007, -0.014), 0.012)
    ),
    min(
      sdCapsule(lp, vec3(0.014, -0.008,  0.014), vec3(0.028, -0.008, -0.014), 0.0115),
      sdCapsule(lp, vec3(0.011, -0.022,  0.011), vec3(0.024, -0.022, -0.012), 0.0105)
    )
  );
  float dThumbL = sdCapsule(lp, vec3(0.006, 0.018, 0.018), vec3(0.028, 0.034, 0.024), 0.013);
  float dHandL = smin(dPalmL, min(dFingersL, dThumbL), 0.008);
  dArmL = smin(dArmL, dHandL, 0.012);

  float dArmR = smin(
    sdRoundCone(p, rShoulder, rElbow, 0.048, 0.042),
    sdRoundCone(p, rElbow, rWrist, 0.041, 0.035),
    0.014
  );
  // Articulated Right Hand: Palm + 4 Curled Fingers + Thumb
  vec3 rHandDir = normalize(rWrist - rElbow);
  vec3 rPalmCenter = rWrist + rHandDir * 0.032;
  float dPalmR = sdEllipsoid(p - rPalmCenter, vec3(0.036, 0.042, 0.034));
  vec3 rp = p - rPalmCenter;
  float dFingersR = min(
    min(
      sdCapsule(rp, vec3(-0.012,  0.022,  0.012), vec3(-0.026,  0.022, -0.014), 0.0115),
      sdCapsule(rp, vec3(-0.014,  0.007,  0.015), vec3(-0.028,  0.007, -0.014), 0.012)
    ),
    min(
      sdCapsule(rp, vec3(-0.014, -0.008,  0.014), vec3(-0.028, -0.008, -0.014), 0.0115),
      sdCapsule(rp, vec3(-0.011, -0.022,  0.011), vec3(-0.024, -0.022, -0.012), 0.0105)
    )
  );
  float dThumbR = sdCapsule(rp, vec3(-0.006, 0.018, 0.018), vec3(-0.028, 0.034, 0.024), 0.013);
  float dHandR = smin(dPalmR, min(dFingersR, dThumbR), 0.008);
  dArmR = smin(dArmR, dHandR, 0.012);

  float dArms = min(dArmL, dArmR);
  float dShoulders = min(length(p - lShoulder) - 0.058, length(p - rShoulder) - 0.058);
  res = opSmoothSkin(res, HitInfo(dShoulders, 1.0, 3), 0.018);
  res = opSmoothSkin(res, HitInfo(dArms, 1.0, 4), 0.014);

  // ========================================================================
  // 3. SLENDER LEGS (Thigh -> Knee -> Calf -> Ankle)
  // ========================================================================
  float dLegL = smin(
    sdRoundCone(p, lHip, lKnee, 0.058, 0.048),
    sdRoundCone(p, lKnee, lAnkle, 0.047, 0.037),
    0.018
  );
  float dLegR = smin(
    sdRoundCone(p, rHip, rKnee, 0.058, 0.048),
    sdRoundCone(p, rKnee, rAnkle, 0.047, 0.037),
    0.018
  );
  res = opU(res, HitInfo(min(dLegL, dLegR), 1.0, 6));

  // ========================================================================
  // 4. TAILORED SPORTSWEAR: LAYERED T-SHIRT OVERHANG & CRISP SHORTS CUFFS
  // ========================================================================
  float shirtHemY = pelvisCenter.y + 0.045;

  // Torso Garment (Mat 4.0) with natural 3D overhang over shorts
  vec3 torsoBot = vec3(pelvisCenter.x, shirtHemY, pelvisCenter.z);
  vec3 torsoTop = chestCenter + vec3(0.0, 0.06, 0.0);
  // Elliptical cross-section torso (wider X than Z, just like a real T-shirt!)
  vec3 tp = p;
  tp.z *= 1.24;
  vec3 tbScaled = vec3(torsoBot.x, torsoBot.y, torsoBot.z * 1.24);
  vec3 ttScaled = vec3(torsoTop.x, torsoTop.y, torsoTop.z * 1.24);
  float dTorso = sdRoundCone(tp, tbScaled, ttScaled, 0.146, 0.152) / 1.12;

  // Clean flat shirt hem cut at shirtHemY
  dTorso = smax(dTorso, -(p.y - shirtHemY), 0.010);

  // Sculpted Crew-Neck Collar Rim
  vec3 collarP = p - (torsoTop + vec3(0.0, 0.012, 0.005));
  float dCollar = abs(length(collarP.xz) - 0.056) - 0.014;
  dCollar = max(dCollar, abs(collarP.y) - 0.014);
  dTorso = smin(dTorso, dCollar, 0.010);

  if (uGender < 0.5) {
    // Boy: Crisp Short Sleeves wider than the arm (creating real 3D sleeve cuff opening!)
    vec3 lSleeveEnd = mix(lShoulder, lElbow, 0.52);
    vec3 rSleeveEnd = mix(rShoulder, rElbow, 0.52);
    float dSleeveL = sdRoundCone(p, lShoulder, lSleeveEnd, 0.064, 0.066);
    float dSleeveR = sdRoundCone(p, rShoulder, rSleeveEnd, 0.064, 0.066);
    // Flat cuff cut at sleeve ends
    dSleeveL = smax(dSleeveL, dot(p - lSleeveEnd, normalize(lElbow - lShoulder)), 0.008);
    dSleeveR = smax(dSleeveR, dot(p - rSleeveEnd, normalize(rElbow - rShoulder)), 0.008);
    dTorso = smin(dTorso, min(dSleeveL, dSleeveR), 0.022);
  } else {
    // Girl: Fitted Athletic Tank Top
    float dBust = sdEllipsoid(p - (chestCenter + vec3(0.0, -0.01, 0.055)), vec3(0.128, 0.082, 0.075));
    dTorso = smin(dTorso, dBust, 0.025);
  }

  int torsoMuscle = (p.z < chestCenter.z - 0.02) ? 2 : ((p.y > pelvisCenter.y + 0.16) ? 1 : 5);
  res = opU(res, HitInfo(dTorso, 4.0, torsoMuscle));

  // Tailored Athletic Shorts (Mat 5.0) - Tucked cleanly inside the shirt overhang!
  vec3 lShortEnd = mix(lHip, lKnee, uGender > 0.5 ? 0.45 : 0.58);
  vec3 rShortEnd = mix(rHip, rKnee, uGender > 0.5 ? 0.45 : 0.58);

  float dShortLegL = sdRoundCone(p, lHip, lShortEnd, 0.080, 0.074);
  float dShortLegR = sdRoundCone(p, rHip, rShortEnd, 0.080, 0.074);
  // Crisp cuff cut perpendicular to the thigh so shorts look like real fabric tubes!
  dShortLegL = smax(dShortLegL, dot(p - lShortEnd, normalize(lKnee - lHip)), 0.008);
  dShortLegR = smax(dShortLegR, dot(p - rShortEnd, normalize(rKnee - rHip)), 0.008);

  float dPelvisShorts = sdEllipsoid(p - (pelvisCenter - vec3(0.0, 0.01, 0.0)), vec3(0.134, 0.095, 0.106));
  float dShorts = smin(dPelvisShorts, min(dShortLegL, dShortLegR), 0.025);
  // Clamp top of shorts strictly below shirtHemY + 0.002 so it never pokes through the shirt
  dShorts = smax(dShorts, p.y - (shirtHemY - 0.002), 0.006);
  res = opU(res, HitInfo(dShorts, 5.0, 6));

  // ========================================================================
  // 5. CRISP WHITE ANKLE SOCKS & 3-LACE SNEAKERS (Exact Reference Image 1!)
  // ========================================================================
  vec3 lSockTop = mix(lAnkle, lKnee, 0.22);
  vec3 rSockTop = mix(rAnkle, rKnee, 0.22);
  float dSockL = sdRoundCone(p, lAnkle, lSockTop, 0.044, 0.046);
  float dSockR = sdRoundCone(p, rAnkle, rSockTop, 0.044, 0.046);
  dSockL = smax(dSockL, dot(p - lSockTop, normalize(lKnee - lAnkle)), 0.005);
  dSockR = smax(dSockR, dot(p - rSockTop, normalize(rKnee - rAnkle)), 0.005);
  res = opU(res, HitInfo(min(dSockL, dSockR), 6.0, 6));

  vec3 lCalfDir = normalize(lAnkle - lKnee);
  vec3 rCalfDir = normalize(rAnkle - rKnee);
  vec3 lFootDir = normalize(vec3(0.0, lCalfDir.z, -lCalfDir.y));
  vec3 rFootDir = normalize(vec3(0.0, rCalfDir.z, -rCalfDir.y));

  vec3 lToe = lAnkle + lFootDir * 0.145 + lCalfDir * 0.022;
  vec3 rToe = rAnkle + rFootDir * 0.145 + rCalfDir * 0.022;
  float dShoeUpper = min(
    sdRoundCone(p, lAnkle - lFootDir * 0.015, lToe, 0.056, 0.050),
    sdRoundCone(p, rAnkle - rFootDir * 0.015, rToe, 0.056, 0.050)
  );
  res = opU(res, HitInfo(dShoeUpper, 7.0, 6));

  // 3 Crisp White Shoelace Bars across each shoe instep (Reference Image 1 & 2!)
  float dLaces = 100.0;
  for (int i = 0; i < 3; i++) {
    float fi = 0.34 + float(i) * 0.16;
    vec3 lLaceC = mix(lAnkle, lToe, fi) - lCalfDir * 0.038;
    vec3 rLaceC = mix(rAnkle, rToe, fi) - rCalfDir * 0.038;
    dLaces = min(dLaces, sdCapsule(p, lLaceC + vec3(-0.026, 0.0, 0.0), lLaceC + vec3(0.026, 0.0, 0.0), 0.0075));
    dLaces = min(dLaces, sdCapsule(p, rLaceC + vec3(-0.026, 0.0, 0.0), rLaceC + vec3(0.026, 0.0, 0.0), 0.0075));
  }

  // Flat Cushioned White Outsole
  float dShoeSole = min(
    sdRoundCone(p, lAnkle + lCalfDir * 0.036 - lFootDir * 0.018, lToe + lCalfDir * 0.032 + lFootDir * 0.010, 0.060, 0.054),
    sdRoundCone(p, rAnkle + rCalfDir * 0.036 - rFootDir * 0.018, rToe + rCalfDir * 0.032 + rFootDir * 0.010, 0.060, 0.054)
  );
  res = opU(res, HitInfo(min(dShoeSole, dLaces), 6.0, 6));

  // ========================================================================
  // 6. MULTI-LOCK SCULPTED 3D CLAY HAIR (Crisp Strand Grooves!)
  // ========================================================================
  // Back skull cap hugging the upper cranium
  float dHairCap = sdEllipsoid(hp - vec3(0.0, 0.042, -0.022), vec3(0.144, 0.142, 0.146));
  // Carve out face opening cleanly
  dHairCap = smax(dHairCap, -(length(hp - vec3(0.0, -0.025, 0.085)) - 0.125), 0.018);

  if (uGender < 0.5) {
    // BOY: Multi-Lock Side-Parted Swept Hair (Exact Reference Image 1 & 2!)
    // Lock 1: Front-right sweeping main pompadour lock
    float lock1 = sdRoundCone(hp, vec3(-0.075, 0.125, 0.075), vec3(0.045, 0.155, 0.125), 0.038, 0.046);
    // Lock 2: Upper-center layered sweeping lock
    float lock2 = sdRoundCone(hp, vec3(-0.055, 0.152, 0.015), vec3(0.085, 0.162, 0.075), 0.042, 0.044);
    // Lock 3: Far-right angled bang lock
    float lock3 = sdRoundCone(hp, vec3(0.035, 0.140, 0.085), vec3(0.115, 0.105, 0.095), 0.036, 0.028);
    // Lock 4: Left-parted side volume puff
    float lock4 = sdRoundCone(hp, vec3(-0.075, 0.135, 0.045), vec3(-0.132, 0.075, 0.065), 0.038, 0.030);
    // Sideburn temple locks in front of ears
    float sideL = sdRoundCone(hp, vec3(-0.115, 0.095, 0.025), vec3(-0.130, 0.025, 0.020), 0.032, 0.020);
    float sideR = sdRoundCone(hp, vec3( 0.115, 0.095, 0.025), vec3( 0.130, 0.025, 0.020), 0.032, 0.020);
    // Back crown tuft
    float tuft = sdCapsule(hp, vec3(0.0, 0.135, -0.105), vec3(0.0, 0.175, -0.150), 0.024);

    // Small smin (0.014) preserves crisp grooves between individual hair locks!
    float dLocks = smin(lock1, lock2, 0.014);
    dLocks = smin(dLocks, lock3, 0.014);
    dLocks = smin(dLocks, lock4, 0.014);
    dLocks = smin(dLocks, min(sideL, sideR), 0.016);
    dLocks = smin(dLocks, tuft, 0.016);
    float dBoyHair = smin(dHairCap, dLocks, 0.018);
    res = opU(res, HitInfo(dBoyHair, 2.0, 0));
  } else {
    // GIRL: Sculpted Parted Bangs + Side Locks + Bouncy S-Curve Ponytail
    float g1 = sdRoundCone(hp, vec3(-0.01, 0.148, 0.095), vec3(-0.125, 0.065, 0.065), 0.042, 0.030);
    float g2 = sdRoundCone(hp, vec3( 0.01, 0.148, 0.095), vec3( 0.125, 0.065, 0.065), 0.042, 0.030);
    float gTop = sdRoundCone(hp, vec3(-0.06, 0.155, 0.02), vec3(0.06, 0.155, 0.02), 0.040, 0.040);
    float dGirlHair = smin(dHairCap, smin(min(g1, g2), gTop, 0.016), 0.018);

    float sway = sin(t * 1.4) * 0.04;
    vec3 pTie = vec3(0.0, 0.085, -0.145);
    vec3 pMid1 = vec3(0.0, 0.175 + sway * 0.4, -0.26);
    vec3 pMid2 = vec3(0.0, 0.115 + sway * 0.8, -0.38);
    vec3 pTip  = vec3(0.0, 0.185 + sway, -0.47);

    float dPony = smin(
      sdRoundCone(hp, pTie, pMid1, 0.044, 0.078),
      smin(
        sdRoundCone(hp, pMid1, pMid2, 0.078, 0.058),
        sdRoundCone(hp, pMid2, pTip, 0.058, 0.022),
        0.032
      ),
      0.032
    );
    dGirlHair = smin(dGirlHair, dPony, 0.020);
    res = opU(res, HitInfo(dGirlHair, 2.0, 0));

    // Scrunchie
    float dScrunchie = length(hp - pTie) - 0.048;
    res = opU(res, HitInfo(dScrunchie, 4.0, 0));
  }

  // ========================================================================
  // 7. EXPRESSIVE EYES, ARCHED BROWS & WARM CORAL SMILE (Mat 3.0 & 9.0)
  // ========================================================================
  vec3 eyeP = vec3(abs(hp.x) - 0.046, hp.y - 0.008, hp.z - 0.122);
  float dEyes = sdEllipsoid(eyeP, vec3(0.014, 0.021, 0.011));

  // Thick, expressive arched eyebrows (Reference Image 1!)
  vec3 browP = vec3(abs(hp.x) - 0.048, hp.y - 0.045 + (abs(hp.x) - 0.048) * 0.15, hp.z - 0.120);
  float dBrows = sdCapsule(browP, vec3(-0.022, 0.002, 0.0), vec3(0.022, -0.003, 0.0), 0.0095);
  res = opU(res, HitInfo(min(dEyes, dBrows), 3.0, 0));

  // Warm Terracotta/Coral-Red Smiling Mouth Curve (Mat 9.0 - Exact Reference Image 1!)
  vec3 mouthP = hp - vec3(0.0, -0.056 + hp.x * hp.x * 2.8, 0.118);
  float dMouth = sdCapsule(mouthP, vec3(-0.024, 0.0, 0.0), vec3(0.024, 0.0, 0.0), 0.0065);
  res = opU(res, HitInfo(dMouth, 9.0, 0));

  // ========================================================================
  // 8. PROPS: 3D HURDLE OR 3D DUMBBELLS
  // ========================================================================
  if (showHurdle) {
    float dBar = sdRoundBox(p - vec3(0.0, -0.36, 0.08), vec3(0.38, 0.036, 0.018), 0.012);
    res = opU(res, HitInfo(dBar, 6.0, 0));

    vec3 hpSym = vec3(abs(p.x) - 0.29, p.y, p.z);
    float dPost = sdCapsule(hpSym, vec3(0.0, -0.38, 0.08), vec3(0.0, -0.82, 0.08), 0.022);
    float dBase = sdCapsule(hpSym, vec3(0.0, -0.82, 0.12), vec3(0.0, -0.82, -0.22), 0.025);
    res = opU(res, HitInfo(min(dPost, dBase), 8.0, 0));
  }

  if (showDumbbells) {
    float dbL = min(
      sdCapsule(p, lPalmCenter + vec3(-0.09, 0.0, 0.0), lPalmCenter + vec3(0.09, 0.0, 0.0), 0.016),
      min(
        sdEllipsoid(p - (lPalmCenter + vec3(-0.085, 0.0, 0.0)), vec3(0.028, 0.065, 0.065)),
        sdEllipsoid(p - (lPalmCenter + vec3( 0.085, 0.0, 0.0)), vec3(0.028, 0.065, 0.065))
      )
    );
    float dbR = min(
      sdCapsule(p, rPalmCenter + vec3(-0.09, 0.0, 0.0), rPalmCenter + vec3(0.09, 0.0, 0.0), 0.016),
      min(
        sdEllipsoid(p - (rPalmCenter + vec3(-0.085, 0.0, 0.0)), vec3(0.028, 0.065, 0.065)),
        sdEllipsoid(p - (rPalmCenter + vec3( 0.085, 0.0, 0.0)), vec3(0.028, 0.065, 0.065))
      )
    );
    res = opU(res, HitInfo(min(dbL, dbR), 8.0, 4));
  }

  return res;
}

vec3 calcNormal(vec3 p) {
  const float h = 0.002;
  const vec2 k = vec2(1.0, -1.0);
  return normalize(
    k.xyy * mapScene(p + k.xyy * h).d +
    k.yyx * mapScene(p + k.yyx * h).d +
    k.yxy * mapScene(p + k.yxy * h).d +
    k.xxx * mapScene(p + k.xxx * h).d
  );
}

float calcAO(vec3 pos, vec3 nor) {
  float occ = 0.0;
  float sca = 1.0;
  for (int i = 0; i < 4; i++) {
    float h = 0.02 + 0.06 * float(i);
    float d = mapScene(pos + h * nor).d;
    occ += (h - d) * sca;
    sca *= 0.75;
  }
  return clamp(1.0 - 2.2 * occ, 0.35, 1.0);
}

void main() {
  vec2 uv = vUv;
  uv.x *= uResolution.x / uResolution.y;

  // Studio Background with soft floor contact shadow
  vec3 bgCol = mix(vec3(0.95, 0.965, 0.985), vec3(1.0, 1.0, 1.0), 1.0 - length(uv) * 0.35);

  // When Super Saiyan or Divine mode is active, introduce the dramatic Dragon Ball battle sky vignette!
  if (uAuraLevel >= 1.5) {
    vec3 animeBg = (uAuraLevel >= 2.5)
      ? mix(vec3(0.14, 0.06, 0.20), vec3(0.05, 0.02, 0.09), length(uv) * 0.65)
      : mix(vec3(0.22, 0.09, 0.18), vec3(0.08, 0.04, 0.09), length(uv) * 0.70);
    bgCol = mix(bgCol, animeBg, 0.88);

    // Radiant background energy rays bursting into the sky (as in Dragon Ball manga/anime)
    float rayAng = atan(uv.y - 0.05, uv.x);
    float rayDist = length(vec2(uv.x, uv.y - 0.05));
    float rayBurst = sin(rayAng * 14.0 + uTime * 4.0) * sin(rayAng * 24.0 - uTime * 6.0);
    rayBurst = smoothstep(0.20, 0.80, rayBurst) * smoothstep(1.3, 0.30, rayDist);
    vec3 rayCol = (uAuraLevel >= 2.5) ? vec3(0.85, 0.40, 1.0) : vec3(1.0, 0.85, 0.15);
    bgCol += rayCol * rayBurst * 0.42;
  } else if (uAuraLevel > 0.5) {
    bgCol = mix(bgCol, vec3(0.98, 0.94, 0.88), 0.35);
  }

  // Orbit Camera around Y-axis
  float cy = cos(uYaw);
  float sy = sin(uYaw);
  vec3 ro = vec3(sy * 2.55, 0.02, cy * 2.55);
  vec3 ta = vec3(0.0, -0.02, 0.0);

  vec3 cw = normalize(ta - ro);
  vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
  vec3 cv = cross(cu, cw);
  vec3 rd = normalize(uv.x * cu + uv.y * cv + 1.85 * cw);

  // Bounding sphere early exit (Expanded when Saiyan aura is active so flames and shockwaves are never clipped)
  float boundR = (uAuraLevel > 0.1) ? 2.15 : 1.35;
  float b = dot(ro, rd);
  float c = dot(ro, ro) - boundR * boundR;
  if (b * b - c < 0.0) {
    gl_FragColor = vec4(bgCol, 1.0);
    return;
  }

  // Soft floor shadow plane check at y = -0.86
  if (rd.y < -0.001) {
    float tFloor = (-0.86 - ro.y) / rd.y;
    if (tFloor > 0.0) {
      vec3 fp = ro + rd * tFloor;
      float distFromOrigin = length(fp.xz);
      float shadowAlpha = smoothstep(0.68, 0.05, distFromOrigin) * 0.22;
      bgCol = mix(bgCol, vec3(0.45, 0.52, 0.62), shadowAlpha);

      // Super Saiyan Ground Energy Shockwave Blast Rings (Option 6)
      if (uAuraLevel > 0.1) {
        vec3 groundAuraCol = (uAuraLevel >= 2.5) 
          ? vec3(0.85, 0.30, 0.98) 
          : ((uAuraLevel >= 1.5) ? vec3(1.0, 0.88, 0.15) : vec3(0.98, 0.75, 0.20));
        for (int gr = 0; gr < 2; gr++) {
          float grPhase = fract(uTime * 1.0 + float(gr) * 0.5);
          float grRadius = 0.15 + grPhase * 0.85;
          float grDist = abs(distFromOrigin - grRadius);
          float grAlpha = smoothstep(0.08, 0.0, grDist) * (1.0 - grPhase) * (1.0 - grPhase);
          bgCol += groundAuraCol * grAlpha * 1.4;
        }
      }
    }
  }

  // Raymarch 3D Clay Scene & Track Closest Distance for Ki Wave Silhouette
  float t = 1.0;
  HitInfo hit = HitInfo(100.0, 0.0, 0);
  bool didHit = false;
  float minD = 100.0;
  vec3 closestP = ro;

  for (int i = 0; i < 58; i++) {
    vec3 p = ro + rd * t;
    hit = mapScene(p);
    if (hit.d < minD) {
      minD = hit.d;
      closestP = p;
    }
    if (hit.d < 0.0025) {
      didHit = true;
      break;
    }
    t += hit.d * 0.88;
    if (t > 4.2) break;
  }

  if (!didHit) {
    // 🌟 SUPER SAIYAN MASSIVE GOLDEN KI FLAMES & EXPANDING BLAST SHOCKWAVES (Option 6)
    if (uAuraLevel > 0.1) {
      vec3 auraCoreCol;
      vec3 auraMidCol;
      vec3 auraOuterCol;
      vec3 waveCol;

      if (uAuraLevel >= 2.5) {
        // LV3: Divine Ultra Instinct / God Mode (Purple-Magenta & Divine Cyan)
        auraCoreCol = vec3(0.95, 0.90, 1.0);
        auraMidCol = vec3(0.85, 0.28, 0.98);
        auraOuterCol = vec3(0.40, 0.10, 0.85);
        waveCol = vec3(0.90, 0.45, 1.0);
      } else if (uAuraLevel >= 1.5) {
        // LV2: SUPER SAIYAN (Pure Blazing Golden Yellow Ki & Electric Sparks!)
        auraCoreCol = vec3(1.0, 1.0, 0.72);      // Blinding white-yellow core
        auraMidCol = vec3(1.0, 0.88, 0.08);       // Intense Dragon Ball lemon/golden yellow
        auraOuterCol = vec3(1.0, 0.52, 0.02);     // Fiery gold-orange outer flames
        waveCol = vec3(1.0, 0.95, 0.25);          // Radiant yellow blast wave
      } else {
        // LV1: Dawn golden embers
        auraCoreCol = vec3(1.0, 0.95, 0.60);
        auraMidCol = vec3(1.0, 0.75, 0.18);
        auraOuterCol = vec3(0.95, 0.45, 0.08);
        waveCol = vec3(1.0, 0.82, 0.20);
      }

      // 1. Spiky Jagged Ki Flame Outline (Dragon Ball anime flames roaring upwards)
      float phi = atan(closestP.z, closestP.x);
      float upY = closestP.y * 6.5 - uTime * 15.0;
      float upFast = closestP.y * 12.0 - uTime * 25.0;

      // Jagged triangular flame spikes pointing outwards
      float spikeA = abs(fract(phi * 2.5 + upY * 0.15) * 2.0 - 1.0);
      float spikeB = abs(fract(phi * 4.2 - upFast * 0.12) * 2.0 - 1.0);
      float spikes = pow(spikeA * 0.65 + spikeB * 0.35, 1.4);

      // Flame boundary extends further out around torso, shoulders and above head
      float flameThickness = 0.14 + 0.18 * spikes + 0.04 * sin(closestP.y * 18.0 - uTime * 20.0);
      flameThickness += 0.10 * smoothstep(-0.2, 0.65, closestP.y); // Wider around upper body
      flameThickness += 0.14 * smoothstep(0.45, 0.85, closestP.y); // Shoots high above head!

      // Flame Intensity & Layering
      float dFlame = minD - flameThickness;
      float flameFactor = smoothstep(0.06, -0.04, dFlame) * smoothstep(-0.85, -0.55, closestP.y);
      float coreFactor = smoothstep(0.04, 0.0, minD);
      vec3 flameColor = mix(mix(auraOuterCol, auraMidCol, flameFactor), auraCoreCol, coreFactor);

      // 2. EXPANDING EXPLOSIVE YELLOW ENERGY BLAST WAVES (黃色光波)
      float shockwave = 0.0;
      for (int w = 0; w < 3; w++) {
        float wavePhase = fract(uTime * 1.35 + float(w) * 0.333);
        float waveRadius = 0.03 + wavePhase * 0.72; // Expands outward from body up to 0.75 units!
        float waveDist = abs(minD - waveRadius);
        float waveThick = 0.036 * (1.0 + wavePhase * 0.7);
        float singleWave = smoothstep(waveThick, 0.002, waveDist) * (1.0 - wavePhase) * (1.0 - wavePhase * 0.6);
        singleWave *= (0.7 + 0.3 * sin(phi * 8.0 - uTime * 12.0 + closestP.y * 10.0));
        shockwave += singleWave;
      }

      // 3. SUPER SAIYAN CRACKLING LIGHTNING SPARKS (SSJ2 金色與青白閃電)
      float lightningNoise = sin(closestP.y * 45.0 - uTime * 38.0 + sin(phi * 14.0) * 8.0);
      float spark = step(0.93, lightningNoise) * smoothstep(0.38, 0.0, minD);
      vec3 sparkCol = vec3(1.0, 1.0, 0.9) * spark * 3.0;

      // 4. Soft outer ambient aura glow
      float ambientKi = smoothstep(0.75, 0.0, minD) * 0.35;

      // Combine All Ki Energy Components
      vec3 totalKi = flameColor * flameFactor * 1.6 + waveCol * shockwave * 2.6 + sparkCol + auraMidCol * ambientKi;
      float totalAlpha = clamp(flameFactor * 1.3 + shockwave * 1.8 + ambientKi * 1.2, 0.0, 1.0);

      // Render onto canvas with strong additive and alpha blending
      bgCol = mix(bgCol, totalKi, totalAlpha * 0.92);
      bgCol += totalKi * 0.55;
    }
    gl_FragColor = vec4(bgCol, 1.0);
    return;
  }

  vec3 pos = ro + rd * t;
  vec3 nor = calcNormal(pos);
  float ao = calcAO(pos, nor);

  // Material Base Colors (Exact Reference Image Palettes!)
  vec3 baseCol = vec3(0.96, 0.74, 0.60); // 1.0 Soft Peach Clay Skin
  float roughness = 0.75;

  // Cute rosy cheeks on face skin
  if (hit.mat < 1.5 && pos.y > 0.35 && pos.z > 0.10) {
    float cheekDist = length(vec2(abs(pos.x) - 0.115, pos.y - uHeadCenter.y + 0.035));
    float blush = smoothstep(0.068, 0.015, cheekDist);
    baseCol = mix(baseCol, vec3(0.97, 0.56, 0.54), blush * 0.42);
  }

  if (hit.mat > 1.5 && hit.mat < 2.5) {
    // 2.0 Hair
    if (uAuraLevel >= 1.5 && uAuraLevel < 2.5) {
      // 🌟 SUPER SAIYAN GLOWING GOLDEN BLONDE HAIR!
      baseCol = vec3(1.0, 0.88, 0.18);
      roughness = 0.28;
    } else if (uAuraLevel >= 2.5) {
      // ⚡ ULTRA INSTINCT SILVER-PURPLE HAIR!
      baseCol = vec3(0.92, 0.88, 1.0);
      roughness = 0.25;
    } else {
      // Normal Hair (Dark Charcoal for Boy, Warm Chocolate Brown for Girl)
      baseCol = (uGender < 0.5) ? vec3(0.20, 0.19, 0.21) : vec3(0.32, 0.18, 0.14);
    }
  } else if (hit.mat > 2.5 && hit.mat < 3.5) {
    // 3.0 Eyes & Brows (with dual-sparkle cute anime catchlights!)
    if (uAuraLevel >= 1.5 && uAuraLevel < 2.5) {
      // Super Saiyan Golden Eyebrows + Emerald-Cyan Eyes!
      if (pos.y > uHeadCenter.y + 0.015) {
        baseCol = vec3(1.0, 0.86, 0.15); // Golden Eyebrows
      } else {
        baseCol = vec3(0.12, 0.90, 0.72); // Fierce Emerald-Cyan Eyes
      }
    } else if (uAuraLevel >= 2.5) {
      baseCol = vec3(0.85, 0.90, 1.0); // Divine Silver Eyes
    } else {
      baseCol = vec3(0.10, 0.08, 0.08);
    }
    roughness = 0.16;
    float sp1 = smoothstep(0.012, 0.005, length(vec2(abs(pos.x) - 0.072, pos.y - uHeadCenter.y - 0.022)));
    float sp2 = smoothstep(0.007, 0.002, length(vec2(abs(pos.x) - 0.084, pos.y - uHeadCenter.y - 0.035)));
    baseCol = mix(baseCol, vec3(1.0), max(sp1, sp2 * 0.85));
  } else if (hit.mat > 3.5 && hit.mat < 4.5) {
    // 4.0 Top (Vibrant Orange Shirt for Boy, Lavender-Purple Tank for Girl)
    baseCol = (uGender < 0.5) ? vec3(0.98, 0.56, 0.22) : vec3(0.72, 0.50, 0.92);
  } else if (hit.mat > 4.5 && hit.mat < 5.5) {
    // 5.0 Shorts (Royal Blue Shorts for Boy, Coral-Orange Shorts for Girl)
    baseCol = (uGender < 0.5) ? vec3(0.23, 0.50, 0.96) : vec3(0.96, 0.42, 0.16);
  } else if (hit.mat > 5.5 && hit.mat < 6.5) {
    // 6.0 White Clay (Drawstrings / Wristbands / Socks / Soles / Hurdle Bar)
    baseCol = vec3(0.96, 0.97, 0.99);
    if (uAction == 0 && pos.y > -0.42 && pos.y < -0.28 && abs(abs(pos.x) - 0.22) < 0.055) {
      baseCol = vec3(0.36, 0.40, 0.46);
    }
  } else if (hit.mat > 6.5 && hit.mat < 7.5) {
    // 7.0 Sneaker Upper
    baseCol = (uGender < 0.5) ? vec3(0.20, 0.46, 0.94) : vec3(0.64, 0.40, 0.88);
  } else if (hit.mat > 7.5 && hit.mat < 8.5) {
    // 8.0 Dark Grey Props
    baseCol = vec3(0.38, 0.42, 0.48);
  } else if (hit.mat > 8.5) {
    // 9.0 Warm Terracotta / Coral Red Smiling Mouth Curve (Reference Image 1!)
    baseCol = vec3(0.86, 0.34, 0.28);
    roughness = 0.45;
  }

  // Muscle Recovery Thermal Subsurface Glow - LOCALIZED HOTSPOT RADAR (Doesn't dye garments!)
  vec3 glowEmission = vec3(0.0);
  if (uShowGlow > 0.5 && hit.muscle > 0) {
    float mStatus = 0.0;
    vec3 mCenter = vec3(0.0);

    if (hit.muscle == 1) {
      mStatus = uMuscleStatus123.x;
      mCenter = vec3(0.0, 0.25, 0.18); // CHEST
    } else if (hit.muscle == 2) {
      mStatus = uMuscleStatus123.y;
      mCenter = vec3(0.0, 0.24, -0.18); // BACK
    } else if (hit.muscle == 3) {
      mStatus = uMuscleStatus123.z;
      mCenter = vec3(pos.x > 0.0 ? 0.22 : -0.22, 0.30, 0.0); // SHOULDERS
    } else if (hit.muscle == 4) {
      mStatus = uMuscleStatus456.x;
      mCenter = vec3(pos.x > 0.0 ? 0.30 : -0.30, 0.08, 0.06); // ARMS
    } else if (hit.muscle == 5) {
      mStatus = uMuscleStatus456.y;
      mCenter = vec3(0.0, 0.08, 0.16); // CORE
    } else if (hit.muscle == 6) {
      mStatus = uMuscleStatus456.z;
      mCenter = vec3(pos.x > 0.0 ? 0.15 : -0.15, -0.30, 0.04); // LEGS (Quadriceps)
    }

    // Radial hotspot intensity so fabric keeps its saturated color outside the core
    float distM = length(pos - mCenter);
    float hotspotFactor = smoothstep(0.24, 0.04, distM);

    float pulse = 0.5 + 0.5 * sin(uTime * 5.0);
    if (mStatus > 1.5) {
      // FATIGUED (<45%): Pulsing Rose-Red Thermal Hotspot
      baseCol = mix(baseCol, vec3(0.98, 0.25, 0.38), (0.55 + 0.15 * pulse) * hotspotFactor);
      glowEmission = vec3(0.50, 0.06, 0.14) * (0.6 + 0.4 * pulse) * hotspotFactor;
    } else if (mStatus > 0.5) {
      // RECOVERING (45-84%): Warm Amber Glow
      baseCol = mix(baseCol, vec3(0.98, 0.68, 0.12), 0.48 * hotspotFactor);
      glowEmission = vec3(0.32, 0.18, 0.02) * hotspotFactor;
    } else if (hit.muscle == uSelectedMuscle) {
      // SELECTED & RECOVERED: Emerald Highlight
      baseCol = mix(baseCol, vec3(0.15, 0.88, 0.58), 0.40 * hotspotFactor);
      glowEmission = vec3(0.06, 0.30, 0.16) * hotspotFactor;
    }
  }

  // Blender 3-Point Studio Clay Lighting + Subsurface Scattering (SSS)
  vec3 keyLight = normalize(vec3(0.55 * cy + 0.65 * sy, 0.75, 0.65 * cy - 0.55 * sy));
  vec3 fillLight = normalize(vec3(-0.6 * cy, 0.25, 0.6 * sy));

  // Half-Lambert Soft Clay Diffuse (prevents harsh black shadows!)
  float ndl = dot(nor, keyLight);
  float wrapDiff = pow(ndl * 0.5 + 0.5, 1.35);

  // Warm Subsurface Scattering (Pixar soft translucency)
  vec3 sssCol = vec3(0.98, 0.42, 0.28) * smoothstep(-0.4, 0.4, ndl) * (1.0 - max(0.0, ndl)) * 0.28;

  // Soft Specular Sheen
  vec3 halfVec = normalize(keyLight - rd);
  float spec = pow(max(0.0, dot(nor, halfVec)), mix(48.0, 12.0, roughness)) * mix(0.55, 0.16, roughness);

  // Soft Fresnel Studio Rim Light (signature look of Blender 3D icons!)
  float fresnel = pow(1.0 - max(0.0, dot(nor, -rd)), 3.0);
  vec3 rimLight = vec3(1.0, 0.98, 0.96) * fresnel * 0.34;

  // Combine studio lighting
  vec3 shadowTint = baseCol * vec3(0.76, 0.64, 0.62);
  vec3 col = mix(shadowTint, baseCol * 1.06, wrapDiff);
  col += sssCol;
  col += vec3(1.0, 0.98, 0.95) * spec;
  col += rimLight;
  col *= mix(0.68, 1.0, ao);
  col += glowEmission * (0.5 + 0.8 * fresnel);

  // Super Saiyan Blazing Golden Rim Light & Surface Ki Energy Waves (Option 6)
  if (uAuraLevel > 0.1) {
    vec3 auraRimCol = (uAuraLevel >= 2.5) 
      ? vec3(0.85, 0.30, 0.98) 
      : ((uAuraLevel >= 1.5) ? vec3(1.0, 0.88, 0.15) : vec3(0.98, 0.75, 0.20));
    
    // 1. Dazzling Golden Fresnel Rim Light around the silhouette
    float fresnelAura = pow(1.0 - max(0.0, dot(nor, -rd)), 1.8);
    float electricPulse = 0.75 + 0.25 * sin(uTime * 10.0 + pos.y * 14.0);
    col += auraRimCol * fresnelAura * electricPulse * 1.8;

    // 2. Surging Golden Ki energy waves licking across chest, arms, and clothing
    if (uAuraLevel >= 1.5) {
      float frontKi = sin(pos.y * 16.0 - uTime * 14.0 + sin(pos.x * 14.0) * 3.5);
      float frontKi2 = sin(pos.y * 24.0 - uTime * 22.0 + pos.z * 12.0);
      if (frontKi > 0.50 && frontKi2 > 0.20) {
        col += vec3(1.0, 0.92, 0.35) * (frontKi - 0.50) * 2.0;
      }
      // Global ambient golden bath on the whole character
      col = mix(col, col * vec3(1.15, 1.08, 0.85) + vec3(0.12, 0.09, 0.01), 0.45);
    }
  }

  // Tone mapping & gamma adjustment for crisp pastel-vibrant studio colors
  col = clamp(col, 0.0, 1.0);
  gl_FragColor = vec4(col, 1.0);
}
`

function compileShader(glCtx, type, src) {
  const sh = glCtx.createShader(type)
  glCtx.shaderSource(sh, src)
  glCtx.compileShader(sh)
  if (!glCtx.getShaderParameter(sh, glCtx.COMPILE_STATUS)) {
    console.error('Shader compile error:', glCtx.getShaderInfoLog(sh))
    glCtx.deleteShader(sh)
    return null
  }
  return sh
}

function initWebGL() {
  const canvas = glCanvasRef.value
  if (!canvas) return false
  gl = canvas.getContext('webgl', { antialias: true, alpha: false })
  if (!gl) return false

  const vs = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER_SRC)
  const fs = compileShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER_SRC)
  if (!vs || !fs) return false

  program = gl.createProgram()
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('Program link error:', gl.getProgramInfoLog(program))
    return false
  }

  gl.useProgram(program)

  // Fullscreen quad
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
    gl.STATIC_DRAW
  )
  const aPos = gl.getAttribLocation(program, 'aPosition')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  uniforms = {
    uResolution: gl.getUniformLocation(program, 'uResolution'),
    uTime: gl.getUniformLocation(program, 'uTime'),
    uYaw: gl.getUniformLocation(program, 'uYaw'),
    uGender: gl.getUniformLocation(program, 'uGender'),
    uAction: gl.getUniformLocation(program, 'uAction'),
    uShowGlow: gl.getUniformLocation(program, 'uShowGlow'),
    uSelectedMuscle: gl.getUniformLocation(program, 'uSelectedMuscle'),
    uMuscleStatus123: gl.getUniformLocation(program, 'uMuscleStatus123'),
    uMuscleStatus456: gl.getUniformLocation(program, 'uMuscleStatus456'),
    uHeadCenter: gl.getUniformLocation(program, 'uHeadCenter'),
    uClickTime: gl.getUniformLocation(program, 'uClickTime'),
    uAuraLevel: gl.getUniformLocation(program, 'uAuraLevel')
  }
  return true
}

function projectPin3D(pt3d, cosY, sinY) {
  const rx = pt3d.x * cosY - pt3d.z * sinY
  const rz = pt3d.x * sinY + pt3d.z * cosY
  const fov = 1.85 / (2.55 - rz)
  return {
    xPct: Math.min(88, Math.max(12, 50 + rx * fov * 42)),
    yPct: Math.min(88, Math.max(12, 50 - pt3d.y * fov * 52)),
    rz
  }
}

function renderLoop(timestamp = 0) {
  const canvas = glCanvasRef.value
  if (!canvas || !gl || !program) return

  const clientW = canvas.clientWidth || 400
  const clientH = canvas.clientHeight || 330
  if (stageSize.value.w !== clientW || stageSize.value.h !== clientH) {
    stageSize.value = { w: clientW, h: clientH }
  }

  const dpr = Math.min(window.devicePixelRatio || 2, 2.0)
  const w = Math.floor(clientW * dpr)
  const h = Math.floor(clientH * dpr)
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w
    canvas.height = h
    gl.viewport(0, 0, w, h)
  }

  if (autoRotate.value && !isDragging.value) {
    yaw.value += 0.012
  } else if (targetYaw.value !== null) {
    const diff = targetYaw.value - yaw.value
    const wrapped = Math.atan2(Math.sin(diff), Math.cos(diff))
    if (Math.abs(wrapped) < 0.02) {
      yaw.value = targetYaw.value
      targetYaw.value = null
    } else {
      yaw.value += wrapped * 0.14
    }
  }

  const actObj = workoutActions.find(a => a.key === currentAction.value)
  const actId = actObj ? actObj.id : 0

  const statusArr = new Float32Array(7)
  normalizedMuscles.value.forEach(m => {
    const idx = MUSCLE_INDEX[m.muscle_group]
    if (idx) {
      statusArr[idx] = m.status === 'FATIGUED' ? 2.0 : (m.status === 'RECOVERING' ? 1.0 : 0.0)
    }
  })

  const sec = timestamp * 0.001
  const tAnim = sec * 3.2
  let headY = 0.575
  if (actId === 5) headY = 0.575 + Math.sin(tAnim * 0.8) * 0.010
  else if (actId === 0) headY = 0.575 + 0.14 + (0.5 + 0.5 * Math.sin(tAnim * 0.9)) * 0.09
  else if (actId === 1) headY = 0.575 + Math.abs(Math.cos(tAnim * 1.35)) * 0.055
  else if (actId === 3) headY = 0.575 - (0.5 + 0.5 * Math.sin(tAnim * 1.1)) * 0.22
  else if (actId === 6) headY = 0.575 - 0.16 + Math.sin(tAnim * 0.5) * 0.012

  gl.useProgram(program)
  gl.uniform2f(uniforms.uResolution, w, h)
  gl.uniform1f(uniforms.uTime, sec)
  gl.uniform1f(uniforms.uYaw, yaw.value)
  gl.uniform1f(uniforms.uGender, isFemale.value ? 1.0 : 0.0)
  gl.uniform1i(uniforms.uAction, actId)
  gl.uniform1f(uniforms.uShowGlow, showHotspotGlow.value ? 1.0 : 0.0)
  gl.uniform1i(uniforms.uSelectedMuscle, MUSCLE_INDEX[selectedMuscleGroup.value] || 1)
  gl.uniform3f(uniforms.uMuscleStatus123, statusArr[1], statusArr[2], statusArr[3])
  gl.uniform3f(uniforms.uMuscleStatus456, statusArr[4], statusArr[5], statusArr[6])
  gl.uniform3f(uniforms.uHeadCenter, 0.0, headY, 0.015)
  const clickSec = sec - clickBounceTime.value
  gl.uniform1f(uniforms.uClickTime, clickSec >= 0 && clickSec < 10.0 ? clickSec : 999.0)
  gl.uniform1f(uniforms.uAuraLevel, currentAura.value.level)

  gl.drawArrays(gl.TRIANGLES, 0, 6)

  // Update 3D-projected floating pins with slender athletic anchors
  const cosY = Math.cos(yaw.value)
  const sinY = Math.sin(yaw.value)
  const isStanding = actId === 5
  const pinAnchors = isStanding
    ? {
        SHOULDERS: { x: -0.22, y: 0.35, z: 0.05, frontOnly: false },
        CHEST: { x: 0.0, y: 0.28, z: 0.16, frontOnly: true },
        CORE: { x: 0.0, y: 0.09, z: 0.15, frontOnly: true },
        BACK: { x: 0.0, y: 0.28, z: -0.16, backOnly: true },
        ARMS: { x: 0.26, y: 0.10, z: 0.05, frontOnly: false },
        LEGS: { x: 0.18, y: -0.38, z: 0.05, frontOnly: false }
      }
    : {
        SHOULDERS: { x: -0.24, y: 0.36, z: 0.05, frontOnly: false },
        CHEST: { x: 0.0, y: 0.29, z: 0.18, frontOnly: true },
        CORE: { x: 0.0, y: 0.10, z: 0.16, frontOnly: true },
        BACK: { x: 0.0, y: 0.29, z: -0.18, backOnly: true },
        ARMS: { x: 0.28, y: 0.16, z: 0.06, frontOnly: false },
        LEGS: { x: 0.20, y: -0.38, z: 0.08, frontOnly: false }
      }

  projectedMusclePins.value = normalizedMuscles.value.map(m => {
    const anch = pinAnchors[m.muscle_group] || { x: 0, y: 0, z: 0 }
    const p = projectPin3D(anch, cosY, sinY)
    let visible = true
    if (anch.frontOnly && cosY < -0.25) visible = false
    if (anch.backOnly && cosY > 0.25) visible = false
    return {
      ...m,
      xPct: p.xPct,
      yPct: p.yPct,
      visible
    }
  })

  animFrameId = requestAnimationFrame(renderLoop)
}

onMounted(() => {
  if (initWebGL()) {
    animFrameId = requestAnimationFrame(renderLoop)
  }
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animFrameId)
})

function getPinBadgeClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-600 text-white border-rose-200 shadow-rose-500/30'
  if (status === 'RECOVERING') return 'bg-amber-400 text-slate-950 border-amber-200 shadow-amber-500/30'
  return 'bg-white/95 text-emerald-700 border-emerald-300 shadow-slate-300/60'
}

function getPinRingClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-500'
  if (status === 'RECOVERING') return 'bg-amber-400'
  return 'bg-emerald-400'
}

function getBottomPillClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100'
  if (status === 'RECOVERING') return 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
  return 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
}

function getDotClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-500'
  if (status === 'RECOVERING') return 'bg-amber-400'
  return 'bg-emerald-500'
}

function getDetailHudClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-50/90 border-rose-200'
  if (status === 'RECOVERING') return 'bg-amber-50/90 border-amber-200'
  return 'bg-emerald-50/80 border-emerald-200'
}

function getHudBadgeClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-600 text-white'
  if (status === 'RECOVERING') return 'bg-amber-400 text-slate-950'
  return 'bg-emerald-600 text-white'
}

function getHotspotStatusLabel(status) {
  if (status === 'FATIGUED') return '🔥 充血疲勞熱點'
  if (status === 'RECOVERING') return '⏳ 超補償修復中'
  return '✅ 滿血可進攻'
}

function getSideCardClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-50/95 border-rose-300 text-rose-950 hover:bg-rose-100 shadow-rose-200/50'
  if (status === 'RECOVERING') return 'bg-amber-50/95 border-amber-300 text-amber-950 hover:bg-amber-100 shadow-amber-200/50'
  return 'bg-white/95 border-slate-200 text-slate-800 hover:bg-slate-100 shadow-slate-200/40'
}

function getPctBadgeClass(status) {
  if (status === 'FATIGUED') return 'bg-rose-100 text-rose-700'
  if (status === 'RECOVERING') return 'bg-amber-100 text-amber-800'
  return 'bg-emerald-100 text-emerald-700'
}

function getSideCardStatusHint(m) {
  if (m.status === 'FATIGUED') return '🔥 充血疲勞'
  if (m.status === 'RECOVERING') return '⏳ 修復中'
  return '✅ 滿血備戰'
}
</script>

<style scoped>
.reaction-pop-enter-active {
  transition: all 0.32s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.reaction-pop-leave-active {
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}
.reaction-pop-enter-from {
  opacity: 0;
  transform: translate(-50%, 14px) scale(0.8);
}
.reaction-pop-leave-to {
  opacity: 0;
  transform: translate(-50%, -12px) scale(0.9);
}
</style>
