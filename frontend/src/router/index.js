import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import WorkoutView from '@/views/WorkoutView.vue'
import ActiveWorkoutView from '@/views/ActiveWorkoutView.vue'
import DietView from '@/views/DietView.vue'
import StatsView from '@/views/StatsView.vue'
import AICoachView from '@/views/AICoachView.vue'
import ProfileView from '@/views/ProfileView.vue'
import AuthView from '@/views/AuthView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true, title: '今日概覽' }
  },
  {
    path: '/workout',
    name: 'workout',
    component: WorkoutView,
    meta: { requiresAuth: true, title: '訓練庫與課表' }
  },
  {
    path: '/active-workout',
    name: 'active-workout',
    component: ActiveWorkoutView,
    meta: { requiresAuth: true, title: '訓練進行中' }
  },
  {
    path: '/diet',
    name: 'diet',
    component: DietView,
    meta: { requiresAuth: true, title: '飲食記錄' }
  },
  {
    path: '/stats',
    name: 'stats',
    component: StatsView,
    meta: { requiresAuth: true, title: '趨勢分析' }
  },
  {
    path: '/ai-coach',
    name: 'ai-coach',
    component: AICoachView,
    meta: { requiresAuth: true, title: 'AI 隨身教練' }
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: { requiresAuth: true, title: '個人體態中心' }
  },
  {
    path: '/auth',
    name: 'auth',
    component: AuthView,
    meta: { requiresAuth: false, title: '登入 / 註冊' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('fitpulse_token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'auth' })
  } else if (to.name === 'auth' && token) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
