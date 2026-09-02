<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
    <!-- PWA Install Banner on Android / Samsung -->
    <div
      v-if="showInstallPrompt"
      class="bg-gradient-to-r from-emerald-600 to-teal-700 text-white px-4 py-2.5 flex items-center justify-between shadow-md z-50 sticky top-0"
    >
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center font-bold text-sm">
          ⚡
        </div>
        <div>
          <div class="text-xs font-black">安裝 FitPulse App</div>
          <div class="text-[10px] text-emerald-100">新增至主畫面，享受全螢幕獨立 App 體驗</div>
        </div>
      </div>
      <div class="flex items-center gap-1.5">
        <button
          @click="installPWA"
          class="text-xs font-extrabold bg-white text-emerald-800 px-3 py-1.5 rounded-lg shadow active:scale-95 transition-all"
        >
          立即安裝
        </button>
        <button
          @click="showInstallPrompt = false"
          class="p-1 text-white/80 hover:text-white"
        >
          ✕
        </button>
      </div>
    </div>

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
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import BottomNav from '@/components/BottomNav.vue'
import RestTimerWidget from '@/components/RestTimerWidget.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const deferredPrompt = ref(null)
const showInstallPrompt = ref(false)

onMounted(() => {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredPrompt.value = e
    showInstallPrompt.value = true
  })

  window.addEventListener('appinstalled', () => {
    showInstallPrompt.value = false
    deferredPrompt.value = null
  })

  if (authStore.isAuthenticated) {
    authStore.fetchMe()
  }
})

async function installPWA() {
  if (deferredPrompt.value) {
    deferredPrompt.value.prompt()
    const { outcome } = await deferredPrompt.value.userChoice
    if (outcome === 'accepted') {
      showInstallPrompt.value = false
    }
    deferredPrompt.value = null
  }
}
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
