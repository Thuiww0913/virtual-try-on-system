<!--
  AdminModelsGrid.vue
  模特相册管理网格(与 AdminClothesGrid 对称,但无分类):
  - 拖拽排序
  - 行内编辑名称
  - 删除(带二次确认)
-->
<template>
  <div class="rounded-2xl border border-ink-700 bg-ink-800/60 backdrop-blur-md p-5">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <span class="w-1 h-4 rounded-full bg-accent" />
        <h3 class="text-sm font-display font-semibold tracking-wide text-white/90">模特相册管理</h3>
        <span class="text-[11px] text-ink-400 ml-1">共 {{ items.length }} 位</span>
      </div>
    </div>

    <p v-if="items.length > 1"
       class="text-[11px] text-ink-500 mb-3 flex items-center gap-1.5">
      <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 5h6M9 12h6M9 19h6" stroke-linecap="round" />
      </svg>
      拖动卡片可调整在前台模特 Dock 中的展示顺序
    </p>

    <div v-if="items.length"
         class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      <div
        v-for="(item, idx) in items"
        :key="item.id"
        draggable="true"
        @dragstart="onDragStart(idx, $event)"
        @dragover.prevent="onDragOver(idx, $event)"
        @dragleave="onDragLeave"
        @drop.prevent="onDrop(idx)"
        @dragend="onDragEnd"
        class="group relative rounded-2xl overflow-hidden border bg-ink-900/60 transition-all cursor-grab active:cursor-grabbing"
        :class="[
          dragOverIdx === idx && draggingIdx !== null && draggingIdx !== idx
            ? 'border-accent shadow-accent-glow scale-[1.02]'
            : 'border-ink-700 hover:border-ink-600 hover:shadow-card-hover',
          draggingIdx === idx ? 'opacity-40' : ''
        ]"
      >
        <div class="relative aspect-[3/4] bg-ink-800">
          <img :src="item.url" :alt="item.name"
               loading="lazy"
               class="w-full h-full object-cover" />
          <div class="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-ink-900/80 backdrop-blur text-[10px] text-white/80 border border-white/10">
            模特
          </div>
          <div class="absolute top-2 right-2 w-6 h-6 rounded-md bg-ink-900/80 backdrop-blur flex items-center justify-center text-[10px] font-mono font-semibold text-ink-300 border border-white/10">
            {{ idx + 1 }}
          </div>
        </div>

        <div class="p-3">
          <input
            v-model="item.name"
            @blur="onNameBlur(item)"
            @keyup.enter="$event.target.blur()"
            class="w-full bg-transparent text-sm text-white/90 truncate font-medium focus:outline-none border-b border-transparent focus:border-accent/40 transition-colors"
            maxlength="60"
          />
          <div class="mt-2 flex items-center justify-end">
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

    <div v-else class="text-center py-16 px-4 rounded-2xl border border-dashed border-ink-600 bg-ink-900/30">
      <div class="w-12 h-12 mx-auto mb-3 rounded-2xl bg-ink-700 border border-ink-600 flex items-center justify-center">
        <svg class="w-5 h-5 text-ink-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="8" r="4" stroke-linecap="round" />
          <path d="M4 20c0-4 4-7 8-7s8 3 8 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
      <p class="text-sm text-ink-300">还没有模特,使用上方上传第一位吧</p>
    </div>

    <transition name="modal">
      <div v-if="pendingDelete"
           class="fixed inset-0 z-50 flex items-center justify-center px-4"
           @click.self="pendingDelete = null">
        <div class="absolute inset-0 bg-ink-950/80 backdrop-blur-md" />
        <div class="relative w-full max-w-sm rounded-2xl border border-ink-700 bg-ink-800 p-6 shadow-card-hover">
          <h4 class="text-base font-display font-semibold text-white mb-2">确认删除?</h4>
          <p class="text-xs text-ink-400 mb-1">将永久删除模特:</p>
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
import { ref } from 'vue'
import { patchModel, deleteModel, reorderModels } from '../api/admin.js'

const props = defineProps({
  items: { type: Array, required: true },
})
const emit = defineEmits(['changed', 'error'])

const draggingIdx = ref(null)
const dragOverIdx = ref(null)
const pendingDelete = ref(null)

async function onNameBlur(item) {
  try {
    await patchModel(item.id, { name: item.name })
    emit('changed')
  } catch (e) {
    emit('error', e?.response?.data?.detail || '更新失败')
  }
}

function confirmDelete(item) {
  pendingDelete.value = item
}
async function doDelete() {
  if (!pendingDelete.value) return
  try {
    await deleteModel(pendingDelete.value.id)
    pendingDelete.value = null
    emit('changed')
  } catch (e) {
    emit('error', e?.response?.data?.detail || '删除失败')
  }
}

function onDragStart(idx, e) {
  draggingIdx.value = idx
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(idx))
}
function onDragOver(idx) {
  if (draggingIdx.value === null) return
  dragOverIdx.value = idx
}
function onDragLeave() { /* noop */ }
async function onDrop(targetIdx) {
  const from = draggingIdx.value
  draggingIdx.value = null
  dragOverIdx.value = null
  if (from === null || from === targetIdx) return

  const list = [...props.items]
  const [moved] = list.splice(from, 1)
  list.splice(targetIdx, 0, moved)

  try {
    await reorderModels(list.map(x => x.id))
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
