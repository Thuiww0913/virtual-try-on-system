<!--
  AdminUploader.vue
  批量上传衣服：拖拽 / 点击；支持选择分类和重命名前缀
-->
<template>
  <div class="rounded-2xl border border-ink-700 bg-ink-800/60 backdrop-blur-md p-5">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="w-1 h-4 rounded-full bg-accent" />
        <h3 class="text-sm font-display font-semibold tracking-wide text-white/90">上传新衣服</h3>
      </div>
      <span class="text-[11px] text-ink-400">支持拖拽 · 一次最多 20 张</span>
    </div>

    <!-- 拖拽区 -->
    <div
      class="relative rounded-2xl border-2 border-dashed transition-all px-6 py-8 text-center cursor-pointer"
      :class="isDragging
        ? 'border-accent/60 bg-accent/5 scale-[1.005]'
        : 'border-ink-600 bg-ink-900/40 hover:border-ink-500 hover:bg-ink-900/60'"
      @click="triggerInput"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <div class="w-12 h-12 mx-auto mb-3 rounded-2xl flex items-center justify-center transition-all"
           :class="isDragging ? 'bg-accent/20 border border-accent/50 scale-110' : 'bg-ink-700 border border-ink-600'">
        <svg class="w-5 h-5" :class="isDragging ? 'text-accent' : 'text-ink-400'"
             viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 4v12m0-12l-4 4m4-4l4 4M4 20h16"
                stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
      <p class="text-sm font-medium text-white/90 mb-1">
        {{ isDragging ? '松开以上传' : '点击或拖拽图片到这里' }}
      </p>
      <p class="text-[11px] text-ink-400">jpg / png / webp · 单张建议 ≤ 5MB</p>

      <input
        ref="inputRef"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/jpg"
        multiple
        class="hidden"
        @change="onChange"
      />
    </div>

    <!-- 选择 + 操作 -->
    <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
      <div>
        <label class="block text-[11px] text-ink-400 mb-1.5">分类</label>
        <select
          v-model="category"
          class="w-full px-3 py-2 rounded-lg bg-ink-900/60 border border-ink-600 text-sm text-white focus:outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/15"
        >
          <option v-for="c in uploadCategories" :key="c.value" :value="c.value">
            {{ c.icon }} {{ c.label }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-[11px] text-ink-400 mb-1.5">名称（可选，留空使用文件名）</label>
        <input
          v-model="customName"
          maxlength="60"
          placeholder="例：经典白T"
          class="w-full px-3 py-2 rounded-lg bg-ink-900/60 border border-ink-600 text-sm text-white placeholder-ink-500 focus:outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/15"
        />
      </div>
    </div>

    <!-- 待上传预览 -->
    <transition name="fade">
      <div v-if="files.length" class="mt-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] text-ink-400">已选择 {{ files.length }} 个文件</span>
          <button
            type="button"
            @click="files = []"
            class="text-[11px] text-ink-400 hover:text-white"
          >
            清空
          </button>
        </div>
        <div class="grid grid-cols-6 gap-2">
          <div
            v-for="(f, i) in files"
            :key="i"
            class="relative rounded-lg overflow-hidden border border-ink-700 aspect-square group"
          >
            <img :src="previewUrls[i]" :alt="f.name" class="w-full h-full object-cover" />
            <button
              type="button"
              @click="removeFile(i)"
              class="absolute top-1 right-1 w-5 h-5 rounded-full bg-ink-900/80 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-500 transition-all"
              title="移除"
            >
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18L18 6" stroke-linecap="round" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 上传按钮 -->
        <button
          type="button"
          @click="handleUpload"
          :disabled="uploading"
          class="mt-4 w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-display font-semibold transition-all"
          :class="uploading
            ? 'bg-ink-700 text-ink-500 cursor-not-allowed'
            : 'bg-accent text-ink-900 hover:bg-accent-soft shadow-accent-glow active:scale-[0.98]'"
        >
          <svg v-if="uploading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" />
            <path fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" class="opacity-90" />
          </svg>
          <template v-else>
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </template>
          {{ uploading ? `上传中… (${progress}/${files.length})` : `上传 ${files.length} 个文件` }}
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { uploadClothes } from '../api/admin.js'
import { CATEGORIES, DEFAULT_CATEGORY } from '../api/clothes.js'

const emit = defineEmits(['uploaded', 'error'])

const inputRef    = ref(null)
const files       = ref([])
const previewUrls = ref([])
const isDragging  = ref(false)
const category    = ref(DEFAULT_CATEGORY)
const customName  = ref('')
const uploading   = ref(false)
const progress    = ref(0)

// 上传时不展示 "全部"
const uploadCategories = computed(() => CATEGORIES.filter(c => c.value !== 'all'))

function triggerInput() { inputRef.value?.click() }

function onChange(e) {
  addFiles([...(e.target.files || [])])
  e.target.value = ''
}
function onDrop(e) {
  isDragging.value = false
  addFiles([...(e.dataTransfer.files || [])])
}

function addFiles(list) {
  const imgs = list.filter(f => f.type.startsWith('image/')).slice(0, 20 - files.value.length)
  files.value.push(...imgs)
}

function removeFile(i) { files.value.splice(i, 1) }

watch(files, (list) => {
  // 清理旧 preview
  previewUrls.value.forEach(u => URL.revokeObjectURL(u))
  previewUrls.value = list.map(f => URL.createObjectURL(f))
}, { deep: true })

onBeforeUnmount(() => previewUrls.value.forEach(u => URL.revokeObjectURL(u)))

async function handleUpload() {
  if (!files.value.length || uploading.value) return
  uploading.value = true
  progress.value  = 0
  try {
    // 后端一次接收多文件，progress 简单逐张展示
    const created = await uploadClothes(files.value, {
      category: category.value,
      name:     customName.value.trim(),
    })
    progress.value = files.value.length
    emit('uploaded', created)
    files.value = []
    customName.value = ''
  } catch (e) {
    emit('error', e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: all 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(8px); }
</style>
