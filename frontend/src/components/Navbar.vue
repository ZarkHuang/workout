<template>
  <header v-if="authStore.isAuthenticated" class="glass-header">
    <div class="max-w-xl mx-auto px-4 h-14 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2 font-bold text-slate-900 text-lg tracking-tight">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white shadow-sm shadow-brand-500/20">
          <Activity class="w-5 h-5" />
        </div>
        <span class="bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">FitPulse</span>
        <span class="text-xs px-1.5 py-0.5 rounded bg-brand-50 text-brand-700 font-semibold border border-brand-200/50">脈動</span>
      </router-link>

      <!-- Right items -->
      <div class="flex items-center gap-2">
        <!-- Active Workout Ongoing Floating Pill -->
        <router-link
          v-if="workoutStore.isWorkoutActive"
          to="/active-workout"
          class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500 text-white text-xs font-semibold shadow-sm shadow-emerald-500/30 animate-pulse hover:bg-emerald-600 transition-colors"
        >
          <Flame class="w-3.5 h-3.5" />
          <span>訓練進行中</span>
        </router-link>

        <!-- User Profile Avatar / Link -->
        <router-link
          to="/profile"
          class="flex items-center gap-1.5 p-1 pl-2.5 rounded-full bg-slate-100/80 hover:bg-slate-200/80 border border-slate-200/50 transition-colors"
        >
          <span class="text-xs font-medium text-slate-700 max-w-[80px] truncate">{{ authStore.user?.name || '個人' }}</span>
          <div class="w-6 h-6 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center">
            {{ (authStore.user?.name || 'U').charAt(0).toUpperCase() }}
          </div>
        </router-link>
      </div>
    </div>
  </header>
</template>

<script setup>
import { Activity, Flame } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useWorkoutStore } from '@/stores/workout'

const authStore = useAuthStore()
const workoutStore = useWorkoutStore()
</script>
