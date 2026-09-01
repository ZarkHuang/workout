<template>
  <transition
    enter-active-class="transform transition ease-out duration-300"
    enter-from-class="translate-y-full opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transform transition ease-in duration-200"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-full opacity-0"
  >
    <div
      v-if="workoutStore.isTimerActive"
      class="fixed bottom-20 left-4 right-4 max-w-lg mx-auto z-50 bg-slate-900/95 text-white rounded-2xl p-3.5 shadow-2xl backdrop-blur-md border border-slate-700/60 flex items-center justify-between"
    >
      <!-- Timer Info & Progress -->
      <div class="flex items-center gap-3">
        <div class="relative w-10 h-10 flex items-center justify-center">
          <!-- Circular SVG Progress -->
          <svg class="w-10 h-10 transform -rotate-90">
            <circle
              cx="20"
              cy="20"
              r="16"
              stroke="currentColor"
              stroke-width="3"
              class="text-slate-700"
              fill="transparent"
            />
            <circle
              cx="20"
              cy="20"
              r="16"
              stroke="currentColor"
              stroke-width="3"
              class="text-emerald-400 transition-all duration-1000 ease-linear"
              fill="transparent"
              :stroke-dasharray="100.5"
              :stroke-dashoffset="100.5 - (100.5 * (workoutStore.timerRemainingSeconds / workoutStore.timerTotalSeconds))"
              stroke-linecap="round"
            />
          </svg>
          <Timer class="w-4 h-4 text-emerald-400 absolute" />
        </div>

        <div>
          <div class="text-[11px] font-medium text-slate-400 tracking-wide">組間休息倒數</div>
          <div class="text-xl font-bold font-mono text-emerald-400">
            {{ formattedTime }}
          </div>
        </div>
      </div>

      <!-- Quick Control Buttons -->
      <div class="flex items-center gap-2">
        <button
          @click="workoutStore.addTimerSeconds(30)"
          class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 active:scale-95 transition-all"
        >
          +30s
        </button>
        <button
          @click="workoutStore.stopRestTimer()"
          class="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-sm active:scale-95 transition-all"
        >
          跳過
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'
import { Timer } from 'lucide-vue-next'
import { useWorkoutStore } from '@/stores/workout'

const workoutStore = useWorkoutStore()

const formattedTime = computed(() => {
  const sec = workoutStore.timerRemainingSeconds
  const mins = Math.floor(sec / 60)
  const remainingSec = sec % 60
  return `${mins.toString().padStart(2, '0')}:${remainingSec.toString().padStart(2, '0')}`
})
</script>
