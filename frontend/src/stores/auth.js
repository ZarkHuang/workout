import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api/client'
import { useWorkoutStore } from '@/stores/workout'
import { useNutritionStore } from '@/stores/nutrition'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('fitpulse_token') || '')
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const profile = computed(() => user.value?.profile || null)

  async function login(email, password) {
    loading.value = true
    try {
      const res = await authAPI.login({ email, password })
      token.value = res.data.access_token
      localStorage.setItem('fitpulse_token', res.data.access_token)
      const nutritionStore = useNutritionStore()
      nutritionStore.resetState()
      await fetchMe()
      return true
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(name, email, password) {
    loading.value = true
    try {
      const res = await authAPI.register({ name, email, password })
      token.value = res.data.access_token
      localStorage.setItem('fitpulse_token', res.data.access_token)
      const nutritionStore = useNutritionStore()
      nutritionStore.resetState()
      await fetchMe()
      return true
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await authAPI.getMe()
      user.value = res.data
      const workoutStore = useWorkoutStore()
      workoutStore.syncUserOwnership(res.data.id)
    } catch (err) {
      logout()
    }
  }

  async function updateProfile(profileData) {
    loading.value = true
    try {
      const res = await authAPI.updateProfile(profileData)
      await fetchMe()
      return res.data
    } catch (err) {
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('fitpulse_token')
    const workoutStore = useWorkoutStore()
    workoutStore.cancelWorkout()
    workoutStore.ownerUserId = null
    const nutritionStore = useNutritionStore()
    nutritionStore.resetState()
  }

  return {
    token,
    user,
    profile,
    loading,
    isAuthenticated,
    login,
    register,
    fetchMe,
    updateProfile,
    logout
  }
})
