<!--
  ImageSlot.vue
  统一的三栏卡片：人物 / 衣服 / 结果
  - uploadable=true: 支持点击 + 拖拽上传；有图片时 hover 展示“更换”
  - loading=true:   显示骨架 + 扫描动画
  - zoomable=true:  点击图片触发 @zoom (用于结果卡)
-->
<template>
  <div class="relative group w-full flex flex-col">
    <!-- 标签行（内含序号徽章，跨平台不会被遮挡） -->
    <div class="flex items-center justify-between gap-2 mb-3 h-7">
      <div class="flex items-center gap-2 min-w-0">
        <span
          v-if="step"
          class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold font-display border transition-colors"
          :class="[
            preview || loading
              ? 'bg-accent text-ink-900 border-accent shadow-accent-glow'
              : 'bg-ink-800 text-ink-500 border-ink-600'
          ]"
        >{{ step }}</span>
        <span class="text-[13px] font-medium text-white/90 font-display tracking-wide truncate">{{ label }}</span>
        <span v-if="selected" class="flex-shrink-0 px-1.5 py-0.5 rounded-full bg-accent/15 text-accent text-[10px] font-medium border border-accent/30 leading-none">
          已选
        </span>
      </div>
      <span v-if="hint" class="hidden sm:inline text-[11px] text-ink-500 truncate">{{ hint }}</span>
    </div>

    <!-- 卡片本体 -->
    <div
      class="relative rounded-3xl overflow-hidden border transition-all duration-300 aspect-[3/4]"
      :class="[
        isDragging
          ? 'border-accent/60 shadow-accent-glow scale-[1.01]'
          : preview
            ? 'border-ink-600/80 bg-ink-800 shadow-card hover:shadow-card-hover hover:-translate-y-0.5'
            : loading
              ? 'border-accent/40 bg-ink-800 shadow-accent-glow'
              : 'border-dashed border-ink-600 bg-ink-800/60 hover:border-ink-500 hover:bg-ink-800'
      ]"
      :style="{ cursor: cursorClass }"
      @click="onCardClick"
      @dragover.prevent="uploadable && (isDragging = true)"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <!-- 1. 已有预览图 -->
      <template v-if="preview">
        <img
          :src="preview"
          :alt="label"
          loading="lazy"
          class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
        />
        <!-- 顶部渐变让徽章可读 -->
        <div class="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-ink-900/70 to-transparent pointer-events-none" />
        <!-- hover 操作层 -->
        <div
          v-if="uploadable || zoomable || downloadable || capturable"
          class="absolute inset-0 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 bg-ink-900/60 backdrop-blur-[2px]"
        >
          <button
            v-if="uploadable"
            @click.stop="triggerInput"
            class="px-3.5 py-2 rounded-xl bg-white/10 backdrop-blur text-white text-xs font-medium border border-white/15 hover:bg-white/20 transition-all active:scale-95 flex items-center gap-1.5"
          >
            <IconUpload class="w-3.5 h-3.5" />
            更换
          </button>
          <button
            v-if="capturable"
            @click.stop="$emit('capture')"
            class="px-3.5 py-2 rounded-xl bg-white/10 backdrop-blur text-white text-xs font-medium border border-white/15 hover:bg-white/20 transition-all active:scale-95 flex items-center gap-1.5"
          >
            <IconCamera class="w-3.5 h-3.5" />
            重拍
          </button>
          <button
            v-if="zoomable"
            @click.stop="$emit('zoom')"
            class="px-3.5 py-2 rounded-xl bg-white/10 backdrop-blur text-white text-xs font-medium border border-white/15 hover:bg-white/20 transition-all active:scale-95 flex items-center gap-1.5"
          >
            <IconZoom class="w-3.5 h-3.5" />
            放大
          </button>
          <a
            v-if="downloadable"
            :href="preview"
            download="tryon-result.jpg"
            @click.stop
            class="px-3.5 py-2 rounded-xl bg-accent text-ink-900 text-xs font-bold hover:bg-accent-soft transition-all active:scale-95 flex items-center gap-1.5 shadow-accent-glow"
          >
            <IconDownload class="w-3.5 h-3.5" />
            下载
          </a>
        </div>
      </template>

      <!-- 2. 加载 / 生成中 -->
      <div v-else-if="loading" class="absolute inset-0">
        <!-- Skeleton -->
        <div class="absolute inset-0 bg-gradient-to-br from-ink-700 via-ink-800 to-ink-750" />
        <div class="absolute inset-0 opacity-30"
          style="background-image: linear-gradient(90deg, transparent 0%, rgba(200,255,61,0.08) 50%, transparent 100%); background-size: 200% 100%;"
          :style="{ animation: 'shimmer 2s linear infinite' }"
        />
        <!-- 扫描线 -->
        <div class="absolute inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-accent to-transparent animate-scan shadow-[0_0_12px_2px_rgba(200,255,61,0.5)]" />
        <!-- 中心文案 -->
        <div class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-6">
          <div class="w-10 h-10 rounded-xl border border-accent/40 bg-accent/10 flex items-center justify-center">
            <svg class="w-5 h-5 animate-spin text-accent" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
              <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
            </svg>
          </div>
          <p class="text-sm font-medium text-white/90">AI 合成中</p>
          <p class="text-[11px] text-ink-400">稍候，通常需要 30~90 秒</p>
        </div>
      </div>

      <!-- 3. 空状态 -->
      <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6 text-center">
        <div
          class="w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300"
          :class="isDragging
            ? 'bg-accent/15 border border-accent/50 scale-110'
            : 'bg-ink-700 border border-ink-600 group-hover:bg-ink-600'"
        >
          <component :is="iconComponent" class="w-6 h-6 text-ink-400 group-hover:text-white/90 transition-colors" />
        </div>
        <div>
          <p class="text-sm font-medium text-white/90 mb-1 font-display">{{ emptyTitle }}</p>
          <p class="text-[11px] text-ink-400 leading-relaxed">{{ emptyHint }}</p>
        </div>
        <div
          v-if="uploadable"
          class="mt-1 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[11px] transition-all"
          :class="isDragging
            ? 'border-accent/60 text-accent bg-accent/10'
            : 'border-ink-600 text-ink-400 group-hover:border-ink-500 group-hover:text-white/80'"
        >
          <IconUpload class="w-3 h-3" />
          {{ isDragging ? '松开上传' : '点击或拖拽上传' }}
        </div>
        <button
          v-if="capturable"
          @click.stop="$emit('capture')"
          class="mt-1 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-accent/40 text-accent bg-accent/5 hover:bg-accent/10 hover:border-accent/60 text-[11px] transition-all active:scale-95"
        >
          <IconCamera class="w-3 h-3" />
          使用摄像头拍照
        </button>
      </div>

      <!-- 隐藏的 input -->
      <input
        v-if="uploadable"
        ref="inputRef"
        type="file"
        :accept="accept"
        class="hidden"
        @change="onFileChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'

const props = defineProps({
  label:       { type: String, required: true },
  step:        { type: [String, Number], default: '' },
  hint:        { type: String, default: '' },
  emptyTitle:  { type: String, default: '点击上传' },
  emptyHint:   { type: String, default: '' },
  icon:        { type: String, default: 'upload' }, // upload | shirt | sparkles
  accept:      { type: String, default: 'image/*' },
  preview:     { type: String, default: null },
  uploadable:  { type: Boolean, default: false },
  capturable:  { type: Boolean, default: false },
  zoomable:    { type: Boolean, default: false },
  downloadable:{ type: Boolean, default: false },
  loading:     { type: Boolean, default: false },
  selected:    { type: Boolean, default: false },
})

const emit = defineEmits(['upload', 'zoom', 'click', 'capture', 'emptyClick'])

const inputRef = ref(null)
const isDragging = ref(false)

const cursorClass = computed(() => {
  if (props.loading) return 'wait'
  if (props.uploadable || props.zoomable) return 'pointer'
  return 'default'
})

function triggerInput() {
  inputRef.value?.click()
}

function onCardClick() {
  if (props.loading) return
  if (props.preview && props.zoomable) {
    emit('zoom')
    return
  }
  // 空状态：触控屏场景中常见的"只拍照、不上传"模式
  if (!props.preview && props.capturable && !props.uploadable) {
    emit('capture')
    return
  }
  if (props.uploadable) triggerInput()
  else emit('emptyClick')
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (file) emit('upload', file)
  e.target.value = ''
}

function onDrop(e) {
  isDragging.value = false
  if (!props.uploadable) return
  const file = e.dataTransfer.files?.[0]
  if (file) emit('upload', file)
}

/* ── SVG 图标组件 ─────────────────────────────────────────── */
const IconUpload = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M12 4v12m0-12l-4 4m4-4l4 4M4 20h16', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
  ]),
}
const IconZoom = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('circle', { cx: 11, cy: 11, r: 7 }),
    h('path', { d: 'M21 21l-4.35-4.35M9 11h4M11 9v4', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
  ]),
}
const IconDownload = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M12 4v12m0 0l-4-4m4 4l4-4M4 20h16', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
  ]),
}
const IconCamera = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z', 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }),
    h('circle', { cx: 12, cy: 13, r: 4 }),
  ]),
}
const IconPerson = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8 }, [
    h('circle', { cx: 12, cy: 8, r: 4 }),
    h('path', { d: 'M4 21c0-4.5 3.5-7 8-7s8 2.5 8 7', 'stroke-linecap': 'round' }),
  ]),
}
const IconShirt = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8 }, [
    h('path', { d: 'M4 7l4-3 2 2h4l2-2 4 3-2 4h-2v9H8v-9H6L4 7z', 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }),
  ]),
}
const IconSparkles = {
  render: () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.8 }, [
    h('path', { d: 'M12 3l1.8 4.6L18 9l-4.2 1.6L12 15l-1.8-4.4L6 9l4.2-1.4L12 3z', 'stroke-linejoin': 'round' }),
    h('path', { d: 'M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15z', 'stroke-linejoin': 'round' }),
  ]),
}

const iconComponent = computed(() => {
  switch (props.icon) {
    case 'person':   return IconPerson
    case 'shirt':    return IconShirt
    case 'sparkles': return IconSparkles
    default:         return IconUpload
  }
})
</script>

<style scoped>
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
