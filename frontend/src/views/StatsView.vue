<template>
  <div class="pb-24 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header -->
    <div>
      <h1 class="text-xl font-black text-slate-900">體態與肌力趨勢</h1>
      <p class="text-xs text-slate-400">7天體重平滑曲線 · 1RM 肌力突破 · 訓練量分析</p>
    </div>

    <!-- 1. Weight Trend Curve Card -->
    <div class="card-apple space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <TrendingUp class="w-4 h-4" />
          </div>
          <h3 class="font-bold text-slate-800 text-sm">體重趨勢 (7 天平滑)</h3>
        </div>
        <span class="text-xs font-bold text-slate-500">
          目前 {{ authStore.profile?.current_weight_kg || '--' }} kg
        </span>
      </div>

      <div class="h-48 relative">
        <div v-if="weightChartData.labels.length === 0" class="h-full flex items-center justify-center text-xs text-slate-400">
          尚無足夠體重紀錄，請至飲食頁面打卡體重
        </div>
        <Line v-else :data="weightChartData" :options="chartOptions" />
      </div>
    </div>

    <!-- 2. 1RM Strength Progression Curve Card -->
    <div class="card-apple space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Flame class="w-4 h-4" />
          </div>
          <h3 class="font-bold text-slate-800 text-sm">核心動作 1RM 肌力進步曲線</h3>
        </div>
      </div>

      <!-- Exercise select tabs -->
      <div v-if="availableExerciseNames.length > 0" class="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        <button
          v-for="name in availableExerciseNames"
          :key="name"
          @click="selectedExerciseName = name"
          class="px-2.5 py-1 rounded-full text-[10px] font-bold whitespace-nowrap transition-all"
          :class="selectedExerciseName === name ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
        >
          {{ name }}
        </button>
      </div>

      <div class="h-48 relative">
        <div v-if="availableExerciseNames.length === 0" class="h-full flex items-center justify-center text-xs text-slate-400">
          完成更多訓練後即可繪製 1RM 突破曲線
        </div>
        <Line v-else :data="oneRmChartData" :options="chartOptions" />
      </div>
    </div>

    <!-- 3. Today Macro Distribution Doughnut Card -->
    <div class="card-apple space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center">
            <PieChart class="w-4 h-4" />
          </div>
          <h3 class="font-bold text-slate-800 text-sm">宏觀營養熱量佔比</h3>
        </div>
      </div>

      <div class="h-44 relative flex items-center justify-center">
        <Doughnut :data="macroDoughnutData" :options="doughnutOptions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Line, Doughnut } from 'vue-chartjs'
import { TrendingUp, Flame, PieChart } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useNutritionStore } from '@/stores/nutrition'
import { workoutsAPI } from '@/api/client'

const authStore = useAuthStore()
const nutritionStore = useNutritionStore()

const strengthTrends = ref({})
const selectedExerciseName = ref('')

const availableExerciseNames = computed(() => {
  return Object.keys(strengthTrends.value)
})

// Weight Chart Data
const weightChartData = computed(() => {
  const logs = [...nutritionStore.weightLogs].reverse()
  const labels = logs.map(l => {
    const d = new Date(l.recorded_date)
    return `${d.getMonth() + 1}/${d.getDate()}`
  })
  const data = logs.map(l => l.weight_kg)

  return {
    labels,
    datasets: [
      {
        label: '體重 (kg)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderColor: '#10B981',
        pointBackgroundColor: '#10B981',
        pointRadius: 4,
        tension: 0.35,
        fill: true,
        data
      }
    ]
  }
})

// 1RM Chart Data
const oneRmChartData = computed(() => {
  const exName = selectedExerciseName.value || availableExerciseNames.value[0]
  const records = strengthTrends.value[exName] || []
  
  const labels = records.map(r => r.date)
  const data = records.map(r => r.estimated_1rm)

  return {
    labels,
    datasets: [
      {
        label: `${exName} 1RM (kg)`,
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderColor: '#3B82F6',
        pointBackgroundColor: '#3B82F6',
        pointRadius: 4,
        tension: 0.3,
        fill: true,
        data
      }
    ]
  }
})

// Macro Doughnut Data
const macroDoughnutData = computed(() => {
  const p = (nutritionStore.dailyProgress?.consumed_protein_g || 0) * 4
  const c = (nutritionStore.dailyProgress?.consumed_carbs_g || 0) * 4
  const f = (nutritionStore.dailyProgress?.consumed_fat_g || 0) * 9

  const total = p + c + f
  if (total === 0) {
    return {
      labels: ['蛋白質', '碳水化合物', '脂肪'],
      datasets: [{ data: [30, 50, 20], backgroundColor: ['#E2E8F0', '#E2E8F0', '#E2E8F0'] }]
    }
  }

  return {
    labels: ['蛋白質 (P)', '碳水化合物 (C)', '脂肪 (F)'],
    datasets: [
      {
        data: [p, c, f],
        backgroundColor: ['#10B981', '#3B82F6', '#F59E0B'],
        borderWidth: 2,
        borderColor: '#FFFFFF'
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: { grid: { display: false } },
    y: { grid: { color: '#F1F5F9' } }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
  },
  cutout: '70%'
}

async function fetchTrends() {
  try {
    const res = await workoutsAPI.getStrengthTrends()
    strengthTrends.value = res.data.trends || {}
    if (availableExerciseNames.value.length > 0 && !selectedExerciseName.value) {
      selectedExerciseName.value = availableExerciseNames.value[0]
    }
  } catch (err) {
    console.error('Failed to fetch strength trends:', err)
  }
}

onMounted(() => {
  nutritionStore.fetchWeightLogs()
  nutritionStore.fetchTodayProgress()
  fetchTrends()
})
</script>
