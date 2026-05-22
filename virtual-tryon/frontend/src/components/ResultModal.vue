<!--
  ResultModal.vue
  通用图片放大预览弹窗：ESC / 遮罩点击关闭
  · 默认用于试穿结果，支持下载
  · 也用于人物 / 衣服等其他场景预览，通过 title / showDownload 控制
-->
<template>
  <transition name="modal">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8"
      @click.self="$emit('close')"
    >
      <!-- 遮罩 -->
      <div class="absolute inset-0 bg-ink-950/85 backdrop-blur-md" />

      <!-- 内容 -->
      <div class="relative max-w-5xl w-full max-h-[90vh] flex flex-col">
        <!-- 顶部工具栏 -->
        <div class="flex items-center justify-between mb-3 px-1">
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-soft" />
            <span class="text-sm 3xl:text-xl font-display font-medium text-white/90 tracking-wide">{{ title }}</span>
          </div>
          <div class="flex items-center gap-2">
            <a
              v-if="showDownload"
              :href="src"
              :download="downloadName"
              class="inline-flex items-center gap-1.5 px-3.5 py-1.5 3xl:px-6 3xl:py-3 rounded-lg 3xl:rounded-xl bg-accent text-ink-900 text-xs 3xl:text-lg font-bold hover:bg-accent-soft transition-all active:scale-95 shadow-accent-glow"
            >
              <svg class="w-3.5 h-3.5 3xl:w-5 3xl:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
                <path d="M12 4v12m0 0l-4-4m4 4l4-4M4 20h16" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              下载图片
            </a>
            <button
              @click="$emit('close')"
              class="w-8 h-8 3xl:w-14 3xl:h-14 rounded-lg 3xl:rounded-xl border border-ink-600 bg-ink-800/80 backdrop-blur flex items-center justify-center text-ink-400 hover:text-white hover:bg-ink-700 transition-all active:scale-90"
              aria-label="关闭"
            >
              <svg class="w-4 h-4 3xl:w-6 3xl:h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18L18 6" stroke-linecap="round" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 图片 -->
        <div class="relative flex-1 flex items-center justify-center rounded-2xl overflow-hidden border border-ink-700 bg-ink-800 shadow-card-hover thin-scrollbar">
          <img
            v-if="src"
            :src="src"
            :alt="title"
            class="max-h-[82vh] w-auto object-contain"
          />
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  open:         { type: Boolean, default: false },
  src:          { type: String,  default: '' },
  title:        { type: String,  default: '试穿结果预览' },
  showDownload: { type: Boolean, default: true },
  downloadName: { type: String,  default: 'tryon-result.jpg' },
})
const emit = defineEmits(['close'])

function onKey(e) {
  if (e.key === 'Escape' && props.open) emit('close')
}

onMounted(() => document.addEventListener('keydown', onKey))
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))

watch(() => props.open, (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
})
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.25s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: transform 0.35s cubic-bezier(0.22,1,0.36,1), opacity 0.25s;
}
.modal-enter-from > div:last-child {
  transform: scale(0.95) translateY(16px);
  opacity: 0;
}
.modal-leave-to > div:last-child {
  transform: scale(0.98) translateY(8px);
  opacity: 0;
}
</style>
