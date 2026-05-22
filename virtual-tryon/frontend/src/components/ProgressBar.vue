<!--
  ProgressBar.vue
  细长的科技感进度条，渐变 + shimmer + 百分比文字
-->
<template>
  <div class="w-full">
    <div class="flex items-center justify-between mb-2 px-0.5">
      <div class="flex items-center gap-2">
        <span class="relative flex h-2 w-2">
          <span class="absolute inset-0 rounded-full bg-accent opacity-60 animate-ping" />
          <span class="relative inline-flex rounded-full h-2 w-2 bg-accent" />
        </span>
        <span class="text-xs text-white/85 font-medium tracking-wide">
          {{ label }}
        </span>
      </div>
      <span class="text-xs font-mono font-semibold text-accent tabular-nums">
        {{ Math.round(progress) }}%
      </span>
    </div>

    <div class="relative h-1.5 rounded-full overflow-hidden bg-ink-700/70 border border-ink-600/60">
      <!-- 进度填充 -->
      <div
        class="absolute inset-y-0 left-0 rounded-full progress-gradient transition-[width] duration-500 ease-out shadow-[0_0_14px_rgba(200,255,61,0.45)]"
        :style="{ width: progress + '%' }"
      />
      <!-- 末端光点 -->
      <div
        v-if="progress > 0 && progress < 100"
        class="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white shadow-[0_0_8px_rgba(255,255,255,0.9)] transition-[left] duration-500 ease-out"
        :style="{ left: `calc(${progress}% - 4px)` }"
      />
    </div>

    <p v-if="subtitle" class="mt-2 text-[11px] text-ink-400 text-center">
      {{ subtitle }}
    </p>
  </div>
</template>

<script setup>
defineProps({
  progress: { type: Number, default: 0 },
  label:    { type: String, default: '正在生成，请稍候…' },
  subtitle: { type: String, default: '' },
})
</script>
