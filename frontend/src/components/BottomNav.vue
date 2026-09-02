<template>
  <nav v-if="authStore.isAuthenticated" class="glass-bottom-nav select-none">
    <div class="max-w-xl mx-auto px-2 h-16 flex items-center justify-around">
      <!-- 1. 今日概覽 -->
      <router-link
        to="/"
        class="flex flex-col items-center justify-center flex-1 py-1 transition-all group"
        :class="route.path === '/' ? 'text-emerald-600 font-black' : 'text-slate-400 font-medium hover:text-slate-600'"
      >
        <div
          class="w-10 h-7 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/' ? 'bg-emerald-50 text-emerald-600 shadow-xs' : 'text-slate-400 group-hover:text-slate-600'"
        >
          <Home class="w-5 h-5" :class="route.path === '/' ? 'stroke-[2.5]' : 'stroke-2'" />
        </div>
        <span class="text-[10px] mt-0.5" :class="route.path === '/' ? 'text-emerald-700 font-black' : 'text-slate-400'">今日</span>
        <span
          class="w-1.5 h-1.5 rounded-full mt-0.5 transition-all"
          :class="route.path === '/' ? 'bg-emerald-500 scale-100' : 'bg-transparent scale-0'"
        ></span>
      </router-link>

      <!-- 2. 訓練庫與課表 -->
      <router-link
        to="/workout"
        class="flex flex-col items-center justify-center flex-1 py-1 transition-all group relative"
        :class="(route.path === '/workout' || route.path === '/active-workout') ? 'text-emerald-600 font-black' : 'text-slate-400 font-medium hover:text-slate-600'"
      >
        <div v-if="workoutStore.isWorkoutActive" class="absolute top-1 right-5 w-2 h-2 rounded-full bg-amber-500 animate-ping"></div>
        <div
          class="w-10 h-7 rounded-xl flex items-center justify-center transition-all"
          :class="(route.path === '/workout' || route.path === '/active-workout') ? 'bg-emerald-50 text-emerald-600 shadow-xs' : 'text-slate-400 group-hover:text-slate-600'"
        >
          <Dumbbell class="w-5 h-5" :class="(route.path === '/workout' || route.path === '/active-workout') ? 'stroke-[2.5]' : 'stroke-2'" />
        </div>
        <span class="text-[10px] mt-0.5" :class="(route.path === '/workout' || route.path === '/active-workout') ? 'text-emerald-700 font-black' : 'text-slate-400'">訓練</span>
        <span
          class="w-1.5 h-1.5 rounded-full mt-0.5 transition-all"
          :class="(route.path === '/workout' || route.path === '/active-workout') ? 'bg-emerald-500 scale-100' : 'bg-transparent scale-0'"
        ></span>
      </router-link>

      <!-- 3. 飲食記錄 -->
      <router-link
        to="/diet"
        class="flex flex-col items-center justify-center flex-1 py-1 transition-all group"
        :class="route.path === '/diet' ? 'text-emerald-600 font-black' : 'text-slate-400 font-medium hover:text-slate-600'"
      >
        <div
          class="w-10 h-7 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/diet' ? 'bg-emerald-50 text-emerald-600 shadow-xs' : 'text-slate-400 group-hover:text-slate-600'"
        >
          <Utensils class="w-5 h-5" :class="route.path === '/diet' ? 'stroke-[2.5]' : 'stroke-2'" />
        </div>
        <span class="text-[10px] mt-0.5" :class="route.path === '/diet' ? 'text-emerald-700 font-black' : 'text-slate-400'">飲食</span>
        <span
          class="w-1.5 h-1.5 rounded-full mt-0.5 transition-all"
          :class="route.path === '/diet' ? 'bg-emerald-500 scale-100' : 'bg-transparent scale-0'"
        ></span>
      </router-link>

      <!-- 4. 趨勢分析 -->
      <router-link
        to="/stats"
        class="flex flex-col items-center justify-center flex-1 py-1 transition-all group"
        :class="route.path === '/stats' ? 'text-emerald-600 font-black' : 'text-slate-400 font-medium hover:text-slate-600'"
      >
        <div
          class="w-10 h-7 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/stats' ? 'bg-emerald-50 text-emerald-600 shadow-xs' : 'text-slate-400 group-hover:text-slate-600'"
        >
          <TrendingUp class="w-5 h-5" :class="route.path === '/stats' ? 'stroke-[2.5]' : 'stroke-2'" />
        </div>
        <span class="text-[10px] mt-0.5" :class="route.path === '/stats' ? 'text-emerald-700 font-black' : 'text-slate-400'">趨勢</span>
        <span
          class="w-1.5 h-1.5 rounded-full mt-0.5 transition-all"
          :class="route.path === '/stats' ? 'bg-emerald-500 scale-100' : 'bg-transparent scale-0'"
        ></span>
      </router-link>

      <!-- 5. AI 教練 -->
      <router-link
        to="/ai-coach"
        class="flex flex-col items-center justify-center flex-1 py-1 transition-all group"
        :class="route.path === '/ai-coach' ? 'text-emerald-600 font-black' : 'text-slate-400 font-medium hover:text-slate-600'"
      >
        <div
          class="w-10 h-7 rounded-xl flex items-center justify-center transition-all"
          :class="route.path === '/ai-coach' ? 'bg-emerald-50 text-emerald-600 shadow-xs' : 'text-slate-400 group-hover:text-slate-600'"
        >
          <Bot class="w-5 h-5" :class="route.path === '/ai-coach' ? 'stroke-[2.5]' : 'stroke-2'" />
        </div>
        <span class="text-[10px] mt-0.5" :class="route.path === '/ai-coach' ? 'text-emerald-700 font-black' : 'text-slate-400'">AI 教練</span>
        <span
          class="w-1.5 h-1.5 rounded-full mt-0.5 transition-all"
          :class="route.path === '/ai-coach' ? 'bg-emerald-500 scale-100' : 'bg-transparent scale-0'"
        ></span>
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
