import axios from 'axios'

let rawBase = import.meta.env.VITE_API_URL || '/api'
if (rawBase.startsWith('http') && !rawBase.endsWith('/api')) {
  rawBase = `${rawBase.replace(/\/+$/, '')}/api`
}
const API_BASE = rawBase

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add Bearer token to request headers
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('fitpulse_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// Handle 401 Unauthorized globally
client.interceptors.response.use((response) => {
  return response
}, (error) => {
  if (error.response && error.response.status === 401) {
    localStorage.removeItem('fitpulse_token')
    if (window.location.pathname !== '/auth') {
      window.location.href = '/auth'
    }
  }
  return Promise.reject(error)
})

export default client

// Auth APIs
export const authAPI = {
  register: (data) => client.post('/auth/register', data),
  login: (data) => client.post('/auth/login', data),
  getMe: () => client.get('/auth/me'),
  updateProfile: (data) => client.put('/auth/profile', data),
}

// Exercises APIs
export const exercisesAPI = {
  list: (params) => client.get('/exercises', { params }),
  create: (data) => client.post('/exercises', data),
  get: (id) => client.get(`/exercises/${id}`),
  getPreviousHint: (id) => client.get(`/exercises/${id}/previous-hint`),
}

// Workout APIs
export const workoutsAPI = {
  getRoutines: () => client.get('/workouts/routines'),
  createRoutine: (data) => client.post('/workouts/routines', data),
  deleteRoutine: (id) => client.delete(`/workouts/routines/${id}`),
  getSessions: (params) => client.get('/workouts/sessions', { params }),
  createSession: (data) => client.post('/workouts/sessions', data),
  deleteSession: (id) => client.delete(`/workouts/sessions/${id}`),
  getRecoveryStatus: () => client.get('/workouts/recovery'),
  getStrengthTrends: () => client.get('/workouts/stats/1rm-trends'),
  getWeeklyComparison: () => client.get('/workouts/weekly-comparison'),
  cleanup90d: () => client.post('/workouts/cleanup-90d-rolling'),
}

// Nutrition APIs
export const nutritionAPI = {
  getProgress: (dateStr) => client.get('/nutrition/progress', { params: { target_date: dateStr } }),
  addMeal: (data) => client.post('/nutrition/meals', data),
  deleteMeal: (id) => client.delete(`/nutrition/meals/${id}`),
  getWeightLogs: (limit = 30) => client.get('/nutrition/weight', { params: { limit } }),
  recordWeight: (data) => client.post('/nutrition/weight', data),
  cleanup30d: () => client.post('/nutrition/cleanup-30d-rolling'),
}

// AI APIs
export const aiAPI = {
  parseDiet: (text, mealType) => client.post('/ai/parse-diet', { text, meal_type: mealType }),
  recommendWorkout: (params) => client.post('/ai/recommend-workout', params),
  chat: (message, history = []) => client.post('/ai/chat', { message, conversation_history: history }),
}
