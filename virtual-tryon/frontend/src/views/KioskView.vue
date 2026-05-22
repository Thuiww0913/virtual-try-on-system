<!--
  KioskView.vue — 触控大屏全屏模式
  ================================
  专为 65 寸 16:9 触控屏设计的单屏布局：
    · 顶部 Header (~8% 高)
    · 中部三栏图片槽：人物 / 衣服 / 结果 (~60% 高)
    · 操作区：分类 + 大按钮 + 状态 (~11% 高)
    · 底部服装 Dock：横向触摸滚动 (~21% 高)

  进入方式：HomeView 顶部"触控全屏"按钮 → router.push('/kiosk') + requestFullscreen()
  退出方式：右上角按钮 / Esc / 监听 fullscreenchange → 自动回 '/'

  与 HomeView 共用：ImageSlot / CameraCapture / ResultModal / ProgressBar / clothes API
  与 HomeView 完全独立的状态，不影响原页面。
-->
<template>
  <div class="fixed inset-0 z-40 bg-ink-950 text-white overflow-hidden flex flex-col select-none">
    <!-- ── 背景装饰 ──────────────────────────────────────── -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div class="absolute inset-0 bg-grid opacity-50" />
      <div
        class="absolute -top-60 -right-60 w-[720px] h-[720px] rounded-full opacity-60"
        style="background: radial-gradient(circle, rgba(200,255,61,0.12) 0%, transparent 70%);"
      />
      <div
        class="absolute -bottom-60 -left-60 w-[720px] h-[720px] rounded-full opacity-60"
        style="background: radial-gradient(circle, rgba(61,214,255,0.10) 0%, transparent 70%);"
      />
    </div>

    <!-- ── 顶部 Header ───────────────────────────────────── -->
    <header class="relative z-10 shrink-0 flex items-center justify-between px-10 xl:px-16 3xl:px-24 py-5 xl:py-6 3xl:py-10">
      <div class="flex items-center gap-4 3xl:gap-7">
        <div class="w-12 h-12 xl:w-14 xl:h-14 3xl:w-24 3xl:h-24 rounded-2xl 3xl:rounded-3xl bg-gradient-to-br from-accent to-accent-dim flex items-center justify-center shadow-accent-glow">
          <svg class="w-7 h-7 xl:w-8 xl:h-8 3xl:w-14 3xl:h-14 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M4 7l4-3 2 2h4l2-2 4 3-2 4h-2v9H8v-9H6L4 7z" stroke-linejoin="round" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h1 class="text-xl xl:text-2xl 3xl:text-5xl font-display font-semibold tracking-tight leading-none">
            虚拟试衣
            <span class="text-ink-400 font-normal ml-1 3xl:ml-3 text-base xl:text-lg 3xl:text-3xl">Virtual Try-On</span>
          </h1>
          <p class="text-xs xl:text-sm 3xl:text-xl text-ink-400 mt-1.5 3xl:mt-3">触控模式 · AI Powered · OOTDiffusion</p>
        </div>
      </div>

      <div class="flex items-center gap-3 3xl:gap-5">
        <div class="hidden md:flex items-center gap-2.5 3xl:gap-4 px-4 3xl:px-7 py-2.5 3xl:py-4 rounded-full border border-ink-600 bg-ink-800/70 backdrop-blur text-sm 3xl:text-xl text-ink-300">
          <span class="w-2 h-2 3xl:w-3 3xl:h-3 rounded-full bg-accent animate-pulse-soft" />
          <span>触控全屏</span>
          <span class="mx-1 text-ink-600">|</span>
          <span class="font-mono text-ink-500 text-xs 3xl:text-base">{{ viewportSize }}</span>
        </div>
        <button
          @click="resetAll"
          class="px-4 xl:px-5 3xl:px-7 py-2.5 3xl:py-4 rounded-2xl 3xl:rounded-3xl border border-ink-600 bg-ink-800/70 hover:bg-ink-700 active:scale-95 transition-all text-sm 3xl:text-xl font-medium backdrop-blur flex items-center gap-2 3xl:gap-3"
          title="重置当前会话"
        >
          <svg class="w-4 h-4 3xl:w-6 3xl:h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 0115-6.7L21 8M21 3v5h-5M21 12a9 9 0 01-15 6.7L3 16M3 21v-5h5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          重置
        </button>
        <button
          @click="exitKiosk"
          class="px-5 xl:px-6 3xl:px-8 py-2.5 3xl:py-4 rounded-2xl 3xl:rounded-3xl border border-ink-600 bg-ink-800/70 hover:bg-ink-700 active:scale-95 transition-all text-sm 3xl:text-xl font-medium backdrop-blur flex items-center gap-2 3xl:gap-3"
        >
          <svg class="w-4 h-4 3xl:w-6 3xl:h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M8 3v3a2 2 0 002 2h3M21 8V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3M16 21h3a2 2 0 002-2v-3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          退出全屏
        </button>
      </div>
    </header>

    <!-- ── 中部三栏 ──────────────────────────────────────── -->
    <main class="relative z-10 flex-1 min-h-0 flex items-center justify-center gap-6 xl:gap-10 3xl:gap-20 px-10 xl:px-16 3xl:px-24">
      <!-- 1. 人物：只支持拍照（无文件上传）；有照片后点击放大 -->
      <div class="kiosk-slot-wrap">
        <ImageSlot
          step="1"
          label="人物图片"
          hint="点击卡片打开摄像头 · 自动 3:4"
          empty-title="点击此处拍照"
          empty-hint="将打开摄像头取景 · 拍照后自动裁切"
          icon="person"
          :preview="personPreview"
          capturable
          :zoomable="!!personPreview"
          @capture="cameraOpen = true"
          @zoom="openZoom(personPreview, '人像预览', false)"
        />
      </div>

      <!-- 2. 衣服：只支持从下方 Dock 选取；有图后点击放大 -->
      <div class="kiosk-slot-wrap">
        <ImageSlot
          step="2"
          label="服装款式"
          hint="从下方款式精选挑选"
          empty-title="选择一件衣服"
          empty-hint="点击 ↓ 下方款式精选 · 滑动浏览"
          icon="shirt"
          :preview="clothPreview"
          :selected="!!selectedPresetId"
          :zoomable="!!clothPreview"
          @zoom="openZoom(clothPreview, '服装预览', false)"
          @empty-click="pulseDock"
        />
      </div>

      <!-- 3. 结果：点击放大 + 可下载 -->
      <div class="kiosk-slot-wrap">
        <ImageSlot
          step="3"
          label="试穿结果"
          hint="点击放大 · 可下载"
          empty-title="等待生成"
          empty-hint="完成人像与衣服后，点击「开始试衣」"
          icon="sparkles"
          :preview="resultUrl"
          :loading="loading"
          :zoomable="!!resultUrl"
          @zoom="openZoom(resultUrl, '试穿结果预览', true)"
        />
      </div>
    </main>

    <!-- ── 操作区 ────────────────────────────────────────── -->
    <section class="relative z-10 shrink-0 px-10 xl:px-16 3xl:px-24 py-7 xl:py-8 3xl:py-12 grid grid-cols-3 items-center gap-4 3xl:gap-8 kiosk-action">
      <!-- 左：分类切换（有衣服时显示） -->
      <div class="flex items-center justify-start">
        <transition name="fade">
          <div
            v-if="clothPreview"
            class="inline-flex items-center gap-1 3xl:gap-2 p-1.5 3xl:p-2.5 rounded-2xl 3xl:rounded-3xl border border-ink-600 bg-ink-800/70 backdrop-blur"
          >
            <button
              v-for="opt in categoryOptions"
              :key="opt.value"
              @click="clothCategory = opt.value"
              :disabled="loading"
              class="px-4 xl:px-5 3xl:px-8 py-2.5 3xl:py-4 rounded-xl 3xl:rounded-2xl text-sm 3xl:text-xl font-medium transition-all active:scale-95"
              :class="clothCategory === opt.value
                ? 'bg-accent text-ink-900 shadow-accent-glow'
                : 'text-ink-300 hover:bg-ink-700/60'"
            >
              <span class="mr-1.5">{{ opt.icon }}</span>{{ opt.label }}
            </button>
          </div>
        </transition>
      </div>

      <!-- 中：开始试衣 大按钮 -->
      <div class="flex flex-col items-center gap-1">
        <button
          @click="handleTryOn"
          :disabled="!canSubmit"
          class="group relative inline-flex items-center justify-center gap-3 3xl:gap-5 px-10 xl:px-14 3xl:px-24 py-4 xl:py-5 3xl:py-8 rounded-2xl 3xl:rounded-3xl font-display font-bold text-base xl:text-lg 3xl:text-3xl tracking-wide transition-all duration-300 min-w-[220px] 3xl:min-w-[400px]"
          :class="canSubmit
            ? 'bg-accent text-ink-900 hover:bg-accent-soft shadow-accent-glow hover:scale-[1.03] active:scale-[0.97]'
            : loading
              ? 'bg-ink-700 text-white/80 cursor-not-allowed'
              : 'bg-ink-700/70 text-ink-500 cursor-not-allowed border border-ink-600/60'"
        >
          <span
            v-if="canSubmit"
            class="absolute inset-0 rounded-2xl 3xl:rounded-3xl blur-xl opacity-50 bg-accent -z-10 transition-opacity group-hover:opacity-75"
          />
          <template v-if="loading">
            <svg class="w-5 h-5 3xl:w-8 3xl:h-8 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25"/>
              <path fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" class="opacity-90"/>
            </svg>
            生成中…
          </template>
          <template v-else>
            <svg class="w-5 h-5 3xl:w-8 3xl:h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
              <path d="M13 2L4.09 13.43a1 1 0 00.77 1.63H10l-1 7 8.91-11.43a1 1 0 00-.77-1.63H14l1-7z" stroke-linejoin="round" stroke-linecap="round"/>
            </svg>
            开始试衣
          </template>
        </button>
      </div>

      <!-- 右：状态 / 进度 / 错误 -->
      <div class="flex items-center justify-end min-w-0">
        <transition name="fade" mode="out-in">
          <div v-if="loading" key="prog" class="w-full max-w-xs 3xl:max-w-md">
            <ProgressBar :progress="progress" label="正在生成…" :subtitle="progressStage" />
          </div>
          <div
            v-else-if="error"
            key="err"
            class="max-w-sm 3xl:max-w-lg px-4 3xl:px-6 py-2.5 3xl:py-4 rounded-xl 3xl:rounded-2xl border border-red-900/60 bg-red-950/30 text-red-300 text-xs 3xl:text-lg flex items-center gap-2 3xl:gap-3 truncate"
          >
            <svg class="w-4 h-4 3xl:w-6 3xl:h-6 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" stroke-linecap="round" />
            </svg>
            <span class="truncate">{{ error }}</span>
          </div>
          <div
            v-else-if="readinessHint"
            key="hint"
            class="px-4 3xl:px-7 py-2.5 3xl:py-4 rounded-full border border-ink-600/70 bg-ink-800/60 text-sm 3xl:text-xl text-ink-400 backdrop-blur"
          >
            {{ readinessHint }}
          </div>
        </transition>
      </div>
    </section>

    <!-- ── 模特相册条(紧凑单行,仅在有模特时显示) ──────────── -->
    <section
      v-if="!modelsLoading && allModels.length"
      class="relative z-10 shrink-0 px-10 xl:px-16 3xl:px-24 pt-3 xl:pt-4 3xl:pt-6 pb-1"
    >
      <div class="flex items-center justify-between mb-2 3xl:mb-3">
        <div class="flex items-center gap-2 3xl:gap-3">
          <span class="w-1 h-4 3xl:w-1.5 3xl:h-7 rounded-full bg-accent" />
          <h3 class="text-sm xl:text-base 3xl:text-2xl font-display font-semibold text-white/90 tracking-wide">
            模特相册
          </h3>
          <span class="text-[11px] xl:text-xs 3xl:text-lg text-ink-500">
            {{ allModels.length }} 位 · 不想拍照?直接选一位
          </span>
        </div>
      </div>

      <div class="relative rounded-2xl 3xl:rounded-3xl border border-ink-700/60 bg-ink-800/30 backdrop-blur-sm">
        <div
          ref="modelDockEl"
          @scroll="onModelDockScroll"
          class="kiosk-model-dock-scroller overflow-x-auto scroll-smooth no-scrollbar"
        >
          <div
            class="flex items-center gap-3 xl:gap-4 3xl:gap-7 px-5 3xl:px-9"
            :class="{ 'justify-center w-full': allModels.length <= 8 }"
          >
            <button
              v-for="m in allModels"
              :key="m.id"
              type="button"
              @click="onModelPresetSelect(m.id)"
              class="kiosk-dock-card relative flex-shrink-0 rounded-xl 3xl:rounded-2xl overflow-hidden border-2 bg-ink-800 transition-all duration-200 active:scale-95"
              :class="selectedModelId === m.id
                ? 'border-accent shadow-accent-glow scale-[1.05]'
                : 'border-ink-600/70 hover:border-ink-500'"
              :title="m.name"
            >
              <div class="relative w-[78px] h-[104px] xl:w-[92px] xl:h-[122px] 3xl:w-[150px] 3xl:h-[200px]">
                <img
                  :src="m.url"
                  :alt="m.name"
                  loading="lazy"
                  class="w-full h-full object-cover"
                />
                <div
                  v-if="selectedModelId === m.id"
                  class="absolute top-1.5 right-1.5 3xl:top-2.5 3xl:right-2.5 w-5 h-5 3xl:w-8 3xl:h-8 rounded-full bg-accent flex items-center justify-center shadow-accent-glow"
                >
                  <svg class="w-3 h-3 3xl:w-5 3xl:h-5 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5">
                    <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ── 底部 Dock(衣服) ──────────────────────────────────── -->
    <section
      ref="dockSectionEl"
      class="relative z-10 shrink-0 px-10 xl:px-16 3xl:px-24 pb-6 xl:pb-8 3xl:pb-12 pt-4 xl:pt-5 3xl:pt-8 kiosk-dock-section"
      :class="{ 'kiosk-dock-pulse': dockPulsing }"
    >
      <!-- 标题 + 分类筛选 -->
      <div class="flex items-center justify-between mb-3 3xl:mb-5">
        <div class="flex items-center gap-2.5 3xl:gap-4">
          <span class="w-1 h-5 3xl:w-1.5 3xl:h-9 rounded-full bg-accent" />
          <h3 class="text-base xl:text-lg 3xl:text-3xl font-display font-semibold text-white/90 tracking-wide">
            服装款式精选
          </h3>
          <span class="text-xs xl:text-sm 3xl:text-xl text-ink-500">
            {{ filteredClothes.length }} 款 · 点击试穿
          </span>
        </div>
        <div class="flex items-center gap-1.5 3xl:gap-2 p-1 3xl:p-2 rounded-2xl 3xl:rounded-3xl border border-ink-600 bg-ink-800/70 backdrop-blur">
          <button
            v-for="c in CATEGORIES"
            :key="c.value"
            @click="setCategory(c.value)"
            class="px-4 3xl:px-7 py-2 3xl:py-3.5 rounded-xl 3xl:rounded-2xl text-sm 3xl:text-xl font-medium transition-all active:scale-95"
            :class="currentCategory === c.value
              ? 'bg-accent text-ink-900 shadow-accent-glow'
              : 'text-ink-400 hover:text-white hover:bg-ink-700/60'"
          >
            <span class="mr-1.5">{{ c.icon }}</span>{{ c.label }}
          </button>
        </div>
      </div>

      <!-- Dock 容器 -->
      <div class="relative rounded-2xl 3xl:rounded-3xl border border-ink-700/60 bg-ink-800/30 backdrop-blur-sm">
        <!-- 首次滑动提示：未滑动且还能向右滚动时显示，带 swipe 动画 -->
        <transition name="fade">
          <div
            v-if="showSwipeHint"
            class="pointer-events-none absolute right-20 3xl:right-32 top-1/2 -translate-y-1/2 z-10 flex items-center gap-2 3xl:gap-3 px-3 py-1.5 3xl:px-5 3xl:py-3 rounded-full bg-ink-900/80 backdrop-blur border border-ink-600 text-xs 3xl:text-lg text-white/85 swipe-hint-anim"
          >
            <span class="text-accent">←</span>
            <span>手指滑动浏览更多</span>
          </div>
        </transition>
        <!-- 左右导航大按钮（触控屏友好） -->
        <button
          v-show="canScrollLeft"
          @click="dockScroll(-dockScrollStep)"
          class="absolute left-2 3xl:left-4 top-1/2 -translate-y-1/2 z-20 w-12 h-12 xl:w-14 xl:h-14 3xl:w-24 3xl:h-24 rounded-full border border-ink-500 bg-ink-900/85 backdrop-blur flex items-center justify-center text-white hover:bg-ink-700 active:scale-90 transition-all shadow-card"
          aria-label="向左滚动"
        >
          <svg class="w-5 h-5 xl:w-6 xl:h-6 3xl:w-10 3xl:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
            <path d="M15 6l-6 6 6 6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button
          v-show="canScrollRight"
          @click="dockScroll(dockScrollStep)"
          class="absolute right-2 3xl:right-4 top-1/2 -translate-y-1/2 z-20 w-12 h-12 xl:w-14 xl:h-14 3xl:w-24 3xl:h-24 rounded-full border border-ink-500 bg-ink-900/85 backdrop-blur flex items-center justify-center text-white hover:bg-ink-700 active:scale-90 transition-all shadow-card"
          aria-label="向右滚动"
        >
          <svg class="w-5 h-5 xl:w-6 xl:h-6 3xl:w-10 3xl:h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
            <path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>

        <div
          ref="dockEl"
          @scroll="onDockScroll"
          class="kiosk-dock-scroller overflow-x-auto scroll-smooth no-scrollbar"
        >
          <div
            class="flex items-center gap-4 xl:gap-5 3xl:gap-8 px-6 3xl:px-10"
            :class="{ 'justify-center w-full': filteredClothes.length <= 6 }"
          >
            <button
              v-for="item in filteredClothes"
              :key="item.id"
              type="button"
              @click="onPresetSelect(item.id)"
              class="kiosk-dock-card snap-card relative flex-shrink-0 rounded-2xl 3xl:rounded-3xl overflow-hidden border-2 3xl:border-[3px] bg-ink-800 transition-all duration-200 active:scale-95"
              :class="selectedPresetId === item.id
                ? 'border-accent shadow-accent-glow scale-[1.04]'
                : 'border-ink-600/70 hover:border-ink-500'"
              :title="item.name"
            >
              <div class="relative w-[132px] h-[176px] xl:w-[152px] xl:h-[203px] 3xl:w-[240px] 3xl:h-[320px]">
                <img
                  :src="item.url || item.thumb"
                  :alt="item.name"
                  loading="lazy"
                  class="w-full h-full object-cover"
                />
                <div class="absolute inset-x-0 bottom-0 px-2.5 3xl:px-4 py-2 3xl:py-3 bg-gradient-to-t from-ink-900/95 via-ink-900/40 to-transparent">
                  <p class="text-[12px] xl:text-[13px] 3xl:text-xl font-medium text-white/90 truncate leading-tight">
                    {{ item.name }}
                  </p>
                </div>
                <div
                  v-if="selectedPresetId === item.id"
                  class="absolute top-2 right-2 3xl:top-3 3xl:right-3 w-6 h-6 3xl:w-10 3xl:h-10 rounded-full bg-accent flex items-center justify-center shadow-accent-glow"
                >
                  <svg class="w-3.5 h-3.5 3xl:w-6 3xl:h-6 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5">
                    <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
              </div>
            </button>

            <!-- 空状态 -->
            <div
              v-if="!clothesLoading && filteredClothes.length === 0"
              class="w-full text-center py-10 text-ink-400 text-sm 3xl:text-xl"
            >
              该分类下暂无衣服，请在后台管理添加
            </div>
            <div
              v-if="clothesLoading"
              class="w-full text-center py-10 text-ink-400 text-sm 3xl:text-xl animate-pulse-soft"
            >
              正在加载衣服库…
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 通用预览弹窗（人物 / 衣服 / 结果共用） -->
    <ResultModal
      :open="zoomOpen"
      :src="zoomSrc"
      :title="zoomTitle"
      :show-download="zoomDownload"
      @close="zoomOpen = false"
    />
    <CameraCapture
      :open="cameraOpen"
      @close="cameraOpen = false"
      @capture="onCameraCaptured"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

import ImageSlot     from '../components/ImageSlot.vue'
import ProgressBar   from '../components/ProgressBar.vue'
import ResultModal   from '../components/ResultModal.vue'
import CameraCapture from '../components/CameraCapture.vue'
import { listClothes, CATEGORIES, DEFAULT_CATEGORY } from '../api/clothes.js'
import { listModels } from '../api/models.js'

const router = useRouter()

/* ── 试衣状态（独立于 HomeView） ──────────────────────── */
const personFile       = ref(null)
const clothFile        = ref(null)
const personPreview    = ref(null)
const clothPreview     = ref(null)
const selectedPresetId = ref(null)
const clothCategory    = ref(DEFAULT_CATEGORY)
const categoryLockedByPreset = ref(false)

const categoryOptions = computed(() => CATEGORIES.filter(c => c.value !== 'all'))

const loading       = ref(false)
const resultUrl     = ref(null)
const error         = ref(null)
const cameraOpen    = ref(false)

/* 通用预览弹窗（人像 / 衣服 / 结果共用） */
const zoomOpen     = ref(false)
const zoomSrc      = ref('')
const zoomTitle    = ref('')
const zoomDownload = ref(false)

function openZoom(src, title, downloadable = false) {
  if (!src) return
  zoomSrc.value = src
  zoomTitle.value = title
  zoomDownload.value = downloadable
  zoomOpen.value = true
}

const progress      = ref(0)
const progressStage = ref('')
let   progressTimer = null

const allClothes      = ref([])
const clothesLoading  = ref(true)
const currentCategory = ref('all')

/* 模特相册状态 */
const allModels        = ref([])
const modelsLoading    = ref(true)
const selectedModelId  = ref(null)

const filteredClothes = computed(() => {
  if (currentCategory.value === 'all') return allClothes.value
  return allClothes.value.filter(c => c.category === currentCategory.value)
})

const canSubmit = computed(() => personFile.value && clothFile.value && !loading.value)

const readinessHint = computed(() => {
  if (loading.value) return ''
  if (!personFile.value && !clothFile.value) return '请先上传/拍摄人像，并选择一件衣服'
  if (!personFile.value) return '还差一步：请上传或拍摄人像'
  if (!clothFile.value)  return '还差一步：请选择或上传衣服'
  return '准备就绪，点击「开始试衣」'
})

/* ── 视口尺寸显示（仅装饰） ──────────────────────────── */
const viewportSize = ref('')
function updateViewport() {
  viewportSize.value = `${window.innerWidth}×${window.innerHeight}`
}

/* ── 加载衣服列表 ──────────────────────────────────────── */
async function loadClothes() {
  clothesLoading.value = true
  try {
    allClothes.value = await listClothes()
  } catch (e) {
    console.error('加载衣服失败', e)
    allClothes.value = []
  } finally {
    clothesLoading.value = false
    await nextTick()
    refreshDockScrollState()
  }
}

/* ── 加载模特相册 ──────────────────────────────────────── */
async function loadModels() {
  modelsLoading.value = true
  try {
    allModels.value = await listModels()
  } catch (e) {
    console.error('加载模特失败', e)
    allModels.value = []
  } finally {
    modelsLoading.value = false
  }
}

function setCategory(c) {
  currentCategory.value = c
  nextTick(refreshDockScrollState)
}

/* ── helpers ──────────────────────────────────────────── */
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
  selectedModelId.value = null
  resetResult()
}

function onCameraCaptured(file) {
  onPersonUpload(file)
}

async function onModelPresetSelect(id) {
  const preset = allModels.value.find(p => p.id === id)
  if (!preset) return
  selectedModelId.value = id
  error.value = null

  revokePreview(personPreview.value)
  personPreview.value = preset.url
  personFile.value = null

  try {
    const file = await urlToFile(preset.url, `${preset.id}.jpg`)
    personFile.value = file
  } catch (e) {
    console.error(e)
    error.value = '加载预设模特失败：' + (e.message || '网络错误')
    selectedModelId.value = null
    personPreview.value = null
  }
  resetResult()
}

function onClothUpload(file) {
  revokePreview(clothPreview.value)
  clothFile.value = file
  clothPreview.value = file ? URL.createObjectURL(file) : null
  selectedPresetId.value = null
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

/* ── 重置 ──────────────────────────────────────────────── */
function resetAll() {
  revokePreview(personPreview.value)
  revokePreview(clothPreview.value)
  personFile.value = null
  personPreview.value = null
  clothFile.value = null
  clothPreview.value = null
  selectedPresetId.value = null
  selectedModelId.value = null
  categoryLockedByPreset.value = false
  clothCategory.value = DEFAULT_CATEGORY
  resultUrl.value = null
  error.value = null
  zoomOpen.value = false
  cameraOpen.value = false
}

/* ── Dock 滚动 ─────────────────────────────────────────── */
const dockEl         = ref(null)
const dockSectionEl  = ref(null)
const modelDockEl    = ref(null)
const canScrollLeft  = ref(false)
const canScrollRight = ref(false)
const dockPulsing    = ref(false)   // 提示性脉冲高亮
const hasSwiped      = ref(false)   // 用户是否已滑过 Dock；首次滑动后提示消失
// 单次点击左右导航按钮滚动的距离（随屏幕宽度自适应：4K 屏滚更多）
const dockScrollStep = computed(() => window.innerWidth >= 2400 ? 880 : 480)
// 首次滑动提示：当 Dock 可向右滚动 且 用户还没滑过时显示
const showSwipeHint  = computed(() => canScrollRight.value && !hasSwiped.value)

/* 模特 Dock 的滚动事件占位(目前仅用于触控滑动,无导航按钮) */
function onModelDockScroll() { /* placeholder for future scroll-state */ }

function refreshDockScrollState() {
  const el = dockEl.value
  if (!el) return
  canScrollLeft.value  = el.scrollLeft > 4
  canScrollRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4
}

function onDockScroll() {
  refreshDockScrollState()
  if (!hasSwiped.value && (canScrollLeft.value || dockEl.value?.scrollLeft > 30)) {
    hasSwiped.value = true
  }
}

function dockScroll(dx) {
  dockEl.value?.scrollBy({ left: dx, behavior: 'smooth' })
  hasSwiped.value = true
}

// 用户点了空衣服槽 → 滚动到 Dock 并脉冲提示
function pulseDock() {
  dockSectionEl.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  dockPulsing.value = true
  setTimeout(() => { dockPulsing.value = false }, 1400)
}

/* ── 全屏控制 ──────────────────────────────────────────── */
async function enterFullscreenIfNeeded() {
  try {
    if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
      await document.documentElement.requestFullscreen({ navigationUI: 'hide' }).catch(() => {})
    }
  } catch (_) { /* 用户拒绝或 API 不支持，忽略 */ }
}

async function exitKiosk() {
  if (document.fullscreenElement) {
    try { await document.exitFullscreen() } catch (_) { /* ignore */ }
  }
  router.push('/')
}

function onFullscreenChange() {
  // 若用户从全屏退出（按 ESC），自动返回首页，避免被卡在小窗口的 kiosk 视图里
  if (!document.fullscreenElement) {
    router.push('/')
  }
}

/* ── 生命周期 ──────────────────────────────────────────── */
onMounted(async () => {
  updateViewport()
  window.addEventListener('resize', updateViewport)
  window.addEventListener('resize', refreshDockScrollState)
  document.addEventListener('fullscreenchange', onFullscreenChange)

  await Promise.all([loadClothes(), loadModels()])
  await enterFullscreenIfNeeded()
})

onBeforeUnmount(() => {
  clearInterval(progressTimer)
  window.removeEventListener('resize', updateViewport)
  window.removeEventListener('resize', refreshDockScrollState)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  revokePreview(personPreview.value)
  revokePreview(clothPreview.value)
})
</script>

<style scoped>
/*
  三栏槽位宽度自适应：
  · 取 (可用高度 - chrome - 额外呼吸空间) × 3/4 作为槽宽
  · "chrome" 预算预留 header + action + dock + 标签行 + 上下呼吸 padding
  · 1080 屏: chrome 预算 620px → 槽宽 ≈ 345px / 高 ≈ 460px，上下与操作行各 ~50px 留白
  · 1440 屏: 上限 460px
  · 4K 屏 (3840×2160): 单独算式，槽宽上限 840px
*/
.kiosk-slot-wrap {
  width: clamp(220px, calc((100vh - 620px) * 0.75), 460px);
  flex-shrink: 0;
}

/* 4K 大屏（65 寸触控屏 3840×2160）整体放大
   chrome 预算 980px → 槽宽 ≈ 885 / 高 ≈ 1180，留 100+px 上下呼吸 */
@media (min-width: 2400px) {
  .kiosk-slot-wrap {
    width: clamp(420px, calc((100vh - 980px) * 0.75), 840px);
  }
}

/* 操作区上下各一条极淡分隔线，清晰区分槽位 / 操作 / Dock */
.kiosk-action {
  position: relative;
}
.kiosk-action::before,
.kiosk-action::after {
  content: '';
  position: absolute;
  left: 8%;
  right: 8%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.08) 30%,
    rgba(255, 255, 255, 0.08) 70%,
    transparent 100%
  );
  pointer-events: none;
}
.kiosk-action::before { top: 0; }
.kiosk-action::after  { bottom: 0; }

/* 触控屏隐藏滚动条但保留滚动能力 */
.no-scrollbar {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.no-scrollbar::-webkit-scrollbar { display: none; }

.kiosk-dock-scroller {
  padding: 12px 0;
  /* 两侧渐隐遮罩，比绝对定位 div 更干净 */
  -webkit-mask-image: linear-gradient(
    90deg, transparent 0, #000 32px, #000 calc(100% - 32px), transparent 100%
  );
          mask-image: linear-gradient(
    90deg, transparent 0, #000 32px, #000 calc(100% - 32px), transparent 100%
  );
  /* 触控屏惯性滚动更顺滑 */
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  /* 滚动吸附：滑动后自动对齐到最近的衣服卡片，触感像翻硬卡片 */
  scroll-snap-type: x proximity;
  scroll-padding-left: 32px;
}

/* 模特 Dock:更紧凑,不需要 snap 吸附 */
.kiosk-model-dock-scroller {
  padding: 8px 0;
  -webkit-mask-image: linear-gradient(
    90deg, transparent 0, #000 24px, #000 calc(100% - 24px), transparent 100%
  );
          mask-image: linear-gradient(
    90deg, transparent 0, #000 24px, #000 calc(100% - 24px), transparent 100%
  );
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
}

.kiosk-dock-card {
  will-change: transform;
  /* 优先把横向触摸传递给 Dock 滚动，避免与垂直手势冲突 */
  touch-action: pan-x;
  -webkit-user-select: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.snap-card {
  scroll-snap-align: start;
  scroll-snap-stop: always;
}

/* 衣服 Dock 接收到点击空衣服槽信号时的脉冲高亮 */
.kiosk-dock-section {
  transition: filter 0.4s ease;
}
.kiosk-dock-pulse {
  animation: dock-pulse 1.4s ease-out;
}
@keyframes dock-pulse {
  0%   { filter: drop-shadow(0 0 0 rgba(200,255,61,0)); transform: translateY(0); }
  20%  { filter: drop-shadow(0 -6px 28px rgba(200,255,61,0.45)); transform: translateY(-4px); }
  60%  { filter: drop-shadow(0 -3px 16px rgba(200,255,61,0.25)); transform: translateY(0); }
  100% { filter: drop-shadow(0 0 0 rgba(200,255,61,0)); transform: translateY(0); }
}

/* 首次滑动提示：左右摆动一下，像在示意"往这边滑" */
.swipe-hint-anim {
  animation: swipe-hint 1.6s ease-in-out infinite;
}
@keyframes swipe-hint {
  0%, 100% { transform: translate(0, -50%); opacity: 0.85; }
  50%      { transform: translate(-14px, -50%); opacity: 1; }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; transform: translateY(4px); }
</style>
