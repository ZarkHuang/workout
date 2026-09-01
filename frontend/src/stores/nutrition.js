import { defineStore } from 'pinia'
import { ref } from 'vue'
import { nutritionAPI } from '@/api/client'

export const useNutritionStore = defineStore('nutrition', () => {
  const dailyProgress = ref(null)
  const weightLogs = ref([])
  const loading = ref(false)

  async function fetchTodayProgress(dateStr = null) {
    loading.value = true
    try {
      const res = await nutritionAPI.getProgress(dateStr)
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
      await fetchTodayProgress()
      return res.data
    } catch (err) {
      throw err
    }
  }

  async function deleteMeal(mealId) {
    try {
      await nutritionAPI.deleteMeal(mealId)
      await fetchTodayProgress()
    } catch (err) {
      throw err
    }
  }

  async function fetchWeightLogs() {
    try {
      const res = await nutritionAPI.getWeightLogs(30)
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

  return {
    dailyProgress,
    weightLogs,
    loading,
    fetchTodayProgress,
    addMeal,
    deleteMeal,
    fetchWeightLogs,
    recordWeight
  }
})
