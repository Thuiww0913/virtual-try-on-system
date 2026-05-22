<!--
  AdminView.vue — 后台管理主页面
-->
<template>
  <div class="min-h-screen relative">
    <!-- 背景 -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute inset-0 bg-grid" />
      <div class="absolute -top-40 -right-40 w-[460px] h-[460px] rounded-full opacity-50"
           style="background: radial-gradient(circle, rgba(200,255,61,0.07) 0%, transparent 70%);" />
    </div>

    <!-- 顶部 nav -->
    <header class="relative z-10 border-b border-ink-700/60 bg-ink-900/50 backdrop-blur-md">
      <div class="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dim flex items-center justify-center shadow-accent-glow">
            <svg class="w-4 h-4 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="9" rx="1" />
              <rect x="14" y="3" width="7" height="5" rx="1" />
              <rect x="14" y="12" width="7" height="9" rx="1" />
              <rect x="3" y="16" width="7" height="5" rx="1" />
            </svg>
          </div>
          <div>
            <h1 class="text-sm font-display font-semibold text-white leading-none">后台管理</h1>
            <p class="text-[10px] text-ink-400 mt-0.5">虚拟试衣 · 资源库管理</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <router-link
            to="/"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-ink-600 bg-ink-800/60 text-xs text-ink-300 hover:text-white hover:border-ink-500 transition-all"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h6v6M21 3l-9 9M14 21H4a1 1 0 01-1-1V10" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            访问前台
          </router-link>
          <button
            @click="onLogout"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-ink-600 bg-ink-800/60 text-xs text-ink-300 hover:text-red-400 hover:border-red-500/40 transition-all"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"
                    stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            退出登录
          </button>
        </div>
      </div>
    </header>

    <!-- 主体 -->
    <main class="relative z-10 max-w-7xl mx-auto px-6 py-6">
      <!-- Tab 切换 -->
      <div class="mb-5 animate-fade-up">
        <div class="inline-flex items-center gap-1 p-1 rounded-xl border border-ink-700 bg-ink-800/60 backdrop-blur">
          <button
            @click="activeTab = 'clothes'"
            class="px-4 py-1.5 rounded-lg text-xs font-medium transition-all active:scale-95"
            :class="activeTab === 'clothes'
              ? 'bg-accent text-ink-900 shadow-accent-glow'
              : 'text-ink-300 hover:text-white hover:bg-ink-700/60'"
          >
            <span class="mr-1.5">👕</span>衣服管理
          </button>
          <button
            @click="activeTab = 'models'"
            class="px-4 py-1.5 rounded-lg text-xs font-medium transition-all active:scale-95"
            :class="activeTab === 'models'
              ? 'bg-accent text-ink-900 shadow-accent-glow'
              : 'text-ink-300 hover:text-white hover:bg-ink-700/60'"
          >
            <span class="mr-1.5">🧍</span>模特管理
          </button>
        </div>
      </div>

      <!-- ─── 衣服管理 Tab ────────────────────────────────────── -->
      <div v-show="activeTab === 'clothes'">
        <!-- 统计卡片 -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6 animate-fade-up">
          <div
            v-for="c in CATEGORIES.filter(x => x.value !== 'all')"
            :key="c.value"
            class="rounded-xl border border-ink-700 bg-ink-800/60 backdrop-blur p-3 hover:border-ink-600 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="text-[10px] text-ink-400 uppercase tracking-wide">{{ c.label }}</p>
                <p class="text-xl font-display font-bold text-white mt-1 tabular-nums">{{ countByCat(c.value) }}</p>
              </div>
              <div class="text-2xl opacity-60">{{ c.icon }}</div>
            </div>
          </div>
        </div>

        <div class="mb-6 animate-fade-up animate-delay-100">
          <AdminUploader
            @uploaded="onClothesUploaded"
            @error="showToast($event, 'error')"
          />
        </div>

        <div class="animate-fade-up animate-delay-200">
          <div v-if="clothesLoading" class="text-center py-12 text-sm text-ink-400 animate-pulse-soft">
            加载中…
          </div>
          <AdminClothesGrid
            v-else
            :items="clothes"
            @changed="loadClothes"
            @error="showToast($event, 'error')"
          />
        </div>
      </div>

      <!-- ─── 模特管理 Tab ────────────────────────────────────── -->
      <div v-show="activeTab === 'models'">
        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6 animate-fade-up">
          <div class="rounded-xl border border-ink-700 bg-ink-800/60 backdrop-blur p-3 hover:border-ink-600 transition-colors">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-[10px] text-ink-400 uppercase tracking-wide">模特总数</p>
                <p class="text-xl font-display font-bold text-white mt-1 tabular-nums">{{ models.length }}</p>
              </div>
              <div class="text-2xl opacity-60">🧍</div>
            </div>
          </div>
        </div>

        <div class="mb-6 animate-fade-up animate-delay-100">
          <AdminModelUploader
            @uploaded="onModelsUploaded"
            @error="showToast($event, 'error')"
          />
        </div>

        <div class="animate-fade-up animate-delay-200">
          <div v-if="modelsLoading" class="text-center py-12 text-sm text-ink-400 animate-pulse-soft">
            加载中…
          </div>
          <AdminModelsGrid
            v-else
            :items="models"
            @changed="loadModels"
            @error="showToast($event, 'error')"
          />
        </div>
      </div>
    </main>

    <!-- Toast -->
    <transition name="toast">
      <div
        v-if="toast"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-xl border backdrop-blur-md flex items-center gap-2 text-sm shadow-card-hover"
        :class="toast.type === 'error'
          ? 'border-red-500/40 bg-red-950/80 text-red-200'
          : 'border-accent/40 bg-ink-800/90 text-white'"
      >
        <svg v-if="toast.type === 'error'" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4M12 16h.01" stroke-linecap="round" />
        </svg>
        <svg v-else class="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        {{ toast.text }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { adminListClothes, adminListModels, logout } from '../api/admin.js'
import { CATEGORIES } from '../api/clothes.js'
import AdminUploader       from '../components/AdminUploader.vue'
import AdminClothesGrid    from '../components/AdminClothesGrid.vue'
import AdminModelUploader  from '../components/AdminModelUploader.vue'
import AdminModelsGrid     from '../components/AdminModelsGrid.vue'

const router        = useRouter()
const activeTab     = ref('clothes')   // 'clothes' | 'models'
const clothes       = ref([])
const clothesLoading = ref(true)
const models        = ref([])
const modelsLoading = ref(true)
const toast         = ref(null)
let toastTimer = null

async function loadClothes() {
  clothesLoading.value = true
  try {
    clothes.value = await adminListClothes()
  } catch (e) {
    showToast(e?.response?.data?.detail || '加载衣服失败', 'error')
  } finally {
    clothesLoading.value = false
  }
}

async function loadModels() {
  modelsLoading.value = true
  try {
    models.value = await adminListModels()
  } catch (e) {
    showToast(e?.response?.data?.detail || '加载模特失败', 'error')
  } finally {
    modelsLoading.value = false
  }
}

function countByCat(value) {
  return clothes.value.filter(x => x.category === value).length
}

function onClothesUploaded(created) {
  showToast(`成功上传 ${created.length} 件衣服`)
  loadClothes()
}

function onModelsUploaded(created) {
  showToast(`成功上传 ${created.length} 位模特`)
  loadModels()
}

async function onLogout() {
  await logout()
  router.replace('/admin/login')
}

function showToast(text, type = 'success') {
  toast.value = { text, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = null }, 2800)
}

onMounted(() => {
  loadClothes()
  loadModels()
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s cubic-bezier(0.22,1,0.36,1); }
.toast-enter-from { opacity: 0; transform: translate(-50%, 20px); }
.toast-leave-to   { opacity: 0; transform: translate(-50%, 8px); }
</style>
