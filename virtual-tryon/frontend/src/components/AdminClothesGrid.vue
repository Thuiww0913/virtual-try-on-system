<!--
  AdminClothesGrid.vue
  衣服管理网格：
  - 拖拽排序（HTML5 native drag and drop）
  - 行内编辑名称
  - 切换分类
  - 删除（带二次确认）
-->
<template>
  <div class="rounded-2xl border border-ink-700 bg-ink-800/60 backdrop-blur-md p-5">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <span class="w-1 h-4 rounded-full bg-accent" />
        <h3 class="text-sm font-display font-semibold tracking-wide text-white/90">衣服管理</h3>
        <span class="text-[11px] text-ink-400 ml-1">共 {{ filtered.length }} / {{ items.length }} 件</span>
      </div>

      <!-- 分类过滤 -->
      <div class="flex items-center gap-1 flex-wrap">
        <button
          v-for="c in CATEGORIES"
          :key="c.value"
          @click="filterCat = c.value"
          class="px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-all active:scale-95"
          :class="filterCat === c.value
            ? 'bg-accent/15 text-accent border-accent/40'
            : 'bg-ink-900/40 text-ink-400 border-ink-600 hover:border-ink-500 hover:text-white'"
        >
          {{ c.icon }} {{ c.label }}
        </button>
      </div>
    </div>

    <!-- 拖拽排序提示 -->
    <p v-if="filtered.length > 1 && filterCat === 'all'"
       class="text-[11px] text-ink-500 mb-3 flex items-center gap-1.5">
      <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 5h6M9 12h6M9 19h6" stroke-linecap="round" />
      </svg>
      拖动卡片可调整在前台 Dock 中的展示顺序
    </p>

    <!-- 网格 -->
    <div v-if="filtered.length"
         class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      <div
        v-for="(item, idx) in filtered"
        :key="item.id"
        :draggable="filterCat === 'all'"
        @dragstart="onDragStart(idx, $event)"
        @dragover.prevent="onDragOver(idx, $event)"
        @dragleave="onDragLeave"
        @drop.prevent="onDrop(idx)"
        @dragend="onDragEnd"
        class="group relative rounded-2xl overflow-hidden border bg-ink-900/60 transition-all"
        :class="[
          dragOverIdx === idx && draggingIdx !== null && draggingIdx !== idx
            ? 'border-accent shadow-accent-glow scale-[1.02]'
            : 'border-ink-700 hover:border-ink-600 hover:shadow-card-hover',
          draggingIdx === idx ? 'opacity-40' : '',
          filterCat === 'all' ? 'cursor-grab active:cursor-grabbing' : ''
        ]"
      >
        <!-- 图片 -->
        <div class="relative aspect-[3/4] bg-ink-800">
          <img :src="item.url" :alt="item.name"
               loading="lazy"
               class="w-full h-full object-cover" />
          <!-- 顶部分类徽标 -->
          <div class="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-ink-900/80 backdrop-blur text-[10px] text-white/80 border border-white/10">
            {{ CATEGORY_LABEL[item.category] || '其他' }}
          </div>
          <!-- 顺序角标 -->
          <div class="absolute top-2 right-2 w-6 h-6 rounded-md bg-ink-900/80 backdrop-blur flex items-center justify-center text-[10px] font-mono font-semibold text-ink-300 border border-white/10">
            {{ idx + 1 }}
          </div>
        </div>

        <!-- 信息 + 编辑 -->
        <div class="p-3">
          <input
            v-model="item.name"
            @blur="onNameBlur(item)"
            @keyup.enter="$event.target.blur()"
            class="w-full bg-transparent text-sm text-white/90 truncate font-medium focus:outline-none border-b border-transparent focus:border-accent/40 transition-colors"
            maxlength="60"
          />
          <div class="mt-2 flex items-center justify-between">
            <select
              :value="item.category"
              @change="onCategoryChange(item, $event.target.value)"
              class="text-[10px] bg-ink-700 border border-ink-600 rounded-md px-1.5 py-0.5 text-ink-300 focus:outline-none focus:border-accent/50"
            >
              <option v-for="c in editCategories" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </select>
            <button
              @click="confirmDelete(item)"
              class="text-[10px] px-2 py-0.5 rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 hover:border-red-500/40 transition-all active:scale-95"
              title="删除"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空态 -->
    <div v-else class="text-center py-16 px-4 rounded-2xl border border-dashed border-ink-600 bg-ink-900/30">
      <div class="w-12 h-12 mx-auto mb-3 rounded-2xl bg-ink-700 border border-ink-600 flex items-center justify-center">
        <svg class="w-5 h-5 text-ink-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 7l4-3 2 2h4l2-2 4 3-2 4h-2v9H8v-9H6L4 7z" stroke-linejoin="round" stroke-linecap="round" />
        </svg>
      </div>
      <p class="text-sm text-ink-300">{{ items.length === 0 ? '还没有衣服，使用上方上传第一件吧' : '该分类下暂无衣服' }}</p>
    </div>

    <!-- 删除确认 -->
    <transition name="modal">
      <div v-if="pendingDelete"
           class="fixed inset-0 z-50 flex items-center justify-center px-4"
           @click.self="pendingDelete = null">
        <div class="absolute inset-0 bg-ink-950/80 backdrop-blur-md" />
        <div class="relative w-full max-w-sm rounded-2xl border border-ink-700 bg-ink-800 p-6 shadow-card-hover">
          <h4 class="text-base font-display font-semibold text-white mb-2">确认删除？</h4>
          <p class="text-xs text-ink-400 mb-1">将永久删除衣服：</p>
          <p class="text-sm text-white/90 mb-5 truncate">{{ pendingDelete.name }}</p>
          <div class="flex gap-2">
            <button
              @click="pendingDelete = null"
              class="flex-1 px-4 py-2 rounded-lg text-xs text-ink-300 bg-ink-700 hover:bg-ink-600 transition-colors"
            >
              取消
            </button>
            <button
              @click="doDelete"
              class="flex-1 px-4 py-2 rounded-lg text-xs font-medium bg-red-500 text-white hover:bg-red-600 transition-colors active:scale-95"
            >
              确认删除
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CATEGORIES, CATEGORY_LABEL } from '../api/clothes.js'
import { patchCloth, deleteCloth, reorderClothes } from '../api/admin.js'

const props = defineProps({
  items: { type: Array, required: true },
})
const emit = defineEmits(['changed', 'error'])

const filterCat   = ref('all')
const draggingIdx = ref(null)
const dragOverIdx = ref(null)

const editCategories = computed(() => CATEGORIES.filter(c => c.value !== 'all'))

const filtered = computed(() => {
  if (filterCat.value === 'all') return props.items
  return props.items.filter(x => x.category === filterCat.value)
})

const pendingDelete = ref(null)

/* ── 编辑 ────────────────────────────────────────── */
async function onNameBlur(item) {
  try {
    await patchCloth(item.id, { name: item.name })
    emit('changed')
  } catch (e) {
    emit('error', e?.response?.data?.detail || '更新失败')
  }
}

async function onCategoryChange(item, value) {
  try {
    await patchCloth(item.id, { category: value })
    item.category = value
    emit('changed')
  } catch (e) {
    emit('error', e?.response?.data?.detail || '更新失败')
  }
}

/* ── 删除 ────────────────────────────────────────── */
function confirmDelete(item) {
  pendingDelete.value = item
}
async function doDelete() {
  if (!pendingDelete.value) return
  try {
    await deleteCloth(pendingDelete.value.id)
    pendingDelete.value = null
    emit('changed')
  } catch (e) {
    emit('error', e?.response?.data?.detail || '删除失败')
  }
}

/* ── 拖拽排序（仅 all 视图下生效） ─────────────────── */
function onDragStart(idx, e) {
  if (filterCat.value !== 'all') return
  draggingIdx.value = idx
  e.dataTransfer.effectAllowed = 'move'
  // Firefox 需要 setData 才会触发 drag
  e.dataTransfer.setData('text/plain', String(idx))
}
function onDragOver(idx) {
  if (draggingIdx.value === null) return
  dragOverIdx.value = idx
}
function onDragLeave() {
  // noop（dragOverIdx 在 dragover 持续更新即可）
}
async function onDrop(targetIdx) {
  const from = draggingIdx.value
  draggingIdx.value = null
  dragOverIdx.value = null
  if (from === null || from === targetIdx || filterCat.value !== 'all') return

  // 在 props.items 中移动元素并提交新顺序
  const list = [...props.items]
  const [moved] = list.splice(from, 1)
  list.splice(targetIdx, 0, moved)

  // 乐观更新本地（emit changed 之后父组件会刷新）
  try {
    await reorderClothes(list.map(x => x.id))
    emit('changed')
  } catch (e) {
    emit('error', e?.response?.data?.detail || '排序保存失败')
  }
}
function onDragEnd() {
  draggingIdx.value = null
  dragOverIdx.value = null
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to       { opacity: 0; }
</style>
