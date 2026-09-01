<template>
  <div class="card-apple">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center">
          <Utensils class="w-4 h-4" />
        </div>
        <h3 class="font-bold text-slate-800 text-sm">今日宏觀營養進度</h3>
      </div>
      <router-link to="/diet" class="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-0.5">
        記飲食
        <ChevronRight class="w-3.5 h-3.5" />
      </router-link>
    </div>

    <!-- Calories Hero Progress -->
    <div class="p-3.5 rounded-2xl bg-gradient-to-r from-orange-50/60 to-amber-50/60 border border-orange-100/80 mb-3.5 flex items-center justify-between">
      <div>
        <div class="text-[11px] font-semibold text-orange-900/80 mb-0.5">今日熱量攝取</div>
        <div class="flex items-baseline gap-1.5">
          <span class="text-2xl font-black text-slate-900">{{ progress?.consumed_calories || 0 }}</span>
          <span class="text-xs text-slate-500 font-medium">/ {{ progress?.target_calories || 2400 }} kcal</span>
        </div>
      </div>
      <div class="text-right">
        <div class="text-[11px] font-semibold text-slate-500 mb-0.5">剩餘額度</div>
        <div
          class="text-lg font-extrabold"
          :class="remainingKcal >= 0 ? 'text-emerald-600' : 'text-rose-600'"
        >
          {{ remainingKcal >= 0 ? `${remainingKcal} kcal` : `超標 ${Math.abs(remainingKcal)}` }}
        </div>
      </div>
    </div>

    <!-- 3 Macros Bars -->
    <div class="grid grid-cols-3 gap-2 text-center">
      <!-- Protein -->
      <div class="p-2 rounded-xl bg-slate-50 border border-slate-100">
        <div class="text-[10px] font-bold text-slate-500 mb-1">蛋白質 (P)</div>
        <div class="text-xs font-black text-emerald-700 mb-1">
          {{ progress?.consumed_protein_g || 0 }} <span class="text-[10px] font-normal text-slate-400">/ {{ progress?.target_protein_g || 140 }}g</span>
        </div>
        <div class="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-emerald-500 rounded-full transition-all duration-500"
            :style="{ width: `${Math.min(100, ((progress?.consumed_protein_g || 0) / (progress?.target_protein_g || 1)) * 100)}%` }"
          ></div>
        </div>
      </div>

      <!-- Carbs -->
      <div class="p-2 rounded-xl bg-slate-50 border border-slate-100">
        <div class="text-[10px] font-bold text-slate-500 mb-1">碳水 (C)</div>
        <div class="text-xs font-black text-blue-700 mb-1">
          {{ progress?.consumed_carbs_g || 0 }} <span class="text-[10px] font-normal text-slate-400">/ {{ progress?.target_carbs_g || 280 }}g</span>
        </div>
        <div class="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-blue-500 rounded-full transition-all duration-500"
            :style="{ width: `${Math.min(100, ((progress?.consumed_carbs_g || 0) / (progress?.target_carbs_g || 1)) * 100)}%` }"
          ></div>
        </div>
      </div>

      <!-- Fat -->
      <div class="p-2 rounded-xl bg-slate-50 border border-slate-100">
        <div class="text-[10px] font-bold text-slate-500 mb-1">脂肪 (F)</div>
        <div class="text-xs font-black text-amber-700 mb-1">
          {{ progress?.consumed_fat_g || 0 }} <span class="text-[10px] font-normal text-slate-400">/ {{ progress?.target_fat_g || 65 }}g</span>
        </div>
        <div class="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-amber-500 rounded-full transition-all duration-500"
            :style="{ width: `${Math.min(100, ((progress?.consumed_fat_g || 0) / (progress?.target_fat_g || 1)) * 100)}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Utensils, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  progress: {
    type: Object,
    default: null
  }
})

const remainingKcal = computed(() => {
  if (!props.progress) return 2400
  return (props.progress.target_calories || 0) - (props.progress.consumed_calories || 0)
})
</script>
