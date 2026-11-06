<template>
  <div class="card-apple">
    <div class="flex items-center justify-between gap-2 mb-3">
      <div class="flex items-center gap-2 min-w-0">
        <div class="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
          <Activity class="w-4 h-4" />
        </div>
        <div class="min-w-0">
          <h3 class="font-bold text-slate-800 text-sm whitespace-nowrap truncate">3D 肌肉修復與訓練熱點圖</h3>
          <p class="text-[10px] text-slate-400 truncate">即時顯示各部位疲勞熱點與超補償進度</p>
        </div>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <button
          type="button"
          @click="show3DAvatar = !show3DAvatar"
          class="px-2.5 py-1 rounded-lg text-[10px] font-extrabold transition-all border whitespace-nowrap shrink-0"
          :class="show3DAvatar ? 'bg-slate-900 text-white border-slate-900' : 'bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200'"
        >
          {{ show3DAvatar ? '🎭 隱藏 3D' : '🎭 展開 3D' }}
        </button>
        <button
          @click="$emit('refresh')"
          class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 text-xs flex items-center gap-1 shrink-0"
          title="重新整理修復狀態"
        >
          <RotateCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
        </button>
      </div>
    </div>

    <!-- 3D Cute Muscular Hotspot Figurine Stage -->
    <div v-if="show3DAvatar" class="mb-3.5">
      <MuscleAvatar3D
        :muscles="overview?.muscles || []"
        :suggested-aura="overview?.suggested_aura"
        :streak-days="overview?.streak_days || 0"
        @recommend-split="$emit('recommend-split', $event)"
      />
    </div>

    <!-- Recommendations & Avoid summary pills -->
    <div class="space-y-2 mb-3.5">
      <div v-if="overview?.recommended_focus?.length" class="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-start gap-2">
        <Sparkles class="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div class="text-xs text-emerald-900 leading-relaxed">
          <span class="font-bold text-emerald-800">今日推薦進攻部位：</span>
          <span class="font-medium">{{ overview.recommended_focus.join('、') }}</span>
        </div>
      </div>

      <div v-if="overview?.avoid_muscles?.length" class="p-2.5 rounded-xl bg-rose-50/80 border border-rose-200/80 flex items-start gap-2">
        <span class="text-xs leading-none mt-0.5">⛔</span>
        <div class="text-xs text-rose-900 leading-relaxed">
          <span class="font-bold text-rose-800">疲勞保護（建議休息避免高強度訓練）：</span>
          <span class="font-semibold">{{ overview.avoid_muscles.join('、') }}</span>
        </div>
      </div>
    </div>

    <!-- 6 Muscle Grid -->
    <div class="grid grid-cols-2 gap-2.5">
      <div
        v-for="m in overview?.muscles"
        :key="m.muscle_group"
        class="p-2.5 rounded-xl border transition-all"
        :class="getMuscleCardClass(m.status)"
      >
        <div class="flex items-center justify-between gap-1 mb-1.5">
          <span class="text-xs font-bold text-slate-800 whitespace-nowrap truncate">{{ getShortLabel(m.label_zh) }}</span>
          <span
            class="text-[10px] font-bold px-1.5 py-0.2 rounded-full whitespace-nowrap shrink-0"
            :class="getStatusBadgeClass(m.status)"
          >
            {{ m.recovery_percentage }}%
          </span>
        </div>

        <!-- Progress bar -->
        <div class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-1.5">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="getProgressBarClass(m.status)"
            :style="{ width: `${m.recovery_percentage}%` }"
          ></div>
        </div>

        <!-- Info note -->
        <div class="text-[10px] text-slate-500 flex items-center justify-between gap-1 whitespace-nowrap">
          <span>{{ getStatusText(m.status) }}</span>
          <span v-if="m.hours_since_last_trained !== null">{{ m.hours_since_last_trained }}h 前練</span>
          <span v-else>未紀錄</span>
        </div>

        <!-- Remaining recovery countdown -->
        <div
          v-if="m.hours_until_recovered && m.hours_until_recovered > 0"
          class="mt-1 pt-1 border-t border-slate-200/60 text-[10px] font-bold flex items-center justify-between gap-1 whitespace-nowrap"
          :class="m.status === 'FATIGUED' ? 'text-rose-700' : 'text-amber-700'"
        >
          <span>⏳ 再休 {{ m.hours_until_recovered }}h</span>
          <span class="text-[9px] font-normal text-slate-400">週期 {{ m.target_recovery_hours || 48 }}h</span>
        </div>
        <div
          v-else-if="m.hours_since_last_trained !== null"
          class="mt-1 pt-1 border-t border-emerald-200/50 text-[10px] font-semibold text-emerald-700 flex items-center justify-between gap-1 whitespace-nowrap"
        >
          <span>✅ 超補償完成</span>
          <span class="text-[9px] font-normal text-slate-400">週期 {{ m.target_recovery_hours || 48 }}h</span>
        </div>
      </div>
    </div>

    <!-- Scientific Recovery Footnote -->
    <div class="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-400 leading-relaxed flex items-center justify-between flex-wrap gap-1">
      <span>🧬 科學修復週期：核心 24h · 肩/手 36h · 胸/背 48-60h · 臀腿 72h</span>
      <span class="text-slate-500 font-semibold">達 85% 即可高強度訓練</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Activity, RotateCw, Sparkles } from 'lucide-vue-next'
import MuscleAvatar3D from '@/components/MuscleAvatar3D.vue'

const props = defineProps({
  overview: {
    type: Object,
    default: () => ({ muscles: [], recommended_focus: [], avoid_muscles: [] })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'recommend-split'])

const show3DAvatar = ref(true)

function getShortLabel(labelZh) {
  if (!labelZh) return ''
  return labelZh.split(' ')[0]
}

function getStatusText(status) {
  if (status === 'RECOVERED') return '已完全修復'
  if (status === 'RECOVERING') return '組織修復中'
  return '肌肉疲勞中'
}

function getMuscleCardClass(status) {
  if (status === 'RECOVERED') return 'bg-emerald-50/40 border-emerald-100 hover:border-emerald-200'
  if (status === 'RECOVERING') return 'bg-amber-50/40 border-amber-100 hover:border-amber-200'
  return 'bg-rose-50/40 border-rose-100 hover:border-rose-200'
}

function getStatusBadgeClass(status) {
  if (status === 'RECOVERED') return 'bg-emerald-100 text-emerald-800'
  if (status === 'RECOVERING') return 'bg-amber-100 text-amber-800'
  return 'bg-rose-100 text-rose-800'
}

function getProgressBarClass(status) {
  if (status === 'RECOVERED') return 'bg-emerald-500'
  if (status === 'RECOVERING') return 'bg-amber-500'
  return 'bg-rose-500'
}
</script>
