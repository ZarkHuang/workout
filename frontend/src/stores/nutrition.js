import { defineStore } from 'pinia'
import { ref } from 'vue'
import { nutritionAPI } from '@/api/client'

export const useNutritionStore = defineStore('nutrition', () => {
  const dailyProgress = ref(null)
  const weightLogs = ref([])
  const loading = ref(false)
  const lastQueriedDate = ref(null)

  async function fetchTodayProgress(dateStr = null) {
    loading.value = true
    const target = dateStr || lastQueriedDate.value || null
    if (dateStr) {
      lastQueriedDate.value = dateStr
    }
    try {
      const res = await nutritionAPI.getProgress(target)
      dailyProgress.value = res.data
      return res.data
    } catch (err) {
      console.error('Failed to fetch nutrition progress:', err)
    } finally {
      loading.value = false
    }
  }

  async function addMeal(mealData) {
    try {
      const res = await nutritionAPI.addMeal(mealData)
      await fetchTodayProgress(mealData.meal_date || lastQueriedDate.value)
      return res.data
    } catch (err) {
      throw err
    }
  }

  async function updateMeal(mealId, mealData) {
    try {
      const res = await nutritionAPI.updateMeal(mealId, mealData)
      await fetchTodayProgress(mealData.meal_date || lastQueriedDate.value)
      return res.data
    } catch (err) {
      throw err
    }
  }

  async function deleteMeal(mealId) {
    try {
      await nutritionAPI.deleteMeal(mealId)
      await fetchTodayProgress(lastQueriedDate.value)
    } catch (err) {
      throw err
    }
  }

  async function fetchWeightLogs(limit = 100) {
    try {
      const res = await nutritionAPI.getWeightLogs(limit)
      weightLogs.value = res.data
      return res.data
    } catch (err) {
      console.error('Failed to fetch weight logs:', err)
    }
  }

  async function recordWeight(weightData) {
    try {
      const res = await nutritionAPI.recordWeight(weightData)
      await fetchWeightLogs()
      return res.data
    } catch (err) {
      throw err
    }
  }

  async function deleteWeight(weightId) {
    try {
      await nutritionAPI.deleteWeight(weightId)
      await fetchWeightLogs()
    } catch (err) {
      throw err
    }
  }

  function resetState() {
    dailyProgress.value = null
    weightLogs.value = []
    lastQueriedDate.value = null
  }

  return {
    dailyProgress,
    weightLogs,
    loading,
    fetchTodayProgress,
    addMeal,
    updateMeal,
    deleteMeal,
    fetchWeightLogs,
    recordWeight,
    deleteWeight,
    resetState
  }
})
