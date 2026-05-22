<!--
  HomeView.vue — 用户端虚拟试衣页（原 App.vue 主体）
  数据：从 /api/clothes 拉取后端管理的衣服列表
-->
<template>
  <div class="min-h-screen relative">
    <!-- ── 全局背景装饰 ──────────────────────────────────── -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute inset-0 bg-grid" />
      <div class="absolute -top-40 -right-40 w-[520px] h-[520px] rounded-full opacity-60"
           style="background: radial-gradient(circle, rgba(200,255,61,0.10) 0%, transparent 70%);" />
      <div class="absolute -bottom-40 -left-40 w-[520px] h-[520px] rounded-full opacity-60"
           style="background: radial-gradient(circle, rgba(61,214,255,0.08) 0%, transparent 70%);" />
    </div>

    <!-- ── 顶部 ────────────────────────────────────────── -->
    <header class="relative z-10 max-w-7xl mx-auto px-6 pt-8 pb-4 flex items-center justify-between animate-fade-up">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-accent-dim flex items-center justify-center shadow-accent-glow">
          <svg class="w-5 h-5 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M4 7l4-3 2 2h4l2-2 4 3-2 4h-2v9H8v-9H6L4 7z" stroke-linejoin="round" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h1 class="text-[19px] font-display font-semibold tracking-tight leading-none">
            虚拟试衣
            <span class="text-ink-400 font-normal ml-1 text-[13px]">Virtual Try-On</span>
          </h1>
          <p class="text-[11px] text-ink-400 mt-1">上传人像 + 选择衣服，AI 一键生成试穿效果</p>
        </div>
      </div>

      <div class="hidden md:flex items-center gap-2">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full border border-ink-600 bg-ink-800/60 backdrop-blur text-xs text-ink-400">
          <span class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-soft" />
          <span>AI Powered · OOTDiffusion</span>
        </div>
        <button
          @click="enterKiosk"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-accent/40 bg-accent/10 text-accent text-xs hover:bg-accent/20 hover:border-accent/60 transition-all active:scale-95"
          title="进入触控全屏模式（适配大屏触控屏）"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 8V5a1 1 0 011-1h3M16 4h3a1 1 0 011 1v3M20 16v3a1 1 0 01-1 1h-3M8 20H5a1 1 0 01-1-1v-3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          触控全屏
        </button>
        <router-link
          to="/admin"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-ink-600 bg-ink-800/60 backdrop-blur text-xs text-ink-400 hover:text-white hover:border-ink-500 transition-all"
          title="进入后台管理"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1l3.09 6.26L22 8.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 13.14 2 8.27l6.91-1.01L12 1z" stroke-linejoin="round" stroke-linecap="round" />
          </svg>
          后台
        </router-link>
      </div>
    </header>

    <!-- ── 主工作区 ────────────────────────────────────── -->
    <main class="relative z-10 max-w-6xl mx-auto px-6 pt-4 pb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 items-start animate-fade-up animate-delay-100">
        <ImageSlot
          step="1"
          label="人物图片"
          hint="正面站立效果最佳"
          empty-title="上传人像"
          empty-hint="点击或拖拽到此处"
          icon="person"
          :preview="personPreview"
          uploadable
          capturable
          @upload="onPersonUpload"
          @capture="cameraOpen = true"
        />
        <ImageSlot
          step="2"
          label="服装款式"
          hint="上传或从下方选择"
          empty-title="选择衣服"
          empty-hint="下方选择预设，或直接上传"
          icon="shirt"
          :preview="clothPreview"
          :selected="!!selectedPresetId"
          uploadable
          @upload="onClothUpload"
        />
        <ImageSlot
          step="3"
          label="试穿结果"
          hint="点击放大 · 可下载"
          empty-title="等待生成"
          empty-hint="完成左侧两项后点击「开始试衣」"
          icon="sparkles"
          :preview="resultUrl"
          :loading="loading"
          :zoomable="!!resultUrl"
          :downloadable="!!resultUrl"
          @zoom="showModal = true"
        />
      </div>

      <!-- 服装类别选择器（影响 OOTDiffusion 推理类型）-->
      <transition name="progress-fade">
        <div v-if="clothPreview" class="mt-8 flex flex-col items-center gap-2 animate-fade-up">
          <div class="flex items-center gap-2 text-[11px] text-ink-400">
            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"
                    stroke-linecap="round" />
            </svg>
            <span>服装类别</span>
            <span v-if="categoryLockedByPreset" class="text-[10px] text-ink-500">（来自预设）</span>
          </div>
          <div class="inline-flex items-center gap-1 p-1 rounded-xl border border-ink-600 bg-ink-800/70 backdrop-blur">
            <button
              v-for="opt in categoryOptions"
              :key="opt.value"
              @click="clothCategory = opt.value"
              :disabled="loading"
              class="px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all active:scale-95"
              :class="clothCategory === opt.value
                ? 'bg-accent text-ink-900 shadow-accent-glow'
                : 'text-ink-300 hover:text-white hover:bg-ink-700/60'"
            >
              <span class="mr-1">{{ opt.icon }}</span>{{ opt.label }}
            </button>
          </div>
        </div>
      </transition>

      <!-- CTA -->
      <div class="mt-6 flex flex-col items-center gap-5 animate-fade-up animate-delay-200">
        <div v-if="!loading && readinessHint"
             class="px-3 py-1.5 rounded-full border border-ink-600/70 bg-ink-800/60 text-[11px] text-ink-400 backdrop-blur">
          {{ readinessHint }}
        </div>

        <button
          @click="handleTryOn"
          :disabled="!canSubmit"
          class="group relative inline-flex items-center gap-2.5 px-9 py-3.5 rounded-2xl font-display font-semibold text-[15px] tracking-wide transition-all duration-300 will-change-transform"
          :class="canSubmit
            ? 'bg-accent text-ink-900 hover:bg-accent-soft shadow-accent-glow hover:scale-[1.03] active:scale-[0.97]'
            : loading
              ? 'bg-ink-700 text-white/80 cursor-not-allowed'
              : 'bg-ink-700/70 text-ink-500 cursor-not-allowed border border-ink-600/60'"
        >
          <span v-if="canSubmit"
                class="absolute inset-0 rounded-2xl blur-xl opacity-50 bg-accent -z-10 transition-opacity group-hover:opacity-75" />
          <template v-if="loading">
            <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25"/>
              <path fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" class="opacity-90"/>
            </svg>
            生成中…
          </template>
          <template v-else>
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M13 2L4.09 13.43a1 1 0 00.77 1.63H10l-1 7 8.91-11.43a1 1 0 00-.77-1.63H14l1-7z" stroke-linejoin="round" stroke-linecap="round"/>
            </svg>
            开始试衣
          </template>
        </button>

        <transition name="progress-fade">
          <div v-if="loading" class="w-full max-w-md mt-1">
            <ProgressBar :progress="progress" label="正在生成，请稍候…" :subtitle="progressStage" />
          </div>
        </transition>

        <transition name="progress-fade">
          <div v-if="error"
               class="max-w-xl w-full px-4 py-3 rounded-xl border border-red-900/60 bg-red-950/30 text-red-300 text-xs text-center flex items-center justify-center gap-2">
            <svg class="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" stroke-linecap="round" />
            </svg>
            <span class="whitespace-pre-line">{{ error }}</span>
          </div>
        </transition>
      </div>

      <!-- 分类标签 -->
      <div class="mt-14 mb-3 flex items-center justify-center flex-wrap gap-2 animate-fade-up animate-delay-300">
        <button
          v-for="c in CATEGORIES"
          :key="c.value"
          @click="setCategory(c.value)"
          class="px-3.5 py-1.5 rounded-full text-xs font-medium border transition-all active:scale-95"
          :class="currentCategory === c.value
            ? 'bg-accent text-ink-900 border-accent shadow-accent-glow'
            : 'bg-ink-800/60 text-ink-400 border-ink-600 hover:border-ink-500 hover:text-white'"
        >
          <span class="mr-1">{{ c.icon }}</span>{{ c.label }}
        </button>
      </div>

      <!-- ── 服装 Dock ───────────────────────────────────── -->
      <div class="mt-2 animate-fade-up animate-delay-300">
        <ClothingDock
          v-if="!clothesLoading && filteredClothes.length"
          :items="filteredClothes"
          v-model="selectedPresetId"
          @update:modelValue="onPresetSelect"
        />
        <div v-else-if="clothesLoading"
             class="text-center py-12 text-sm text-ink-400 animate-pulse-soft">
          正在加载衣服库…
        </div>
        <div v-else
             class="text-center py-12 px-4 rounded-2xl border border-dashed border-ink-600 bg-ink-800/40">
          <p class="text-sm text-ink-400 mb-1">该分类下暂无衣服</p>
          <p class="text-[11px] text-ink-500">
            请在
            <router-link to="/admin" class="text-accent hover:underline">后台管理</router-link>
            添加衣服图片
          </p>
        </div>
      </div>

      <footer class="mt-16 pb-10 text-center text-[11px] text-ink-500">
        Powered by <span class="text-ink-300">OOTDiffusion</span> ·
        © {{ new Date().getFullYear() }} Virtual Try-On
      </footer>
    </main>

    <ResultModal :open="showModal" :src="resultUrl" @close="showModal = false" />
    <CameraCapture
      :open="cameraOpen"
      @close="cameraOpen = false"
      @capture="onCameraCaptured"
    />
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

import ImageSlot      from '../components/ImageSlot.vue'
import ProgressBar    from '../components/ProgressBar.vue'
import ClothingDock   from '../components/ClothingDock.vue'
import ResultModal    from '../components/ResultModal.vue'
import CameraCapture  from '../components/CameraCapture.vue'
import { listClothes, CATEGORIES, DEFAULT_CATEGORY } from '../api/clothes.js'

const router = useRouter()

/* ── 进入触控全屏模式 ──────────────────────────────────── */
async function enterKiosk() {
  // 先请求全屏（必须由用户手势触发，所以放在按钮点击里），再跳路由。
  // 失败也无所谓（用户拒绝 / 浏览器不支持），路由依然进入。
  try {
    if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
      await document.documentElement.requestFullscreen({ navigationUI: 'hide' })
    }
  } catch (_) { /* ignore */ }
  router.push('/kiosk')
}

/* ── State ────────────────────────────────────────────── */
const personFile       = ref(null)
const clothFile        = ref(null)
const personPreview    = ref(null)
const clothPreview     = ref(null)
const selectedPresetId = ref(null)
const clothCategory    = ref(DEFAULT_CATEGORY)   // upperbody / lowerbody / dress
const categoryLockedByPreset = ref(false)        // 仅作 UI 提示

/* 用于服装类别选择器（去掉 "all"）*/
const categoryOptions = computed(() => CATEGORIES.filter(c => c.value !== 'all'))

const loading       = ref(false)
const resultUrl     = ref(null)
const error         = ref(null)
const showModal     = ref(false)
const cameraOpen    = ref(false)

const progress      = ref(0)
const progressStage = ref('')
let   progressTimer = null

const allClothes      = ref([])
const clothesLoading  = ref(true)
const currentCategory = ref('all')

const filteredClothes = computed(() => {
  if (currentCategory.value === 'all') return allClothes.value
  return allClothes.value.filter(c => c.category === currentCategory.value)
})

/* ── Computed ─────────────────────────────────────────── */
const canSubmit = computed(() => personFile.value && clothFile.value && !loading.value)

const readinessHint = computed(() => {
  if (loading.value) return ''
  if (!personFile.value && !clothFile.value) return '请先上传人像，并上传或选择一件衣服'
  if (!personFile.value) return '还差一步：请上传人像图片'
  if (!clothFile.value)  return '还差一步：请选择或上传衣服图片'
  return '准备就绪，点击按钮开始生成'
})

/* ── 拉取衣服列表 ──────────────────────────────────────── */
async function loadClothes() {
  clothesLoading.value = true
  try {
    allClothes.value = await listClothes()
  } catch (e) {
    console.error('加载衣服失败', e)
    allClothes.value = []
  } finally {
    clothesLoading.value = false
  }
}

function setCategory(c) {
  currentCategory.value = c
}

/* ── Helpers ──────────────────────────────────────────── */
function revokePreview(url) {
  if (url && url.startsWith('blob:')) URL.revokeObjectURL(url)
}
function resetResult() {
  resultUrl.value = null
  error.value = null
}

async function urlToFile(url, filename = 'preset.jpg') {
  const res = await fetch(url, { mode: 'cors' })
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`)
  const blob = await res.blob()
  const type = blob.type && blob.type.startsWith('image/') ? blob.type : 'image/jpeg'
  return new File([blob], filename, { type })
}

/* ── 文件操作 ──────────────────────────────────────────── */
function onPersonUpload(file) {
  revokePreview(personPreview.value)
  personFile.value = file
  personPreview.value = file ? URL.createObjectURL(file) : null
  resetResult()
}

function onCameraCaptured(file) {
  onPersonUpload(file)
}

function onClothUpload(file) {
  revokePreview(clothPreview.value)
  clothFile.value = file
  clothPreview.value = file ? URL.createObjectURL(file) : null
  selectedPresetId.value = null
  // 自定义上传：解锁类别选择，由用户决定（默认上半身）
  categoryLockedByPreset.value = false
  resetResult()
}

async function onPresetSelect(id) {
  const preset = allClothes.value.find(p => p.id === id)
  if (!preset) return
  selectedPresetId.value = id
  error.value = null

  revokePreview(clothPreview.value)
  clothPreview.value = preset.url
  clothFile.value = null

  // 选了预设：自动同步类别（用户仍可手动覆盖）
  if (preset.category) {
    clothCategory.value = preset.category
    categoryLockedByPreset.value = true
  }

  try {
    const file = await urlToFile(preset.url, `${preset.id}.jpg`)
    clothFile.value = file
  } catch (e) {
    console.error(e)
    error.value = '加载预设图片失败：' + (e.message || '网络错误')
    selectedPresetId.value = null
    clothPreview.value = null
    categoryLockedByPreset.value = false
  }
  resetResult()
}

/* ── 进度条模拟 ────────────────────────────────────────── */
function startProgressSim() {
  progress.value = 2
  progressStage.value = '上传图像…'
  clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    const p = progress.value
    let delta = 0
    if      (p < 20) delta = 3 + Math.random() * 3
    else if (p < 50) delta = 1.5 + Math.random() * 2
    else if (p < 80) delta = 0.6 + Math.random() * 1.2
    else if (p < 95) delta = 0.2 + Math.random() * 0.6
    else delta = 0
    progress.value = Math.min(95, p + delta)

    if      (progress.value < 15) progressStage.value = '上传图像…'
    else if (progress.value < 35) progressStage.value = '解析人体姿态…'
    else if (progress.value < 55) progressStage.value = '提取服装特征…'
    else if (progress.value < 75) progressStage.value = '扩散模型推理中…'
    else                          progressStage.value = '合成最终图像…'
  }, 400)
}

function stopProgressSim({ success = true } = {}) {
  clearInterval(progressTimer)
  progressTimer = null
  if (success) {
    progress.value = 100
    progressStage.value = '完成！'
    setTimeout(() => { progress.value = 0; progressStage.value = '' }, 800)
  } else {
    progress.value = 0
    progressStage.value = ''
  }
}

/* ── 提交 ──────────────────────────────────────────────── */
async function handleTryOn() {
  if (!canSubmit.value) return

  loading.value = true
  resetResult()
  startProgressSim()

  try {
    const formData = new FormData()
    formData.append('person',   personFile.value)
    formData.append('cloth',    clothFile.value)
    formData.append('category', clothCategory.value)

    const res = await axios.post('/api/tryon', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    if (res.data.code === 0) {
      stopProgressSim({ success: true })
      resultUrl.value = res.data.data.image_url + '?t=' + Date.now()
    } else {
      stopProgressSim({ success: false })
      error.value = res.data.msg || '合成失败，请重试'
    }
  } catch (err) {
    stopProgressSim({ success: false })
    error.value = err.response?.data?.detail || '网络错误，请确认后端服务已启动'
  } finally {
    loading.value = false
  }
}

/* ── 生命周期 ──────────────────────────────────────────── */
onMounted(loadClothes)
onBeforeUnmount(() => clearInterval(progressTimer))
</script>

<style scoped>
.progress-fade-enter-active,
.progress-fade-leave-active {
  transition: all 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.progress-fade-enter-from { opacity: 0; transform: translateY(8px); }
.progress-fade-leave-to   { opacity: 0; transform: translateY(-4px); }
</style>
