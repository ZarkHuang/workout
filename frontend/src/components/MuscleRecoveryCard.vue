<template>
  <div class="card-apple">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
          <Activity class="w-4 h-4" />
        </div>
        <h3 class="font-bold text-slate-800 text-sm">肌肉修復狀態熱力圖</h3>
      </div>
      <button
        @click="$emit('refresh')"
        class="text-slate-400 hover:text-slate-600 text-xs flex items-center gap-1"
      >
        <RotateCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" />
      </button>
    </div>

    <!-- Recommendations summary pills -->
    <div v-if="overview?.recommended_focus?.length" class="mb-4 p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-start gap-2">
      <Sparkles class="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
      <div class="text-xs text-emerald-900 leading-relaxed">
        <span class="font-bold text-emerald-800">今日推薦進攻部位：</span>
        <span class="font-medium">{{ overview.recommended_focus.join('、') }}</span>
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
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs font-bold text-slate-800">{{ getShortLabel(m.label_zh) }}</span>
          <span
            class="text-[10px] font-bold px-1.5 py-0.2 rounded-full"
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
        <div class="text-[10px] text-slate-500 flex items-center justify-between">
          <span>{{ getStatusText(m.status) }}</span>
          <span v-if="m.hours_since_last_trained !== null">{{ m.hours_since_last_trained }}h 前</span>
          <span v-else>未紀錄</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Activity, RotateCw, Sparkles } from 'lucide-vue-next'

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

defineEmits(['refresh'])

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
