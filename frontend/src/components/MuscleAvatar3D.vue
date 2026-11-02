<template>
  <div class="rounded-2xl overflow-hidden bg-white border border-slate-200/90 shadow-sm relative select-none">
    <!-- Top Bar: Boy / Girl Switcher & 360° Camera Controls -->
    <div class="px-3 pt-3 pb-2 flex items-center justify-between gap-1.5 flex-wrap border-b border-slate-100 bg-slate-50/80">
      <!-- Automatic Character Badge based on User Profile Gender -->
      <div class="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-slate-200/90 shadow-2xs">
        <span class="text-sm">{{ isFemale ? '👧' : '👦' }}</span>
        <span class="text-xs font-black text-slate-800">
          {{ isFemale ? '活力馬尾女' : '熱血格鬥肌霸' }}
        </span>
        <span class="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-500">
          3D 即時體態
        </span>
      </div>

      <!-- 3D View Angle, Thermal Glow Toggle & Auto-Spin Controls -->
      <div class="flex items-center gap-1">
        <button
          type="button"
          @click="rotateToAngle(-0.55)"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all"
          :class="!autoRotate && Math.cos(yaw) >= 0 ? 'bg-slate-900 text-white shadow-2xs' : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'"
        >
          正面
        </button>
        <button
          type="button"
          @click="rotateToAngle(Math.PI - 0.55)"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all"
          :class="!autoRotate && Math.cos(yaw) < 0 ? 'bg-slate-900 text-white shadow-2xs' : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'"
        >
          背面(背/臀)
        </button>
        <button
          type="button"
          @click="autoRotate = !autoRotate"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all border"
          :class="autoRotate
            ? 'bg-emerald-50 text-emerald-700 border-emerald-300 shadow-2xs'
            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'"
        >
          {{ autoRotate ? '🔄 轉圈中' : '🔄 360°轉圈' }}
        </button>
        <button
          type="button"
          @click="showHotspotGlow = !showHotspotGlow"
          class="px-2 py-1 rounded-lg text-[10px] font-extrabold transition-all border"
          :class="showHotspotGlow
            ? 'bg-rose-50 text-rose-700 border-rose-200'
            : 'bg-white text-slate-500 border-slate-200'"
          title="切換公仔身上的肌肉熱點發光顯示"
        >
          {{ showHotspotGlow ? '🔥 熱點光:開' : '🔥 熱點光:關' }}
        </button>
      </div>
    </div>

    <!-- Second Bar: Cute 3D Clay Workout Animations -->
    <div class="px-3 py-1.5 bg-white border-b border-slate-100 flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
      <span class="text-[10px] font-bold text-slate-400 whitespace-nowrap flex-shrink-0">🎬 3D 健身動作：</span>
      <div class="flex items-center gap-1">
        <button
          v-for="act in workoutActions"
          :key="act.key"
          type="button"
          @click="currentAction = act.key"
          class="px-2.5 py-1 rounded-lg text-[10px] font-extrabold whitespace-nowrap transition-all"
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
        ↔️ 左右拖曳可 360° 旋轉 · 點擊兩側部位連動
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
        <div class="space-y-0.5 min-w-0">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="text-xs font-black text-slate-900">{{ activeMuscleDetail.label_zh }}</span>
            <span
              class="text-[10px] font-black px-2 py-0.5 rounded-full"
              :class="getHudBadgeClass(activeMuscleDetail.status)"
            >
              {{ getHotspotStatusLabel(activeMuscleDetail.status) }} · {{ activeMuscleDetail.recovery_percentage }}%
            </span>
          </div>
          <div class="text-[11px] text-slate-600 flex items-center gap-2 flex-wrap">
            <span v-if="activeMuscleDetail.hours_since_last_trained !== null">
              🕒 上次訓練：{{ activeMuscleDetail.hours_since_last_trained }}h 前
            </span>
            <span v-else>🕒 近期尚未訓練此部位</span>

            <span
              v-if="activeMuscleDetail.hours_until_recovered > 0"
              class="text-rose-600 font-bold"
            >
              ⏳ 建議再休 {{ activeMuscleDetail.hours_until_recovered }}h (週期 {{ activeMuscleDetail.target_recovery_hours || 48 }}h)
            </span>
            <span v-else class="text-emerald-700 font-bold">
              ✅ 已達超補償巔峰，可安排訓練！
            </span>
          </div>
        </div>

        <button
          v-if="canRecommendSplit(activeMuscleDetail.muscle_group)"
          type="button"
          @click="$emit('recommend-split', activeMuscleDetail.muscle_group)"
          class="px-3 py-2 rounded-xl text-[11px] font-black whitespace-nowrap flex-shrink-0 transition-all active:scale-95 shadow-sm"
          :class="activeMuscleDetail.status === 'FATIGUED'
            ? 'bg-rose-100 hover:bg-rose-200 text-rose-800 border border-rose-300'
            : 'bg-emerald-600 hover:bg-emerald-700 text-white'"
        >
          {{ activeMuscleDetail.status === 'FATIGUED' ? '⚠️ 輕量恢復排課' : '⚡ 排練此部位' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  muscles: {
    type: Array,
    default: () => []
  },
  activeWorkoutMuscles: {
    type: Array,
    default: () => []
  }
})

defineEmits(['recommend-split'])

const authStore = useAuthStore()

// Gender is automatically derived from the user's profile settings (no manual toggle needed)
const isFemale = computed(() => {
  return authStore.profile?.gender === 'FEMALE'
})
const gender = computed(() => (isFemale.value ? 'FEMALE' : 'MALE'))

// 6 Cute 3D Clay Workout Animations
const workoutActions = [
  { key: 'STAND', id: 5, icon: '🧍', label: '直立站姿' },
  { key: 'RUN', id: 1, icon: '🏃', label: '活力慢跑' },
  { key: 'HURDLE', id: 0, icon: '👟', label: '飛躍跨欄' },
  { key: 'CURL', id: 2, icon: '💪', label: '啞鈴彎舉' },
  { key: 'SQUAT', id: 3, icon: '🏋️', label: '深蹲訓練' },
  { key: 'PRESS', id: 4, icon: '🙌', label: '活力肩推' }
]
const currentAction = ref('STAND')
const showHotspotGlow = ref(true)

// 360° Camera Yaw (Default -0.55 rad = 3/4 side-front angle matching the reference images!)
const yaw = ref(-0.55)
const targetYaw = ref(null)
const autoRotate = ref(true)
const isDragging = ref(false)
const lastPointerX = ref(0)
const dragMoved = ref(false)

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
  autoRotate.value = false
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
uniform int uAction;        // 0 = HURDLE, 1 = RUN, 2 = CURL, 3 = SQUAT, 4 = PRESS
uniform float uShowGlow;
uniform int uSelectedMuscle;
uniform vec3 uMuscleStatus123; // x=CHEST(1), y=BACK(2), z=SHOULDERS(3)
uniform vec3 uMuscleStatus456; // x=ARMS(4), y=CORE(5), z=LEGS(6)
uniform vec3 uHeadCenter;

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
// 1.0 = Skin
// 2.0 = Hair
// 3.0 = Eyes / Brows
// 4.0 = Top (Boy Orange Shirt / Girl Purple Tank)
// 5.0 = Shorts (Boy Blue Shorts / Girl Orange Shorts)
// 6.0 = White Clay (Socks / Shoe Soles / Hurdle Bar)
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

// Evaluate complete 3D Clay Character Scene
HitInfo mapScene(vec3 p) {
  // Animation kinematics
  float t = uTime * 3.2;
  float bounceY = 0.0;
  float leanZ = 0.0;

  vec3 lHip = vec3(-0.14, -0.08, 0.0);
  vec3 rHip = vec3( 0.14, -0.08, 0.0);
  vec3 lKnee = vec3(-0.15, -0.44, 0.03);
  vec3 rKnee = vec3( 0.15, -0.44, 0.03);
  vec3 lAnkle = vec3(-0.16, -0.78, 0.0);
  vec3 rAnkle = vec3( 0.16, -0.78, 0.0);

  vec3 lShoulder = vec3(-0.22, 0.30, 0.0);
  vec3 rShoulder = vec3( 0.22, 0.30, 0.0);
  vec3 lElbow = vec3(-0.30, 0.12, -0.02);
  vec3 rElbow = vec3( 0.30, 0.12, -0.02);
  vec3 lWrist = vec3(-0.32, -0.06, 0.14);
  vec3 rWrist = vec3( 0.32, -0.06, 0.14);

  bool showHurdle = false;
  bool showDumbbells = false;

  if (uAction == 5) {
    // ACTION 5: NATURAL STANDING STRAIGHT (直立站姿 - 360° 全方位檢視各部位肌肉與體態)
    float breath = sin(t * 0.8) * 0.012;
    bounceY = breath;
    leanZ = 0.0;

    lHip = vec3(-0.14, -0.08 + bounceY, 0.0);
    rHip = vec3( 0.14, -0.08 + bounceY, 0.0);

    // Natural straight legs planted on floor
    lKnee = vec3(-0.14, -0.44 + bounceY, 0.01);
    rKnee = vec3( 0.14, -0.44 + bounceY, 0.01);
    lAnkle = vec3(-0.14, -0.78, 0.0);
    rAnkle = vec3( 0.14, -0.78, 0.0);

    // Upright natural shoulders
    lShoulder = vec3(-0.21, 0.30 + bounceY, 0.0);
    rShoulder = vec3( 0.21, 0.30 + bounceY, 0.0);

    // Natural arms hanging alongside the body with relaxed elbows and hands
    lElbow = vec3(-0.28, 0.06 + bounceY, 0.01);
    rElbow = vec3( 0.28, 0.06 + bounceY, 0.01);
    lWrist = vec3(-0.26, -0.18 + bounceY + breath * 0.5, 0.04);
    rWrist = vec3( 0.26, -0.18 + bounceY + breath * 0.5, 0.04);
  } else if (uAction == 0) {
    // ACTION 0: HURDLE JUMP (Exact dynamic pose from Reference Image 1!)
    showHurdle = true;
    float jw = 0.5 + 0.5 * sin(t * 0.9);
    bounceY = 0.14 + jw * 0.10;
    leanZ = 0.08;

    // Right leg kicks high & forward over hurdle; Left leg tucks back
    rHip = vec3(0.14, -0.08 + bounceY, 0.04);
    rKnee = vec3(0.15, -0.04 + bounceY, 0.32);
    rAnkle = vec3(0.15, -0.18 + bounceY, 0.62);

    lHip = vec3(-0.14, -0.08 + bounceY, -0.04);
    lKnee = vec3(-0.15, -0.40 + bounceY, -0.14);
    lAnkle = vec3(-0.15, -0.34 + bounceY, -0.46);

    // Left arm punches forward, Right arm swings back
    lShoulder = vec3(-0.21, 0.30 + bounceY, leanZ);
    rShoulder = vec3( 0.21, 0.30 + bounceY, leanZ);
    lElbow = vec3(-0.28, 0.20 + bounceY, 0.24);
    lWrist = vec3(-0.20, 0.30 + bounceY, 0.44);
    rElbow = vec3( 0.32, 0.24 + bounceY, -0.20);
    rWrist = vec3( 0.38, 0.04 + bounceY, -0.26);
  } else if (uAction == 1) {
    // ACTION 1: ENERGETIC RUN (Exact pose from Reference Images 2 & 3!)
    float s = sin(t * 1.4);
    bounceY = abs(cos(t * 1.4)) * 0.06;
    leanZ = 0.05;

    lHip = vec3(-0.14, -0.08 + bounceY, 0.0);
    rHip = vec3( 0.14, -0.08 + bounceY, 0.0);

    lKnee = vec3(-0.15, -0.40 + bounceY + max(0.0, s) * 0.12, s * 0.24 + 0.04);
    lAnkle = vec3(-0.15, -0.74 + bounceY + max(0.0, -s) * 0.16, s * 0.38 - 0.06);

    rKnee = vec3( 0.15, -0.40 + bounceY + max(0.0, -s) * 0.12, -s * 0.24 + 0.04);
    rAnkle = vec3( 0.15, -0.74 + bounceY + max(0.0, s) * 0.16, -s * 0.38 - 0.06);

    lShoulder = vec3(-0.21, 0.30 + bounceY, leanZ);
    rShoulder = vec3( 0.21, 0.30 + bounceY, leanZ);
    lElbow = vec3(-0.28, 0.12 + bounceY, -s * 0.18);
    lWrist = vec3(-0.24, 0.18 + bounceY + max(0.0, -s) * 0.10, -s * 0.26 + 0.16);

    rElbow = vec3( 0.28, 0.12 + bounceY, s * 0.18);
    rWrist = vec3( 0.24, 0.18 + bounceY + max(0.0, s) * 0.10, s * 0.26 + 0.16);
  } else if (uAction == 2) {
    // ACTION 2: DUMBBELL BICEP CURL
    showDumbbells = true;
    float cw = 0.5 + 0.5 * sin(t * 1.3);
    bounceY = sin(t * 1.3) * 0.015;
    lShoulder = vec3(-0.22, 0.30 + bounceY, 0.0);
    rShoulder = vec3( 0.22, 0.30 + bounceY, 0.0);
    lElbow = vec3(-0.28, 0.10 + bounceY, 0.04);
    rElbow = vec3( 0.28, 0.10 + bounceY, 0.04);
    lWrist = vec3(-0.28, -0.06 + cw * 0.28 + bounceY, 0.14 + sin(cw * 3.1415) * 0.14);
    rWrist = vec3( 0.28, -0.06 + cw * 0.28 + bounceY, 0.14 + sin(cw * 3.1415) * 0.14);
  } else if (uAction == 3) {
    // ACTION 3: SQUAT
    float sq = 0.5 + 0.5 * sin(t * 1.1);
    bounceY = -sq * 0.24;
    leanZ = sq * 0.08;
    lHip = vec3(-0.15, -0.08 + bounceY, -sq * 0.14);
    rHip = vec3( 0.15, -0.08 + bounceY, -sq * 0.14);
    lKnee = vec3(-0.17, -0.44 + bounceY * 0.35, 0.05 + sq * 0.18);
    rKnee = vec3( 0.17, -0.44 + bounceY * 0.35, 0.05 + sq * 0.18);
    lShoulder = vec3(-0.22, 0.30 + bounceY, leanZ);
    rShoulder = vec3( 0.22, 0.30 + bounceY, leanZ);
    lElbow = vec3(-0.24, 0.16 + bounceY, 0.14 + sq * 0.12);
    rElbow = vec3( 0.24, 0.16 + bounceY, 0.14 + sq * 0.12);
    lWrist = vec3(-0.12, 0.20 + bounceY, 0.30 + sq * 0.16);
    rWrist = vec3( 0.12, 0.20 + bounceY, 0.30 + sq * 0.16);
  } else {
    // ACTION 4: OVERHEAD SHOULDER PRESS
    showDumbbells = true;
    float pw = 0.5 + 0.5 * sin(t * 1.2);
    bounceY = pw * 0.02;
    lShoulder = vec3(-0.22, 0.30 + bounceY, 0.0);
    rShoulder = vec3( 0.22, 0.30 + bounceY, 0.0);
    lElbow = vec3(-0.32 + pw * 0.05, 0.26 + pw * 0.22 + bounceY, 0.02);
    rElbow = vec3( 0.32 - pw * 0.05, 0.26 + pw * 0.22 + bounceY, 0.02);
    lWrist = vec3(-0.28 + pw * 0.06, 0.48 + pw * 0.28 + bounceY, 0.04);
    rWrist = vec3( 0.28 - pw * 0.06, 0.48 + pw * 0.28 + bounceY, 0.04);
  }

  vec3 pelvisCenter = (lHip + rHip) * 0.5 + vec3(0.0, 0.04, 0.0);
  vec3 chestCenter = vec3(0.0, 0.26 + bounceY, leanZ);
  vec3 neckTop = vec3(0.0, 0.42 + bounceY, leanZ);
  vec3 headCenter = vec3(0.0, 0.62 + bounceY, leanZ + 0.02);

  // ========================================================================
  // 1. SKIN BASE: HEAD, EARS, NOSE, NECK, ARMS & LEGS
  // ========================================================================
  // Cute Chubby-Cheek 3D Clay Head (Cranium sphere + soft lower cheek ellipsoid)
  vec3 hp = p - headCenter;
  float dHead = smin(
    length(hp) - 0.225,
    sdEllipsoid(hp - vec3(0.0, -0.045, 0.02), vec3(0.225, 0.17, 0.205)),
    0.06
  );
  // Cute Button Nose
  float dNose = length(hp - vec3(0.0, -0.02, 0.225)) - 0.036;
  dHead = smin(dHead, dNose, 0.022);

  // Cute Round C-Shaped Ears
  vec3 earP = vec3(abs(hp.x) - 0.225, hp.y + 0.015, hp.z + 0.01);
  float dEar = sdEllipsoid(earP, vec3(0.055, 0.072, 0.045));
  float dEarHole = length(earP - vec3(0.01, 0.0, 0.025)) - 0.028;
  dEar = smax(dEar, -dEarHole, 0.015);
  dHead = smin(dHead, dEar, 0.02);

  // Neck
  float dNeck = sdRoundCone(p, chestCenter, neckTop, 0.09, 0.078);
  float dSkinHeadNeck = smin(dHead, dNeck, 0.03);
  HitInfo res = HitInfo(dSkinHeadNeck, 1.0, 0);

  // Seamless 3D Clay Arms (Shoulder -> Elbow -> Wrist + Cute Fist & Thumb)
  float dArmL = smin(
    sdRoundCone(p, lShoulder, lElbow, 0.078, 0.070),
    sdRoundCone(p, lElbow, lWrist, 0.070, 0.058),
    0.035
  );
  float dHandL = smin(
    length(p - lWrist) - 0.076,
    length(p - (lWrist + vec3(0.04, 0.02, 0.03))) - 0.036,
    0.025
  );
  dArmL = smin(dArmL, dHandL, 0.025);

  float dArmR = smin(
    sdRoundCone(p, rShoulder, rElbow, 0.078, 0.070),
    sdRoundCone(p, rElbow, rWrist, 0.070, 0.058),
    0.035
  );
  float dHandR = smin(
    length(p - rWrist) - 0.076,
    length(p - (rWrist + vec3(-0.04, 0.02, 0.03))) - 0.036,
    0.025
  );
  dArmR = smin(dArmR, dHandR, 0.025);

  float dArms = min(dArmL, dArmR);
  // Upper shoulder deltoid zone
  float dShoulders = min(length(p - lShoulder) - 0.095, length(p - rShoulder) - 0.095);
  res = opSmoothSkin(res, HitInfo(dShoulders, 1.0, 3), 0.03);
  res = opSmoothSkin(res, HitInfo(dArms, 1.0, 4), 0.025);

  // Seamless 3D Clay Legs (Hip -> Knee -> Ankle)
  float dLegL = smin(
    sdRoundCone(p, lHip, lKnee, 0.102, 0.082),
    sdRoundCone(p, lKnee, lAnkle, 0.082, 0.064),
    0.04
  );
  float dLegR = smin(
    sdRoundCone(p, rHip, rKnee, 0.102, 0.082),
    sdRoundCone(p, rKnee, rAnkle, 0.082, 0.064),
    0.04
  );
  res = opU(res, HitInfo(min(dLegL, dLegR), 1.0, 6));

  // ========================================================================
  // 2. SPORTSWEAR: TOP (SHIRT / TANK) & SHORTS
  // ========================================================================
  float dTorso = sdRoundCone(p, pelvisCenter, chestCenter, 0.165, 0.185);
  if (uGender < 0.5) {
    // BOY: Orange T-Shirt with Short Sleeves
    vec3 lSleeveEnd = mix(lShoulder, lElbow, 0.46);
    vec3 rSleeveEnd = mix(rShoulder, rElbow, 0.46);
    float dSleeves = min(
      sdRoundCone(p, lShoulder, lSleeveEnd, 0.096, 0.088),
      sdRoundCone(p, rShoulder, rSleeveEnd, 0.096, 0.088)
    );
    dTorso = smin(dTorso, dSleeves, 0.035);
  } else {
    // GIRL: Sculpted Sport Tank Top
    float dBust = sdEllipsoid(p - (chestCenter + vec3(0.0, -0.02, 0.08)), vec3(0.16, 0.10, 0.10));
    dTorso = smin(dTorso, dBust, 0.04);
  }
  // Assign torso muscle ID based on front/back/height (CHEST=1, BACK=2, CORE=5)
  int torsoMuscle = (p.z < chestCenter.z - 0.02) ? 2 : ((p.y > pelvisCenter.y + 0.16) ? 1 : 5);
  res = opU(res, HitInfo(dTorso, 4.0, torsoMuscle));

  // Shorts (Pelvis + Upper Thigh Cuffs)
  vec3 lShortEnd = mix(lHip, lKnee, uGender > 0.5 ? 0.46 : 0.58);
  vec3 rShortEnd = mix(rHip, rKnee, uGender > 0.5 ? 0.46 : 0.58);
  float dShorts = smin(
    sdEllipsoid(p - pelvisCenter, vec3(0.195, 0.135, 0.165)),
    min(
      sdRoundCone(p, lHip, lShortEnd, 0.118, 0.106),
      sdRoundCone(p, rHip, rShortEnd, 0.118, 0.106)
    ),
    0.04
  );
  res = opU(res, HitInfo(dShorts, 5.0, 6));

  // ========================================================================
  // 3. WHITE SOCKS & CHUNKY 3D SNEAKERS (Auto-oriented to shin angle!)
  // ========================================================================
  vec3 lSockTop = mix(lAnkle, lKnee, 0.26);
  vec3 rSockTop = mix(rAnkle, rKnee, 0.26);
  float dSocks = min(
    sdRoundCone(p, lAnkle, lSockTop, 0.072, 0.074),
    sdRoundCone(p, rAnkle, rSockTop, 0.072, 0.074)
  );
  res = opU(res, HitInfo(dSocks, 6.0, 6));

  vec3 lCalfDir = normalize(lAnkle - lKnee);
  vec3 rCalfDir = normalize(rAnkle - rKnee);
  vec3 lFootDir = normalize(vec3(0.0, lCalfDir.z, -lCalfDir.y));
  vec3 rFootDir = normalize(vec3(0.0, rCalfDir.z, -rCalfDir.y));

  vec3 lToe = lAnkle + lFootDir * 0.165 + lCalfDir * 0.02;
  vec3 rToe = rAnkle + rFootDir * 0.165 + rCalfDir * 0.02;
  float dShoeUpper = min(
    sdRoundCone(p, lAnkle - lFootDir * 0.02, lToe, 0.082, 0.072),
    sdRoundCone(p, rAnkle - rFootDir * 0.02, rToe, 0.082, 0.072)
  );
  res = opU(res, HitInfo(dShoeUpper, 7.0, 6));

  // White Sneaker Laces & Cushioned Sole
  vec3 lMidShoe = mix(lAnkle, lToe, 0.50) - lCalfDir * 0.042;
  vec3 rMidShoe = mix(rAnkle, rToe, 0.50) - rCalfDir * 0.042;
  float dLaces = min(
    sdCapsule(p, lMidShoe + vec3(-0.042, 0.0, 0.0), lMidShoe + vec3(0.042, 0.0, 0.0), 0.018),
    sdCapsule(p, rMidShoe + vec3(-0.042, 0.0, 0.0), rMidShoe + vec3(0.042, 0.0, 0.0), 0.018)
  );

  float dShoeSole = min(
    sdRoundCone(p, lAnkle + lCalfDir * 0.048 - lFootDir * 0.025, lToe + lCalfDir * 0.042 + lFootDir * 0.015, 0.088, 0.080),
    sdRoundCone(p, rAnkle + rCalfDir * 0.048 - rFootDir * 0.025, rToe + rCalfDir * 0.042 + rFootDir * 0.015, 0.088, 0.080)
  );
  res = opU(res, HitInfo(min(dShoeSole, dLaces), 6.0, 6));

  // ========================================================================
  // 4. 3D CLAY HAIR (BOY PUFFY BANGS vs GIRL FLOWING PONYTAIL)
  // ========================================================================
  float dHairCap = sdEllipsoid(hp - vec3(0.0, 0.05, -0.035), vec3(0.24, 0.22, 0.23));
  // Cut away front face from hair cap
  dHairCap = smax(dHairCap, -(length(hp - vec3(0.0, -0.05, 0.14)) - 0.20), 0.03);

  if (uGender < 0.5) {
    // BOY: Puffy 3D Clay Parted Bangs & Back Tuft (Reference Images 2 & 3)
    float b1 = sdCapsule(hp, vec3(-0.14, 0.15, 0.12), vec3(-0.02, 0.20, 0.18), 0.068);
    float b2 = sdCapsule(hp, vec3( 0.01, 0.21, 0.14), vec3( 0.12, 0.17, 0.19), 0.076);
    float b3 = sdCapsule(hp, vec3( 0.12, 0.14, 0.12), vec3( 0.19, 0.07, 0.08), 0.058);
    float tuft = sdCapsule(hp, vec3(0.0, 0.18, -0.16), vec3(0.0, 0.25, -0.24), 0.042);
    float dBoyHair = smin(dHairCap, smin(smin(b1, b2, 0.04), smin(b3, tuft, 0.03), 0.04), 0.04);
    res = opU(res, HitInfo(dBoyHair, 2.0, 0));
  } else {
    // GIRL: Smooth Parted Bangs + Purple Scrunchie + S-Curved Bouncy Ponytail (Reference Image 1)
    float g1 = sdCapsule(hp, vec3(-0.02, 0.19, 0.16), vec3(-0.18, 0.08, 0.10), 0.062);
    float g2 = sdCapsule(hp, vec3( 0.02, 0.19, 0.16), vec3( 0.18, 0.08, 0.10), 0.062);
    float dGirlHair = smin(dHairCap, min(g1, g2), 0.04);

    // Ponytail S-curve behind head
    float sway = sin(t * 1.4) * 0.05;
    vec3 pTie = vec3(0.0, 0.10, -0.22);
    vec3 pMid1 = vec3(0.0, 0.22 + sway * 0.4, -0.38);
    vec3 pMid2 = vec3(0.0, 0.14 + sway * 0.8, -0.54);
    vec3 pTip  = vec3(0.0, 0.24 + sway, -0.66);

    float dPony = smin(
      sdRoundCone(hp, pTie, pMid1, 0.065, 0.115),
      smin(
        sdRoundCone(hp, pMid1, pMid2, 0.115, 0.085),
        sdRoundCone(hp, pMid2, pTip, 0.085, 0.032),
        0.05
      ),
      0.05
    );
    dGirlHair = smin(dGirlHair, dPony, 0.03);
    res = opU(res, HitInfo(dGirlHair, 2.0, 0));

    // Purple Scrunchie
    float dScrunchie = length(hp - pTie) - 0.068;
    res = opU(res, HitInfo(dScrunchie, 4.0, 0));
  }

  // ========================================================================
  // 5. CUTE EYES & EYEBROWS
  // ========================================================================
  vec3 eyeP = vec3(abs(hp.x) - 0.078, hp.y - 0.015, hp.z - 0.205);
  float dEyes = sdEllipsoid(eyeP, vec3(0.024, 0.036, 0.018));
  vec3 browP = vec3(abs(hp.x) - 0.082, hp.y - 0.082, hp.z - 0.202);
  float dBrows = sdCapsule(browP, vec3(-0.032, 0.0, 0.0), vec3(0.032, 0.006, 0.0), 0.014);
  res = opU(res, HitInfo(min(dEyes, dBrows), 3.0, 0));

  // ========================================================================
  // 6. PROPS: 3D HURDLE OR 3D DUMBBELLS
  // ========================================================================
  if (showHurdle) {
    float dBar = sdRoundBox(p - vec3(0.0, -0.36, 0.08), vec3(0.42, 0.042, 0.022), 0.015);
    res = opU(res, HitInfo(dBar, 6.0, 0));

    vec3 hpSym = vec3(abs(p.x) - 0.32, p.y, p.z);
    float dPost = sdCapsule(hpSym, vec3(0.0, -0.38, 0.08), vec3(0.0, -0.82, 0.08), 0.028);
    float dBase = sdCapsule(hpSym, vec3(0.0, -0.82, 0.14), vec3(0.0, -0.82, -0.26), 0.032);
    res = opU(res, HitInfo(min(dPost, dBase), 8.0, 0));
  }

  if (showDumbbells) {
    float dbL = min(
      sdCapsule(p, lWrist + vec3(-0.12, 0.0, 0.0), lWrist + vec3(0.12, 0.0, 0.0), 0.022),
      min(
        sdEllipsoid(p - (lWrist + vec3(-0.11, 0.0, 0.0)), vec3(0.038, 0.085, 0.085)),
        sdEllipsoid(p - (lWrist + vec3( 0.11, 0.0, 0.0)), vec3(0.038, 0.085, 0.085))
      )
    );
    float dbR = min(
      sdCapsule(p, rWrist + vec3(-0.12, 0.0, 0.0), rWrist + vec3(0.12, 0.0, 0.0), 0.022),
      min(
        sdEllipsoid(p - (rWrist + vec3(-0.11, 0.0, 0.0)), vec3(0.038, 0.085, 0.085)),
        sdEllipsoid(p - (rWrist + vec3( 0.11, 0.0, 0.0)), vec3(0.038, 0.085, 0.085))
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

  // Orbit Camera around Y-axis
  float cy = cos(uYaw);
  float sy = sin(uYaw);
  vec3 ro = vec3(sy * 2.55, 0.02, cy * 2.55);
  vec3 ta = vec3(0.0, -0.02, 0.0);

  vec3 cw = normalize(ta - ro);
  vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
  vec3 cv = cross(cu, cw);
  vec3 rd = normalize(uv.x * cu + uv.y * cv + 1.85 * cw);

  // Bounding sphere early exit for high speed
  float b = dot(ro, rd);
  float c = dot(ro, ro) - 1.35 * 1.35;
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
    }
  }

  // Raymarch 3D Clay Scene
  float t = 1.2;
  HitInfo hit = HitInfo(100.0, 0.0, 0);
  bool didHit = false;
  for (int i = 0; i < 56; i++) {
    vec3 p = ro + rd * t;
    hit = mapScene(p);
    if (hit.d < 0.0025) {
      didHit = true;
      break;
    }
    t += hit.d * 0.9;
    if (t > 4.0) break;
  }

  if (!didHit) {
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
    // 2.0 Hair (Dark Charcoal for Boy, Warm Chocolate Brown for Girl)
    baseCol = (uGender < 0.5) ? vec3(0.20, 0.19, 0.21) : vec3(0.32, 0.18, 0.14);
  } else if (hit.mat > 2.5 && hit.mat < 3.5) {
    // 3.0 Eyes & Brows (with cute white eye sparkle!)
    baseCol = vec3(0.10, 0.08, 0.08);
    roughness = 0.18;
    float sparkle = smoothstep(0.011, 0.005, length(vec2(abs(pos.x) - 0.072, pos.y - uHeadCenter.y - 0.022)));
    baseCol = mix(baseCol, vec3(1.0), sparkle);
  } else if (hit.mat > 3.5 && hit.mat < 4.5) {
    // 4.0 Top (Vibrant Orange Shirt for Boy, Lavender-Purple Tank for Girl)
    baseCol = (uGender < 0.5) ? vec3(0.98, 0.56, 0.22) : vec3(0.72, 0.50, 0.92);
  } else if (hit.mat > 4.5 && hit.mat < 5.5) {
    // 5.0 Shorts (Royal Blue Shorts for Boy, Coral-Orange Shorts for Girl)
    baseCol = (uGender < 0.5) ? vec3(0.23, 0.50, 0.96) : vec3(0.96, 0.42, 0.16);
  } else if (hit.mat > 5.5 && hit.mat < 6.5) {
    // 6.0 White Clay (Socks / Soles / Hurdle Top with dark stripes like Reference Image 1!)
    baseCol = vec3(0.96, 0.97, 0.99);
    if (uAction == 0 && pos.y > -0.42 && pos.y < -0.28 && abs(abs(pos.x) - 0.22) < 0.055) {
      baseCol = vec3(0.36, 0.40, 0.46);
    }
  } else if (hit.mat > 6.5 && hit.mat < 7.5) {
    // 7.0 Sneaker Upper
    baseCol = (uGender < 0.5) ? vec3(0.20, 0.46, 0.94) : vec3(0.64, 0.40, 0.88);
  } else if (hit.mat > 7.5) {
    // 8.0 Dark Grey Props
    baseCol = vec3(0.38, 0.42, 0.48);
  }

  // Muscle Recovery Thermal Subsurface Glow
  vec3 glowEmission = vec3(0.0);
  if (uShowGlow > 0.5 && hit.muscle > 0) {
    float mStatus = 0.0;
    if (hit.muscle == 1) mStatus = uMuscleStatus123.x;
    else if (hit.muscle == 2) mStatus = uMuscleStatus123.y;
    else if (hit.muscle == 3) mStatus = uMuscleStatus123.z;
    else if (hit.muscle == 4) mStatus = uMuscleStatus456.x;
    else if (hit.muscle == 5) mStatus = uMuscleStatus456.y;
    else if (hit.muscle == 6) mStatus = uMuscleStatus456.z;

    float pulse = 0.5 + 0.5 * sin(uTime * 5.0);
    if (mStatus > 1.5) {
      // FATIGUED (<45%): Pulsing Rose-Red Thermal Hotspot
      baseCol = mix(baseCol, vec3(0.98, 0.25, 0.38), 0.58 + 0.15 * pulse);
      glowEmission = vec3(0.45, 0.06, 0.12) * (0.6 + 0.4 * pulse);
    } else if (mStatus > 0.5) {
      // RECOVERING (45-84%): Warm Amber Glow
      baseCol = mix(baseCol, vec3(0.98, 0.68, 0.12), 0.48);
      glowEmission = vec3(0.28, 0.16, 0.02);
    } else if (hit.muscle == uSelectedMuscle) {
      // SELECTED & RECOVERED: Emerald Readiness Highlight
      baseCol = mix(baseCol, vec3(0.15, 0.85, 0.58), 0.38);
      glowEmission = vec3(0.05, 0.25, 0.15);
    }
  }

  // Blender 3-Point Studio Clay Lighting + Subsurface Scattering (SSS)
  vec3 keyLight = normalize(vec3(0.55 * cy + 0.65 * sy, 0.75, 0.65 * cy - 0.55 * sy));
  vec3 fillLight = normalize(vec3(-0.6 * cy, 0.25, 0.6 * sy));

  // Half-Lambert Soft Clay Diffuse (prevents harsh black shadows!)
  float ndl = dot(nor, keyLight);
  float wrapDiff = pow(ndl * 0.5 + 0.5, 1.35);

  // Warm Subsurface Scattering (gives skin & clay that soft, translucent Pixar warmth!)
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
    uHeadCenter: gl.getUniformLocation(program, 'uHeadCenter')
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
  let headY = 0.62
  if (actId === 5) headY = 0.62 + Math.sin(tAnim * 0.8) * 0.012
  else if (actId === 0) headY = 0.62 + 0.14 + (0.5 + 0.5 * Math.sin(tAnim * 0.9)) * 0.10
  else if (actId === 1) headY = 0.62 + Math.abs(Math.cos(tAnim * 1.4)) * 0.06
  else if (actId === 3) headY = 0.62 - (0.5 + 0.5 * Math.sin(tAnim * 1.1)) * 0.24

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
  gl.uniform3f(uniforms.uHeadCenter, 0.0, headY, 0.02)

  gl.drawArrays(gl.TRIANGLES, 0, 6)

  // Update 3D-projected floating pins
  const cosY = Math.cos(yaw.value)
  const sinY = Math.sin(yaw.value)
  const isStanding = actId === 5
  const pinAnchors = isStanding
    ? {
        SHOULDERS: { x: -0.30, y: 0.32, z: 0.05, frontOnly: false },
        CHEST: { x: 0.0, y: 0.25, z: 0.22, frontOnly: true },
        CORE: { x: 0.0, y: 0.06, z: 0.20, frontOnly: true },
        BACK: { x: 0.0, y: 0.24, z: -0.22, backOnly: true },
        ARMS: { x: 0.36, y: 0.06, z: 0.05, frontOnly: false },
        LEGS: { x: 0.25, y: -0.42, z: 0.06, frontOnly: false }
      }
    : {
        SHOULDERS: { x: -0.34, y: 0.36, z: 0.05, frontOnly: false },
        CHEST: { x: 0.0, y: 0.28, z: 0.24, frontOnly: true },
        CORE: { x: 0.0, y: 0.08, z: 0.22, frontOnly: true },
        BACK: { x: 0.0, y: 0.26, z: -0.24, backOnly: true },
        ARMS: { x: 0.42, y: 0.15, z: 0.08, frontOnly: false },
        LEGS: { x: 0.32, y: -0.42, z: 0.12, frontOnly: false }
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
