<template>
  <div class="min-h-screen flex flex-col justify-center px-6 py-12 max-w-sm mx-auto">
    <!-- Brand Header -->
    <div class="text-center mb-8 space-y-2">
      <div class="w-14 h-14 rounded-3xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white shadow-float mx-auto">
        <Activity class="w-8 h-8" />
      </div>
      <h1 class="text-2xl font-black text-slate-900 tracking-tight">FitPulse 脈動健身</h1>
      <p class="text-xs text-slate-400">智慧訓練排課 · 純文字 AI 飲食 · 漸進式超負荷</p>
    </div>

    <!-- Auth Card -->
    <div class="card-apple shadow-lg p-6 space-y-5">
      <!-- Tabs -->
      <div class="flex bg-slate-100 p-1 rounded-xl">
        <button
          @click="isRegister = false"
          class="flex-1 py-2 text-xs font-bold rounded-lg transition-all"
          :class="!isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
        >
          會員登入
        </button>
        <button
          @click="isRegister = true"
          class="flex-1 py-2 text-xs font-bold rounded-lg transition-all"
          :class="isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'"
        >
          免費註冊
        </button>
      </div>

      <!-- Error alert -->
      <div v-if="errorMessage" class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
        {{ errorMessage }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-3.5">
        <div v-if="isRegister">
          <label class="block text-xs font-bold text-slate-700 mb-1">您的暱稱 / 姓名</label>
          <input
            v-model="name"
            type="text"
            required
            placeholder="例如：健恩 / 健身新手"
            class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">電子郵件 (Email)</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="your_email@example.com"
            class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">登入密碼</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="至少 6 位字元密碼"
            class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-brand-500"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-black text-xs shadow-md shadow-brand-500/20 active:scale-95 transition-all flex items-center justify-center gap-1.5"
        >
          <Lock class="w-3.5 h-3.5" />
          <span>{{ loading ? '處理中...' : (isRegister ? '立即註冊並開始健身' : '登入 FitPulse') }}</span>
        </button>
      </form>
    </div>

    <div class="text-center mt-6 text-[11px] text-slate-400">
      專為個人、伴侶與好友設計 · 資料安全獨立隔離
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, Lock } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isRegister = ref(false)
const name = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  loading.value = true

  try {
    if (isRegister.value) {
      await authStore.register(name.value, email.value, password.value)
    } else {
      await authStore.login(email.value, password.value)
    }
    router.push('/')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      errorMessage.value = detail.map(item => `${item.loc?.slice(-1)[0] || '欄位'}: ${item.msg}`).join(', ')
    } else if (typeof detail === 'string') {
      errorMessage.value = detail
    } else {
      errorMessage.value = '驗證失敗，請檢查輸入資料（密碼需至少 6 碼、Email 需符合格式）'
    }
  } finally {
    loading.value = false
  }
}
</script>
