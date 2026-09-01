<template>
  <div class="pb-24 pt-4 px-4 max-w-lg mx-auto space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-black text-slate-900">飲食與營養記錄</h1>
        <p class="text-xs text-slate-400">純文字 AI 秒級解析 · 30天滾動省空間</p>
      </div>
      <button
        @click="openAIParsingModal('LUNCH')"
        class="py-2 px-3.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-xs font-black shadow-md shadow-orange-500/20 active:scale-95 transition-all flex items-center gap-1.5"
      >
        <Sparkles class="w-4 h-4" />
        <span>AI 文字記飲食</span>
      </button>
    </div>

    <!-- Date Navigation -->
    <div class="card-apple flex items-center justify-between py-2.5">
      <button @click="changeDate(-1)" class="p-1 text-slate-400 hover:text-slate-700">
        <ChevronLeft class="w-5 h-5" />
      </button>
      <div class="text-center">
        <div class="text-xs font-black text-slate-900">{{ selectedDateFormatted }}</div>
        <div v-if="isToday" class="text-[10px] text-emerald-600 font-bold">（今天）</div>
      </div>
      <button @click="changeDate(1)" class="p-1 text-slate-400 hover:text-slate-700" :disabled="isToday">
        <ChevronRight class="w-5 h-5" :class="{ 'opacity-30': isToday }" />
      </button>
    </div>

    <!-- Macro Rings Overview Card -->
    <NutritionRingCard :progress="nutritionStore.dailyProgress" />

    <!-- Weight Quick Card -->
    <div class="card-apple flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
          <Scale class="w-4 h-4" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-800">今日體重記錄</div>
          <div class="text-[10px] text-slate-400">
            目前：{{ authStore.profile?.current_weight_kg || '--' }} kg (目標 {{ authStore.profile?.target_weight_kg || '--' }} kg)
          </div>
        </div>
      </div>
      <button
        @click="showWeightModal = true"
        class="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs active:scale-95"
      >
        打卡體重
      </button>
    </div>

    <!-- Meals List by Type -->
    <div class="space-y-3">
      <div
        v-for="cat in mealCategories"
        :key="cat.key"
        class="card-apple space-y-2.5"
      >
        <div class="flex items-center justify-between pb-1.5 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="text-base">{{ cat.icon }}</span>
            <h3 class="text-xs font-bold text-slate-900">{{ cat.label }}</h3>
            <span class="text-[10px] text-slate-400 font-medium">({{ getCategoryTotalCals(cat.key) }} kcal)</span>
          </div>
          <button
            @click="openAIParsingModal(cat.key)"
            class="text-[11px] font-bold text-orange-600 hover:text-orange-700 flex items-center gap-0.5"
          >
            <Plus class="w-3.5 h-3.5" />
            <span>記這餐</span>
          </button>
        </div>

        <!-- Meals in this category -->
        <div v-if="getMealsByCategory(cat.key).length === 0" class="text-center py-2 text-[11px] text-slate-300">
          尚無紀錄
        </div>

        <div v-else class="space-y-1.5">
          <div
            v-for="m in getMealsByCategory(cat.key)"
            :key="m.id"
            class="p-2 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between"
          >
            <div>
              <div class="text-xs font-bold text-slate-800">{{ m.food_name }}</div>
              <div class="text-[10px] text-slate-400">
                P: {{ m.protein_g }}g · C: {{ m.carbs_g }}g · F: {{ m.fat_g }}g
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-black text-slate-800">{{ m.calories }} kcal</span>
              <button @click="deleteMeal(m.id)" class="text-slate-300 hover:text-rose-500 p-1">
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 30-Day Rolling Cleanup Utility Banner -->
    <div class="p-3.5 rounded-2xl bg-slate-100/80 border border-slate-200/60 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Database class="w-4 h-4 text-slate-500 flex-shrink-0" />
        <div class="text-[11px] text-slate-500">
          <span class="font-bold text-slate-700">30 天滾動歸檔：</span>
          歷史明細自動彙總為每日摘要，極致省空間。
        </div>
      </div>
      <button
        @click="handleRollingCleanup"
        :disabled="cleaning"
        class="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-200 text-slate-700 text-[10px] font-bold border border-slate-200 shadow-xs active:scale-95 whitespace-nowrap"
      >
        {{ cleaning ? '清理中...' : '手動歸檔' }}
      </button>
    </div>

    <!-- AI Text Parsing Modal -->
    <div
      v-if="showAIModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div class="bg-white w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-5 max-h-[85vh] overflow-y-auto space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center">
              <Sparkles class="w-4 h-4" />
            </div>
            <h3 class="font-black text-slate-900 text-base">AI 純文字飲食解析</h3>
          </div>
          <button @click="showAIModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">用餐分類</label>
            <div class="grid grid-cols-4 gap-1.5">
              <button
                v-for="c in mealCategories"
                :key="c.key"
                @click="targetMealType = c.key"
                class="py-1.5 text-xs font-bold rounded-xl transition-all"
                :class="targetMealType === c.key ? 'bg-orange-500 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              >
                {{ c.label }}
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">
              輸入吃了什麼（自然語言描述，不存圖片零空間負擔）
            </label>
            <textarea
              v-model="dietTextInput"
              rows="3"
              placeholder="例如：全家烤雞胸肉 1 片 + 蒸地瓜 150g + 無糖高纖豆漿 400ml"
              class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-orange-500"
            ></textarea>
          </div>

          <!-- Quick presets pills -->
          <div class="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
            <button
              v-for="p in presetPills"
              :key="p"
              @click="dietTextInput = p"
              class="px-2.5 py-1 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600 hover:bg-orange-50 hover:text-orange-700 whitespace-nowrap border border-slate-200/60"
            >
              {{ p }}
            </button>
          </div>

          <button
            @click="parseWithAI"
            :disabled="parsingAI || !dietTextInput.trim()"
            class="w-full py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-extrabold text-xs shadow-sm active:scale-95 transition-all flex items-center justify-center gap-1.5"
          >
            <Sparkles class="w-4 h-4" :class="{ 'animate-spin': parsingAI }" />
            <span>{{ parsingAI ? 'Gemini 正在精算營養素...' : '✨ 開始 AI 智能計算' }}</span>
          </button>

          <!-- Parsed Result Review & Editable Fields -->
          <div v-if="parsedResult" class="p-3.5 rounded-2xl bg-orange-50/60 border border-orange-200 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-black text-orange-900">{{ parsedResult.summary_name }}</span>
              <span class="text-xs font-black text-orange-600">{{ parsedResult.total_calories }} kcal</span>
            </div>

            <!-- Editable fields -->
            <div class="grid grid-cols-3 gap-2 text-center">
              <div>
                <span class="text-[10px] text-slate-500 font-bold">蛋白質 (g)</span>
                <input
                  v-model.number="parsedResult.total_protein_g"
                  type="number"
                  class="w-full text-center py-1 bg-white border border-orange-200 rounded-lg text-xs font-bold text-emerald-700"
                />
              </div>
              <div>
                <span class="text-[10px] text-slate-500 font-bold">碳水 (g)</span>
                <input
                  v-model.number="parsedResult.total_carbs_g"
                  type="number"
                  class="w-full text-center py-1 bg-white border border-orange-200 rounded-lg text-xs font-bold text-blue-700"
                />
              </div>
              <div>
                <span class="text-[10px] text-slate-500 font-bold">脂肪 (g)</span>
                <input
                  v-model.number="parsedResult.total_fat_g"
                  type="number"
                  class="w-full text-center py-1 bg-white border border-orange-200 rounded-lg text-xs font-bold text-amber-700"
                />
              </div>
            </div>

            <button
              @click="submitParsedMeal"
              class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs shadow-sm active:scale-95 transition-all"
            >
              ✅ 確認寫入今日飲食
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Weight Record Modal -->
    <div
      v-if="showWeightModal"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white w-full max-w-sm rounded-3xl p-5 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between pb-2 border-b border-slate-100">
          <h3 class="font-black text-slate-900 text-base">記錄今日體重</h3>
          <button @click="showWeightModal = false" class="p-1 rounded-full text-slate-400 hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">體重 (kg)</label>
            <input
              v-model.number="inputWeight"
              type="number"
              step="0.1"
              placeholder="例如：70.5"
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-black text-slate-900 focus:outline-none focus:border-brand-500 text-center"
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">體脂率 %（可選）</label>
            <input
              v-model.number="inputBodyFat"
              type="number"
              step="0.1"
              placeholder="例如：15.2"
              class="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-center focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2">
          <button
            @click="submitWeight"
            class="flex-1 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-extrabold text-xs shadow-sm active:scale-95"
          >
            儲存體重
          </button>
          <button
            @click="showWeightModal = false"
            class="py-2.5 px-4 rounded-xl bg-slate-100 text-slate-600 text-xs font-bold hover:bg-slate-200"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Sparkles, ChevronLeft, ChevronRight, Scale, Plus, Trash2, Database, X
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useNutritionStore } from '@/stores/nutrition'
import { aiAPI, nutritionAPI } from '@/api/client'
import NutritionRingCard from '@/components/NutritionRingCard.vue'

const authStore = useAuthStore()
const nutritionStore = useNutritionStore()

const currentDate = ref(new Date())
const showAIModal = ref(false)
const targetMealType = ref('LUNCH')
const dietTextInput = ref('')
const parsingAI = ref(false)
const parsedResult = ref(null)

const showWeightModal = ref(false)
const inputWeight = ref(authStore.profile?.current_weight_kg || 70)
const inputBodyFat = ref(authStore.profile?.body_fat_percentage || null)
const cleaning = ref(false)

const mealCategories = [
  { key: 'BREAKFAST', label: '早餐', icon: '🍳' },
  { key: 'LUNCH', label: '午餐', icon: '🍱' },
  { key: 'DINNER', label: '晚餐', icon: '🍲' },
  { key: 'SNACK', label: '點心/補給', icon: '🥛' }
]

const presetPills = [
  '全家烤雞胸肉 1 片 + 蒸地瓜 150g + 無糖豆漿',
  '超商大握便當 + 2 顆茶葉蛋',
  '乳清蛋白 1 份 (30g) + 香蕉 1 根',
  '牛肉麵大碗 + 燙青菜 1 份'
]

const dateParam = computed(() => {
  const d = currentDate.value
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
})

const selectedDateFormatted = computed(() => {
  const d = currentDate.value
  return `${d.getMonth() + 1}月${d.getDate()}日 (${['週日','週一','週二','週三','週四','週五','週六'][d.getDay()]})`
})

const isToday = computed(() => {
  const today = new Date()
  return currentDate.value.toDateString() === today.toDateString()
})

function changeDate(days) {
  const d = new Date(currentDate.value)
  d.setDate(d.getDate() + days)
  currentDate.value = d
  nutritionStore.fetchTodayProgress(dateParam.value)
}

function getMealsByCategory(type) {
  if (!nutritionStore.dailyProgress?.meals) return []
  return nutritionStore.dailyProgress.meals.filter(m => m.meal_type === type)
}

function getCategoryTotalCals(type) {
  return getMealsByCategory(type).reduce((acc, m) => acc + m.calories, 0)
}

function openAIParsingModal(categoryKey) {
  targetMealType.value = categoryKey
  dietTextInput.value = ''
  parsedResult.value = null
  showAIModal.value = true
}

async function parseWithAI() {
  if (!dietTextInput.value.trim()) return
  parsingAI.value = true
  try {
    const res = await aiAPI.parseDiet(dietTextInput.value, targetMealType.value)
    parsedResult.value = res.data
  } catch (err) {
    alert('AI 解析暫時失敗，請手動確認數值')
  } finally {
    parsingAI.value = false
  }
}

async function submitParsedMeal() {
  if (!parsedResult.value) return
  try {
    await nutritionStore.addMeal({
      meal_type: targetMealType.value,
      food_name: parsedResult.value.summary_name || dietTextInput.value,
      calories: parsedResult.value.total_calories,
      protein_g: parsedResult.value.total_protein_g,
      carbs_g: parsedResult.value.total_carbs_g,
      fat_g: parsedResult.value.total_fat_g,
      meal_date: dateParam.value
    })
    showAIModal.value = false
    parsedResult.value = null
  } catch (err) {
    alert('儲存失敗，請稍後重試')
  }
}

async function deleteMeal(id) {
  try {
    await nutritionStore.deleteMeal(id)
  } catch (err) {
    alert('刪除失敗')
  }
}

async function submitWeight() {
  if (!inputWeight.value) return
  try {
    await nutritionStore.recordWeight({
      weight_kg: Number(inputWeight.value),
      body_fat_pct: inputBodyFat.value ? Number(inputBodyFat.value) : null,
      recorded_date: dateParam.value
    })
    showWeightModal.value = false
    authStore.fetchMe()
    alert('體重已成功記錄！')
  } catch (err) {
    alert('記錄失敗')
  }
}

async function handleRollingCleanup() {
  cleaning.value = true
  try {
    const res = await nutritionAPI.cleanup30d()
    alert(res.data.message || '滾動歸檔完成！')
  } catch (err) {
    alert('歸檔執行失敗')
  } finally {
    cleaning.value = false
  }
}

onMounted(() => {
  nutritionStore.fetchTodayProgress(dateParam.value)
})
</script>
