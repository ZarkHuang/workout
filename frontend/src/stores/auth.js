import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api/client'

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
