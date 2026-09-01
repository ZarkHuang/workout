<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
    <Navbar />

    <main class="flex-1 w-full max-w-xl mx-auto">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Global Floating Rest Timer -->
    <RestTimerWidget />

    <!-- Bottom Navigation Bar for Mobile PWA -->
    <BottomNav />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import BottomNav from '@/components/BottomNav.vue'
import RestTimerWidget from '@/components/RestTimerWidget.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.fetchMe()
  }
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
