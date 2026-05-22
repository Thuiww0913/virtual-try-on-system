<template>
  <div class="min-h-screen relative flex items-center justify-center px-4">
    <!-- 背景 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute inset-0 bg-grid" />
      <div class="absolute inset-0"
           style="background: radial-gradient(circle at 30% 20%, rgba(200,255,61,0.08) 0%, transparent 50%),
                              radial-gradient(circle at 70% 80%, rgba(61,214,255,0.06) 0%, transparent 50%);" />
    </div>

    <div class="relative z-10 w-full max-w-md animate-fade-up">
      <!-- 顶部品牌 -->
      <div class="text-center mb-8">
        <div class="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-br from-accent to-accent-dim items-center justify-center shadow-accent-glow mb-4">
          <svg class="w-6 h-6 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" />
            <path d="M7 11V7a5 5 0 0110 0v4" stroke-linecap="round" />
          </svg>
        </div>
        <h1 class="text-xl font-display font-semibold tracking-tight">管理员登录</h1>
        <p class="text-xs text-ink-400 mt-1.5">虚拟试衣 · 后台管理系统</p>
      </div>

      <!-- 表单卡片 -->
      <form
        @submit.prevent="onSubmit"
        class="relative rounded-3xl border border-ink-700 bg-ink-800/70 backdrop-blur-xl p-7 shadow-card"
      >
        <label class="block">
          <span class="text-xs font-medium text-ink-400 mb-2 block">管理员密码</span>
          <div class="relative">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              autofocus
              placeholder="请输入密码"
              class="w-full pl-10 pr-10 py-3 rounded-xl bg-ink-900/60 border border-ink-600 text-sm text-white placeholder-ink-500 focus:outline-none focus:border-accent/60 focus:bg-ink-900 focus:ring-2 focus:ring-accent/15 transition-all"
            />
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-500"
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0110 0v4" stroke-linecap="round" />
            </svg>
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-md text-ink-500 hover:text-white hover:bg-ink-700/60 transition-colors"
              :title="showPassword ? '隐藏密码' : '显示密码'"
            >
              <svg v-if="showPassword" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-10-8-10-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 10 8 10 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22"
                      stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M2 12s3-8 10-8 10 8 10 8-3 8-10 8-10-8-10-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </div>
        </label>

        <transition name="error-fade">
          <div v-if="error"
               class="mt-3 px-3 py-2 rounded-lg bg-red-950/40 border border-red-900/60 text-red-300 text-xs flex items-center gap-2">
            <svg class="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" stroke-linecap="round" />
            </svg>
            {{ error }}
          </div>
        </transition>

        <button
          type="submit"
          :disabled="loading || !password"
          class="mt-5 w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-display font-semibold text-sm tracking-wide transition-all"
          :class="loading || !password
            ? 'bg-ink-700 text-ink-500 cursor-not-allowed'
            : 'bg-accent text-ink-900 hover:bg-accent-soft shadow-accent-glow active:scale-[0.98]'"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" />
            <path fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" class="opacity-90" />
          </svg>
          {{ loading ? '验证中…' : '登录' }}
        </button>

        <p class="mt-5 text-center text-[11px] text-ink-500">
          默认密码 <code class="px-1.5 py-0.5 rounded bg-ink-700 text-ink-300 text-[10px] font-mono">admin123</code>
          · 通过 <code class="px-1.5 py-0.5 rounded bg-ink-700 text-ink-300 text-[10px] font-mono">ADMIN_PASSWORD</code> 环境变量修改
        </p>
      </form>

      <div class="mt-6 text-center">
        <router-link to="/" class="text-xs text-ink-400 hover:text-white transition-colors inline-flex items-center gap-1">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          返回主页
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/admin.js'

const route  = useRoute()
const router = useRouter()

const password     = ref('')
const showPassword = ref(false)
const loading      = ref(false)
const error        = ref('')

async function onSubmit() {
  if (!password.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    await login(password.value)
    const target = route.query.redirect || '/admin'
    router.replace(target)
  } catch (e) {
    error.value = e?.response?.data?.detail || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.error-fade-enter-active,
.error-fade-leave-active {
  transition: all 0.25s ease;
}
.error-fade-enter-from { opacity: 0; transform: translateY(-4px); }
.error-fade-leave-to   { opacity: 0; transform: translateY(-4px); }
</style>
