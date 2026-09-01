<template>
  <nav v-if="authStore.isAuthenticated" class="glass-bottom-nav">
    <div class="max-w-xl mx-auto px-4 h-16 flex items-center justify-around">
      <!-- 1. 今日概覽 -->
      <router-link
        to="/"
        class="flex flex-col items-center justify-center w-12 py-1 text-slate-400 transition-colors"
        :class="{ 'text-brand-600 font-semibold': route.path === '/' }"
      >
        <Home class="w-5 h-5 mb-0.5" />
        <span class="text-[10px]">今日</span>
      </router-link>

      <!-- 2. 訓練庫與課表 -->
      <router-link
        to="/workout"
        class="flex flex-col items-center justify-center w-12 py-1 text-slate-400 transition-colors relative"
        :class="{ 'text-brand-600 font-semibold': route.path === '/workout' || route.path === '/active-workout' }"
      >
        <div v-if="workoutStore.isWorkoutActive" class="absolute -top-1 right-2 w-2 h-2 rounded-full bg-emerald-500 animate-ping"></div>
        <Dumbbell class="w-5 h-5 mb-0.5" />
        <span class="text-[10px]">訓練</span>
      </router-link>

      <!-- 3. 飲食記錄 -->
      <router-link
        to="/diet"
        class="flex flex-col items-center justify-center w-12 py-1 text-slate-400 transition-colors"
        :class="{ 'text-brand-600 font-semibold': route.path === '/diet' }"
      >
        <Utensils class="w-5 h-5 mb-0.5" />
        <span class="text-[10px]">飲食</span>
      </router-link>

      <!-- 4. 趨勢分析 -->
      <router-link
        to="/stats"
        class="flex flex-col items-center justify-center w-12 py-1 text-slate-400 transition-colors"
        :class="{ 'text-brand-600 font-semibold': route.path === '/stats' }"
      >
        <TrendingUp class="w-5 h-5 mb-0.5" />
        <span class="text-[10px]">趨勢</span>
      </router-link>

      <!-- 5. AI 教練 -->
      <router-link
        to="/ai-coach"
        class="flex flex-col items-center justify-center w-12 py-1 text-slate-400 transition-colors"
        :class="{ 'text-brand-600 font-semibold': route.path === '/ai-coach' }"
      >
        <Bot class="w-5 h-5 mb-0.5" />
        <span class="text-[10px]">AI 教練</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Home, Dumbbell, Utensils, TrendingUp, Bot } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useWorkoutStore } from '@/stores/workout'

const route = useRoute()
const authStore = useAuthStore()
const workoutStore = useWorkoutStore()
</script>
