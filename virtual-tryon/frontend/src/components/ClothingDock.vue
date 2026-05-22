<!--
  ClothingDock.vue
  Mac 风格的 Dock 衣服选择器：
  - 鼠标靠近时项目按距离平滑放大
  - 鼠标移出立即还原
  - 横向滚动 / 鼠标滚轮横滚 / 左右按钮
  - 容器留有充足上方留白，放大效果不会被裁剪
-->
<template>
  <div class="relative animate-fade-up">
    <!-- 标题行 -->
    <div class="flex items-end justify-between mb-3 px-1">
      <div class="flex items-center gap-2">
        <span class="w-1 h-4 rounded-full bg-accent" />
        <h3 class="text-[13px] font-display font-semibold tracking-wide text-white/90">
          服装款式精选
        </h3>
        <span class="text-[11px] text-ink-500">{{ items.length }} 款 · 点击试穿</span>
      </div>

      <div class="hidden md:flex items-center gap-1.5">
        <button
          class="w-7 h-7 rounded-full border border-ink-600/80 bg-ink-800/70 backdrop-blur flex items-center justify-center text-ink-400 hover:text-white hover:border-ink-500 hover:bg-ink-700/80 transition-all active:scale-90"
          :disabled="!canScrollLeft"
          :class="{ 'opacity-30 cursor-not-allowed': !canScrollLeft }"
          @click="scrollByDx(-360)"
          aria-label="向左滚动"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 6l-6 6 6 6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button
          class="w-7 h-7 rounded-full border border-ink-600/80 bg-ink-800/70 backdrop-blur flex items-center justify-center text-ink-400 hover:text-white hover:border-ink-500 hover:bg-ink-700/80 transition-all active:scale-90"
          :disabled="!canScrollRight"
          :class="{ 'opacity-30 cursor-not-allowed': !canScrollRight }"
          @click="scrollByDx(360)"
          aria-label="向右滚动"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
    </div>

    <!--
      Dock 容器
      关键点：
      1. 外壳 rounded + border + 自带 mask-image 渐隐两侧
      2. 内部 scroller 使用充裕的 padding-top（≥ 放大额外高度）
         以避免 overflow-x:auto 强制 overflow-y:auto 时裁剪悬浮放大
    -->
    <div class="relative rounded-2xl border border-ink-700/60 bg-ink-800/30 backdrop-blur-sm">
      <div
        ref="scroller"
        class="dock-scroller no-scrollbar overflow-x-auto scroll-smooth"
        @scroll="onScroll"
        @mousemove="onMouseMove"
        @mouseleave="mouseX = null"
        @wheel="onWheel"
      >
        <div
          class="flex items-end gap-3 px-5 min-w-max"
          :class="{ 'mx-auto justify-center w-full': items.length <= 6 }"
        >
          <button
            v-for="(item, idx) in items"
            :key="item.id"
            ref="itemRefs"
            type="button"
            class="dock-item relative flex-shrink-0 rounded-xl overflow-hidden border bg-ink-800 transition-[border-color,box-shadow] duration-200 ease-out"
            :class="[
              modelValue === item.id
                ? 'border-accent shadow-accent-glow'
                : 'border-ink-600/60 hover:border-ink-500'
            ]"
            :style="getItemStyle(idx)"
            @click="$emit('update:modelValue', item.id)"
            :title="item.name"
          >
            <div class="relative w-[88px] h-[112px]">
              <img
                :src="item.url || item.thumb"
                :alt="item.name"
                loading="lazy"
                class="w-full h-full object-cover"
              />
              <!-- 选中描边 -->
              <div
                v-if="modelValue === item.id"
                class="absolute inset-0 ring-2 ring-inset ring-accent/70 rounded-xl pointer-events-none"
              />
              <!-- 底部名称渐变 -->
              <div class="absolute inset-x-0 bottom-0 px-2 py-1.5 bg-gradient-to-t from-ink-900/95 via-ink-900/40 to-transparent">
                <p class="text-[10px] font-medium text-white/90 truncate leading-tight">{{ item.name }}</p>
              </div>
              <!-- 选中勾选 -->
              <div
                v-if="modelValue === item.id"
                class="absolute top-1.5 right-1.5 w-4 h-4 rounded-full bg-accent flex items-center justify-center shadow-accent-glow"
              >
                <svg class="w-2.5 h-2.5 text-ink-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5">
                  <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  items:      { type: Array,  required: true },
  modelValue: { type: [String, Number], default: null },
})
defineEmits(['update:modelValue'])

const scroller = ref(null)
const itemRefs = ref([])
const mouseX   = ref(null)

const canScrollLeft  = ref(false)
const canScrollRight = ref(true)

/* ── Dock 放大：根据鼠标距离计算缩放 ────────────────────────── */
const MAX_SCALE = 1.22
const RADIUS    = 140      // 生效范围（px）
const MAX_LIFT  = 6        // 上浮幅度（px）

function getItemStyle(idx) {
  if (mouseX.value == null) {
    return { transform: 'translateY(0) scale(1)' }
  }
  const el = itemRefs.value[idx]
  if (!el) return {}
  const rect = el.getBoundingClientRect()
  const center = rect.left + rect.width / 2
  const d = Math.abs(mouseX.value - center)
  if (d > RADIUS) return { transform: 'translateY(0) scale(1)' }
  const t = 1 - d / RADIUS
  // easeOutCubic 让中心更平滑
  const eased = 1 - Math.pow(1 - t, 3)
  const scale = 1 + (MAX_SCALE - 1) * eased
  const lift  = MAX_LIFT * eased
  return {
    transform: `translateY(-${lift}px) scale(${scale})`,
    zIndex: Math.round(eased * 10) + 1,
    transformOrigin: 'bottom center',
  }
}

function onMouseMove(e) {
  mouseX.value = e.clientX
}

function onWheel(e) {
  // 横向滚动支持：垂直滚轮转换为水平
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && scroller.value) {
    scroller.value.scrollLeft += e.deltaY
    e.preventDefault()
  }
}

function scrollByDx(dx) {
  scroller.value?.scrollBy({ left: dx, behavior: 'smooth' })
}

function onScroll() {
  const el = scroller.value
  if (!el) return
  canScrollLeft.value  = el.scrollLeft > 4
  canScrollRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4
}

onMounted(async () => {
  await nextTick()
  onScroll()
  window.addEventListener('resize', onScroll)
})
onBeforeUnmount(() => window.removeEventListener('resize', onScroll))
</script>

<style scoped>
/*
  关键修复：
  1. scroller 给足上方 padding，让放大的 dock-item 不会被裁剪。
     112px * 0.22 = ~25px 增高 + 6px lift = ~31px → padding-top 40px 留有余量
  2. 用 mask-image 实现两侧渐隐，比绝对定位的遮罩 div 更干净，
     不会与 dock-item 的 z-index/hover 冲突
*/
.dock-scroller {
  padding: 40px 0 14px;
  -webkit-mask-image: linear-gradient(
    90deg,
    transparent 0,
    #000 32px,
    #000 calc(100% - 32px),
    transparent 100%
  );
          mask-image: linear-gradient(
    90deg,
    transparent 0,
    #000 32px,
    #000 calc(100% - 32px),
    transparent 100%
  );
}

.dock-item {
  /* 用 transform 单独走 GPU，避免 box-shadow 抖动 */
  will-change: transform;
}
</style>
