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
      class="fixed bottom-[calc(4rem+env(safe-area-inset-bottom,20px)+16px)] left-3.5 right-3.5 max-w-lg mx-auto z-50 bg-slate-900/95 text-white rounded-2xl p-3 shadow-2xl backdrop-blur-md border border-slate-700/60 flex flex-col gap-2 select-none"
    >
      <div class="flex items-center justify-between gap-2">
        <!-- Timer Info & Progress -->
        <div class="flex items-center gap-2.5 min-w-0 flex-1">
          <div class="relative w-9 h-9 flex items-center justify-center flex-shrink-0">
            <!-- Circular SVG Progress -->
            <svg class="w-9 h-9 transform -rotate-90">
              <circle
                cx="18"
                cy="18"
                r="14"
                stroke="currentColor"
                stroke-width="3"
                class="text-slate-700"
                fill="transparent"
              />
              <circle
                cx="18"
                cy="18"
                r="14"
                stroke="currentColor"
                stroke-width="3"
                class="text-emerald-400 transition-all duration-1000 ease-linear"
                fill="transparent"
                :stroke-dasharray="88"
                :stroke-dashoffset="88 - (88 * (workoutStore.timerRemainingSeconds / workoutStore.timerTotalSeconds))"
                stroke-linecap="round"
              />
            </svg>
            <Timer class="w-3.5 h-3.5 text-emerald-400 absolute animate-pulse" />
          </div>

          <div class="min-w-0">
            <div class="text-[10px] font-bold text-slate-300 flex items-center gap-1 whitespace-nowrap">
              <span>組間休息</span>
              <span class="text-[9px] text-emerald-400 font-normal">⏱️ 背景計時中</span>
            </div>
            <div class="text-lg font-black font-mono text-emerald-400 tracking-wider">
              {{ formattedTime }}
            </div>
          </div>
        </div>

        <!-- Quick Stepper & Skip Buttons -->
        <div class="flex items-center gap-1.5 flex-shrink-0">
          <button
            @click="workoutStore.addTimerSeconds(-15)"
            class="px-2 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-black text-slate-300 active:scale-95 transition-all border border-slate-700/80 whitespace-nowrap flex-shrink-0"
            title="減少 15 秒"
          >
            -15s
          </button>
          <button
            @click="workoutStore.addTimerSeconds(30)"
            class="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-black text-emerald-300 active:scale-95 transition-all border border-slate-700/80 whitespace-nowrap flex-shrink-0"
            title="增加 30 秒"
          >
            +30s
          </button>
          <button
            @click="workoutStore.stopRestTimer()"
            class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-black text-white shadow-sm active:scale-95 transition-all whitespace-nowrap flex-shrink-0"
          >
            跳過
          </button>
        </div>
      </div>

      <!-- Notification Permission Prompt Bar (if not yet granted) -->
      <div
        v-if="showNotificationPrompt"
        class="bg-emerald-950/80 border border-emerald-500/40 rounded-xl p-2 flex items-center justify-between text-[10px] text-emerald-200"
      >
        <div class="flex items-center gap-1.5 min-w-0">
          <Bell class="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
          <span class="truncate">開啟通知，滑開 App 或待機時提醒開練！</span>
        </div>
        <button
          @click="enableNotifications"
          class="px-2 py-0.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] whitespace-nowrap flex-shrink-0 active:scale-95 transition-all"
        >
          立即開啟
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { Timer, Bell } from 'lucide-vue-next'
import { useWorkoutStore } from '@/stores/workout'
import { requestNotificationPermission, getNotificationPermission } from '@/utils/notifications'

const workoutStore = useWorkoutStore()
const notificationPermission = ref(getNotificationPermission())

const showNotificationPrompt = computed(() => {
  return notificationPermission.value === 'default'
})

async function enableNotifications() {
  const perm = await requestNotificationPermission()
  notificationPermission.value = perm
  if (perm === 'granted') {
    alert('🔔 休息提醒通知已成功啟用！滑開 App 或待機時也能收到提醒。')
  }
}

const formattedTime = computed(() => {
  const sec = workoutStore.timerRemainingSeconds
  const mins = Math.floor(sec / 60)
  const remainingSec = sec % 60
  return `${mins.toString().padStart(2, '0')}:${remainingSec.toString().padStart(2, '0')}`
})

onMounted(() => {
  notificationPermission.value = getNotificationPermission()
})
</script>
