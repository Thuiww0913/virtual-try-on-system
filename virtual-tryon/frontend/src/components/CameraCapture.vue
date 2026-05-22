<!--
  CameraCapture.vue
  调用本机摄像头拍照（支持多摄像头切换：FaceTime / 外接 USB 摄像头）
  - 通过 navigator.mediaDevices.getUserMedia 获取视频流
  - 取景容器固定 3:4，video 使用 object-cover：所见即所得
  - 拍照时按中心 3:4 比例裁切源视频帧，并输出 768×1024 的 JPEG
    （正好是 OOTDiffusion 的输入尺寸，避免 resize 拉伸变形）
  - 通过 @capture 事件抛给父组件，复用现有上传链路
-->
<template>
  <transition name="modal">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8"
      @click.self="handleClose"
    >
      <!-- 遮罩 -->
      <div class="absolute inset-0 bg-ink-950/85 backdrop-blur-md" />

      <!-- 内容 -->
      <div class="relative max-w-md w-full max-h-[92vh] flex flex-col">
        <!-- 顶部工具栏 -->
        <div class="flex items-center justify-between mb-3 px-1 gap-3">
          <div class="flex items-center gap-2 min-w-0">
            <span class="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-soft flex-shrink-0" />
            <span class="text-sm font-display font-medium text-white/90 tracking-wide flex-shrink-0">
              摄像头拍照
            </span>
            <span class="hidden sm:inline text-[10px] text-accent/80 border border-accent/30 bg-accent/10 px-1.5 py-0.5 rounded-md font-medium">
              3:4 · 768×1024
            </span>
          </div>
          <div class="flex items-center gap-2">
            <!-- 摄像头选择（>= 2 个时显示） -->
            <div
              v-if="devices.length > 1 && !captured"
              class="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-ink-600 bg-ink-800/80 backdrop-blur"
            >
              <svg class="w-3.5 h-3.5 text-ink-400 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" stroke-linejoin="round" stroke-linecap="round"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
              <select
                v-model="selectedDeviceId"
                @change="restartStream"
                class="bg-transparent text-xs text-white/90 outline-none cursor-pointer max-w-[180px] truncate"
              >
                <option
                  v-for="d in devices"
                  :key="d.deviceId"
                  :value="d.deviceId"
                  class="bg-ink-800 text-white"
                >
                  {{ d.label || `摄像头 ${devices.indexOf(d) + 1}` }}
                </option>
              </select>
            </div>

            <!-- 镜像切换 -->
            <button
              v-if="!captured && stream"
              @click="mirrored = !mirrored"
              class="px-2.5 py-1.5 rounded-lg border bg-ink-800/80 backdrop-blur text-xs transition-all active:scale-95 flex items-center gap-1.5"
              :class="mirrored
                ? 'border-accent/50 text-accent'
                : 'border-ink-600 text-ink-400 hover:text-white'"
              title="左右镜像（不影响最终拍照画面）"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 3v18M5 8l-2 4 2 4M19 8l2 4-2 4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              镜像
            </button>

            <button
              @click="handleClose"
              class="w-8 h-8 rounded-lg border border-ink-600 bg-ink-800/80 backdrop-blur flex items-center justify-center text-ink-400 hover:text-white hover:bg-ink-700 transition-all active:scale-90"
              aria-label="关闭"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M6 18L18 6" stroke-linecap="round" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 主画面区（固定 3:4 取景框，所见即所得） -->
        <div class="relative flex items-center justify-center rounded-2xl overflow-hidden border border-ink-700 bg-ink-800 shadow-card-hover aspect-[3/4] w-full">
          <!-- 1. 已拍摄：展示快照 -->
          <img
            v-if="captured"
            :src="captured"
            alt="拍照预览"
            class="w-full h-full object-cover"
          />

          <!-- 2. 未拍摄 + 流就绪：展示视频（cover 裁切 = 输出裁切） -->
          <video
            v-show="!captured && stream && !error"
            ref="videoRef"
            autoplay
            playsinline
            muted
            class="w-full h-full object-cover"
            :class="{ 'scale-x-[-1]': mirrored }"
          />

          <!-- 3. 加载中 -->
          <div
            v-if="!captured && !stream && !error"
            class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-6"
          >
            <div class="w-10 h-10 rounded-xl border border-accent/40 bg-accent/10 flex items-center justify-center">
              <svg class="w-5 h-5 animate-spin text-accent" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
              </svg>
            </div>
            <p class="text-sm font-medium text-white/90">正在打开摄像头…</p>
            <p class="text-[11px] text-ink-400">如系统弹出权限请求，请点击允许</p>
          </div>

          <!-- 4. 错误 -->
          <div
            v-if="error"
            class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center px-8"
          >
            <div class="w-12 h-12 rounded-xl border border-red-500/40 bg-red-500/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" stroke-linecap="round" />
              </svg>
            </div>
            <p class="text-sm font-medium text-white/90">无法访问摄像头</p>
            <p class="text-[12px] text-ink-400 leading-relaxed max-w-md whitespace-pre-line">{{ error }}</p>
            <button
              @click="initCamera"
              class="mt-2 px-4 py-1.5 rounded-lg border border-ink-600 bg-ink-700/60 text-xs text-white/90 hover:bg-ink-700 transition-all active:scale-95"
            >
              重试
            </button>
          </div>

          <!-- 取景辅助层（拍照前） -->
          <div
            v-if="!captured && stream && !error"
            class="absolute inset-0 pointer-events-none"
          >
            <!-- 三分线 -->
            <div class="absolute left-1/3 top-0 bottom-0 w-px bg-white/8" />
            <div class="absolute left-2/3 top-0 bottom-0 w-px bg-white/8" />
            <div class="absolute top-1/3 left-0 right-0 h-px bg-white/8" />
            <div class="absolute top-2/3 left-0 right-0 h-px bg-white/8" />

            <!-- 人形剪影引导 -->
            <svg
              class="absolute inset-0 w-full h-full text-accent/25"
              viewBox="0 0 300 400"
              preserveAspectRatio="xMidYMid meet"
              fill="none"
              stroke="currentColor"
              stroke-width="1.4"
              stroke-dasharray="4 4"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <!-- 头 -->
              <circle cx="150" cy="80" r="30" />
              <!-- 颈 + 肩 -->
              <path d="M150 110 L150 130 M100 165 Q150 140 200 165" />
              <!-- 上身躯干 -->
              <path d="M100 165 L95 270 M200 165 L205 270" />
              <!-- 手臂 -->
              <path d="M100 165 L75 260 M200 165 L225 260" />
              <!-- 下身 -->
              <path d="M95 270 L90 390 M205 270 L210 390 M150 270 L150 390" />
            </svg>

            <!-- 角标 -->
            <div class="absolute top-3 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-md bg-ink-900/60 backdrop-blur text-[10px] text-white/70 border border-white/10">
              将人物对准框内 · 自动裁切为 3:4
            </div>
          </div>

          <!-- 倒计时大数字 -->
          <transition name="count">
            <div
              v-if="countdown !== null"
              class="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
              <div class="absolute inset-0 bg-ink-950/30 backdrop-blur-[2px]" />
              <div
                :key="countdown"
                class="relative font-display font-bold text-accent count-number"
                style="font-size: clamp(120px, 28vh, 280px); line-height: 1;
                       text-shadow: 0 0 60px rgba(200,255,61,0.6), 0 0 120px rgba(200,255,61,0.3);"
              >
                {{ countdown }}
              </div>
            </div>
          </transition>
        </div>

        <!-- 底部控制条 -->
        <div class="mt-4 flex flex-col items-center gap-3">
          <!-- 延时选择（拍照前 + 非倒计时中显示） -->
          <div
            v-if="!captured && stream && !error && countdown === null"
            class="inline-flex items-center gap-1 p-1 rounded-xl border border-ink-600 bg-ink-800/70 backdrop-blur"
          >
            <span class="flex items-center gap-1 px-2.5 text-[11px] text-ink-400">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="13" r="8" />
                <path d="M12 9v4l2 2M9 2h6" stroke-linecap="round" />
              </svg>
              延时
            </span>
            <button
              v-for="opt in DELAY_OPTIONS"
              :key="opt.value"
              @click="delaySeconds = opt.value"
              class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all active:scale-95"
              :class="delaySeconds === opt.value
                ? 'bg-accent text-ink-900 shadow-accent-glow'
                : 'text-ink-300 hover:text-white hover:bg-ink-700/60'"
            >{{ opt.label }}</button>
          </div>

          <div class="flex items-center justify-center gap-3">
            <!-- 拍照前 -->
            <template v-if="!captured">
              <button
                v-if="countdown === null"
                @click="handleClose"
                class="px-5 py-2.5 rounded-xl border border-ink-600 bg-ink-800/70 text-sm text-ink-300 hover:text-white hover:bg-ink-700 transition-all active:scale-95"
              >
                取消
              </button>

              <!-- 主按钮：倒计时未激活时是「拍照」，激活时是「取消倒计时」 -->
              <button
                v-if="countdown === null"
                @click="startCapture"
                :disabled="!stream || !!error"
                class="group relative inline-flex items-center gap-2 px-7 py-3 rounded-2xl font-display font-semibold text-sm transition-all duration-300 will-change-transform"
                :class="stream && !error
                  ? 'bg-accent text-ink-900 hover:bg-accent-soft shadow-accent-glow hover:scale-[1.03] active:scale-[0.97]'
                  : 'bg-ink-700/70 text-ink-500 cursor-not-allowed border border-ink-600/60'"
              >
                <span
                  v-if="stream && !error"
                  class="absolute inset-0 rounded-2xl blur-xl opacity-50 bg-accent -z-10 transition-opacity group-hover:opacity-75"
                />
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" stroke-linejoin="round" stroke-linecap="round"/>
                  <circle cx="12" cy="13" r="4"/>
                </svg>
                {{ delaySeconds > 0 ? `${delaySeconds} 秒后拍照` : '拍照' }}
              </button>

              <button
                v-else
                @click="cancelCountdown"
                class="inline-flex items-center gap-2 px-7 py-3 rounded-2xl font-display font-semibold text-sm border-2 border-accent/70 bg-ink-800/80 backdrop-blur text-white hover:bg-ink-700 transition-all active:scale-95"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
                  <path d="M6 6l12 12M6 18L18 6" stroke-linecap="round" />
                </svg>
                取消倒计时
              </button>
            </template>

          <!-- 拍照后 -->
          <template v-else>
            <button
              @click="retake"
              class="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl border border-ink-600 bg-ink-800/70 text-sm text-ink-300 hover:text-white hover:bg-ink-700 transition-all active:scale-95"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 0115-6.7L21 8M21 3v5h-5M21 12a9 9 0 01-15 6.7L3 16M3 21v-5h5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              重拍
            </button>
            <button
              @click="confirm"
              class="group relative inline-flex items-center gap-2 px-7 py-3 rounded-2xl font-display font-semibold text-sm bg-accent text-ink-900 hover:bg-accent-soft shadow-accent-glow transition-all hover:scale-[1.03] active:scale-[0.97]"
            >
              <span class="absolute inset-0 rounded-2xl blur-xl opacity-50 bg-accent -z-10 transition-opacity group-hover:opacity-75" />
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
                <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              使用这张
            </button>
          </template>
          </div>
        </div>

        <!-- 隐藏的 canvas 用于绘制帧 -->
        <canvas ref="canvasRef" class="hidden" />
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'capture'])

const videoRef  = ref(null)
const canvasRef = ref(null)

const stream           = ref(null)
const devices          = ref([])
const selectedDeviceId = ref('')
const error            = ref('')
const captured         = ref(null)   // dataURL 字符串，用于预览
let   capturedBlob     = null        // Blob，用于生成 File
const mirrored         = ref(true)   // 默认镜像（更符合"照镜子"直觉）

/* ── 延时拍照 ──────────────────────────────────────────── */
const DELAY_OPTIONS = [
  { value: 0,  label: '即拍'  },
  { value: 3,  label: '3 秒' },
  { value: 5,  label: '5 秒' },
  { value: 10, label: '10 秒' },
]
const delaySeconds = ref(0)           // 用户选的延时秒数
const countdown    = ref(null)        // null=未在倒计时；数字=还剩多少秒
let   countdownTimer = null

/* ── 启动摄像头 ────────────────────────────────────────── */
async function initCamera() {
  error.value = ''
  stopStream()

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    error.value = '当前浏览器不支持调用摄像头。\n请使用最新版 Chrome / Edge / Safari，并确保使用 https 或 localhost 访问。'
    return
  }

  try {
    // 优先请求更高纵向分辨率，便于中心 3:4 裁切后仍 ≥ 768×1024
    const videoConstraints = {
      width:  { ideal: 1920 },
      height: { ideal: 1440 },
      aspectRatio: { ideal: 4 / 3 },
    }
    if (selectedDeviceId.value) {
      videoConstraints.deviceId = { exact: selectedDeviceId.value }
    } else {
      videoConstraints.facingMode = 'user'
    }
    const constraints = { video: videoConstraints, audio: false }
    const s = await navigator.mediaDevices.getUserMedia(constraints)
    stream.value = s
    await nextFrame()
    if (videoRef.value) {
      videoRef.value.srcObject = s
      try { await videoRef.value.play() } catch (_) { /* 自动播放静默失败可忽略 */ }
    }
    await refreshDevices()
  } catch (e) {
    handleMediaError(e)
  }
}

async function refreshDevices() {
  try {
    const list = await navigator.mediaDevices.enumerateDevices()
    devices.value = list.filter(d => d.kind === 'videoinput')
    if (!selectedDeviceId.value && stream.value) {
      const track = stream.value.getVideoTracks()[0]
      const id = track?.getSettings?.().deviceId
      if (id) selectedDeviceId.value = id
    }
  } catch (e) {
    console.warn('enumerateDevices failed', e)
  }
}

async function restartStream() {
  cancelCountdown()
  await initCamera()
}

function handleMediaError(e) {
  const name = e?.name || ''
  if (name === 'NotAllowedError' || name === 'SecurityError') {
    error.value = '摄像头权限被拒绝。\n请在浏览器地址栏左侧解锁摄像头权限，或在 macOS "系统设置 → 隐私与安全性 → 摄像头" 中允许浏览器访问。'
  } else if (name === 'NotFoundError' || name === 'OverconstrainedError') {
    error.value = '未检测到可用的摄像头设备。\n请确认 USB 摄像头已正确连接。'
  } else if (name === 'NotReadableError') {
    error.value = '摄像头被其他程序占用。\n请关闭可能正在使用摄像头的应用（如 FaceTime / Zoom / 飞书）后重试。'
  } else {
    error.value = `摄像头初始化失败：${e?.message || name || '未知错误'}`
  }
}

function stopStream() {
  if (stream.value) {
    stream.value.getTracks().forEach(t => t.stop())
    stream.value = null
  }
  if (videoRef.value) videoRef.value.srcObject = null
}

function nextFrame() {
  return new Promise(resolve => requestAnimationFrame(() => resolve()))
}

/* ── 拍照 / 重拍 / 确认 ────────────────────────────────── */
// OOTDiffusion 标准输入尺寸：768(宽) × 1024(高)，即 3:4 竖向
const OUTPUT_W = 768
const OUTPUT_H = 1024
const TARGET_RATIO = OUTPUT_W / OUTPUT_H   // = 0.75

// 入口：根据延时设定决定是立即拍还是先倒计时
function startCapture() {
  if (!stream.value || error.value) return
  if (delaySeconds.value <= 0) {
    capture()
    return
  }
  countdown.value = delaySeconds.value
  clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    if (countdown.value === null) {
      clearInterval(countdownTimer)
      countdownTimer = null
      return
    }
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
      countdown.value = null
      capture()
    }
  }, 1000)
}

function cancelCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = null
}

function capture() {
  const video = videoRef.value
  const canvas = canvasRef.value
  if (!video || !canvas || !stream.value) return

  const vw = video.videoWidth  || 1280
  const vh = video.videoHeight || 960

  // 在源视频帧中央按 3:4 取一块矩形（与预览的 object-cover 完全一致）
  let sx, sy, sw, sh
  const videoRatio = vw / vh
  if (videoRatio > TARGET_RATIO) {
    // 视频更宽（横屏摄像头常见）→ 裁掉左右
    sh = vh
    sw = vh * TARGET_RATIO
    sx = (vw - sw) / 2
    sy = 0
  } else {
    // 视频更窄 → 裁掉上下
    sw = vw
    sh = vw / TARGET_RATIO
    sx = 0
    sy = (vh - sh) / 2
  }

  canvas.width  = OUTPUT_W
  canvas.height = OUTPUT_H

  const ctx = canvas.getContext('2d')
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  // 注意：mirrored 仅用于预览取景，最终拍出的图保持原始方向（不镜像），
  // 这样上传给 OOTDiffusion 的人体姿态不会被左右翻转。
  ctx.drawImage(video, sx, sy, sw, sh, 0, 0, OUTPUT_W, OUTPUT_H)

  captured.value = canvas.toDataURL('image/jpeg', 0.92)
  canvas.toBlob(
    (blob) => { capturedBlob = blob },
    'image/jpeg',
    0.92,
  )
}

function retake() {
  cancelCountdown()
  captured.value = null
  capturedBlob = null
}

function confirm() {
  if (!capturedBlob) {
    // 兜底：从 dataURL 转 Blob
    if (!captured.value) return
    const file = dataURLtoFile(captured.value, fileName())
    emit('capture', file)
    handleClose()
    return
  }
  const file = new File([capturedBlob], fileName(), { type: 'image/jpeg' })
  emit('capture', file)
  handleClose()
}

function fileName() {
  const ts = new Date().toISOString().replace(/[:.]/g, '-')
  return `camera-${ts}.jpg`
}

function dataURLtoFile(dataUrl, name) {
  const arr = dataUrl.split(',')
  const mime = arr[0].match(/:(.*?);/)[1]
  const bstr = atob(arr[1])
  const u8 = new Uint8Array(bstr.length)
  for (let i = 0; i < bstr.length; i++) u8[i] = bstr.charCodeAt(i)
  return new File([u8], name, { type: mime })
}

/* ── 关闭 ──────────────────────────────────────────────── */
function handleClose() {
  cancelCountdown()
  stopStream()
  captured.value = null
  capturedBlob = null
  error.value = ''
  emit('close')
}

/* ── 键盘 & open 监听 ──────────────────────────────────── */
function onKey(e) {
  if (!props.open) return
  if (e.key === 'Escape') {
    // 倒计时中按 Esc 优先取消倒计时，不关闭弹窗
    if (countdown.value !== null) {
      e.preventDefault()
      cancelCountdown()
      return
    }
    handleClose()
  } else if (e.key === ' ' || e.key === 'Enter') {
    if (!captured.value && stream.value && !error.value && countdown.value === null) {
      e.preventDefault()
      startCapture()
    }
  }
}

watch(() => props.open, async (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
  if (v) {
    document.addEventListener('keydown', onKey)
    await initCamera()
  } else {
    document.removeEventListener('keydown', onKey)
    stopStream()
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  cancelCountdown()
  stopStream()
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
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.25s;
}
.modal-enter-from > div:last-child {
  transform: scale(0.95) translateY(16px);
  opacity: 0;
}
.modal-leave-to > div:last-child {
  transform: scale(0.98) translateY(8px);
  opacity: 0;
}

/* 倒计时数字跳动动画：每个新数字 0 → 1，先放大再回到 1 */
.count-number {
  animation: count-pop 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes count-pop {
  0%   { transform: scale(0.4); opacity: 0; }
  30%  { transform: scale(1.15); opacity: 1; }
  60%  { transform: scale(1.00); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.85; }
}

/* 倒计时层的进出过渡 */
.count-enter-active, .count-leave-active { transition: opacity 0.25s ease; }
.count-enter-from, .count-leave-to       { opacity: 0; }
</style>
