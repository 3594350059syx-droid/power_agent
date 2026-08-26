<template>
  <div class="param-gauge">
    <div class="param-header">
      <span class="param-name">{{ name }}</span>
      <StatusIndicator :level="level" />
    </div>
    <div class="param-value">
      <span class="value">{{ value ?? '--' }}</span>
      <span class="unit">{{ unit }}</span>
    </div>
    <div class="param-bar">
      <div class="bar-track">
        <div class="bar-fill" :class="normalizedLevel" :style="{ width: barWidth }"></div>
      </div>
      <div class="bar-labels">
        <span>{{ min ?? '--' }}</span>
        <span>{{ max ?? '--' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StatusIndicator from './StatusIndicator.vue'

const props = defineProps({
  name: { type: String, required: true },
  value: { type: Number, default: undefined },
  unit: { type: String, default: '' },
  level: { type: String, default: 'unknown' },
  min: { type: Number, default: undefined },
  max: { type: Number, default: undefined }
})

const normalizedLevel = computed(() => {
  const aliases = { warning: 'warn', error: 'danger', stopped: 'danger' }
  return aliases[props.level] || props.level || 'unknown'
})

const barWidth = computed(() => {
  if (props.value === undefined || props.min === undefined || props.max === undefined) {
    return '0%'
  }

  const range = props.max - props.min
  if (range <= 0) return '50%'
  const percentage = ((props.value - props.min) / range) * 100
  return `${Math.min(Math.max(percentage, 0), 100)}%`
})
</script>

<style scoped>
.param-gauge {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}
.param-gauge:last-child { border-bottom: none; }
.param-header, .param-value, .bar-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.param-header { margin-bottom: 4px; }
.param-name { font-size: 13px; color: #666; }
.param-value { justify-content: flex-start; gap: 4px; margin-bottom: 4px; }
.value { font-size: 20px; font-weight: 600; color: #333; }
.unit { font-size: 13px; color: #999; }
.bar-track { height: 4px; overflow: hidden; border-radius: 2px; background: #f0f0f0; }
.bar-fill { height: 100%; border-radius: 2px; transition: width .6s ease; }
.bar-fill.normal { background: #52c41a; }
.bar-fill.warn { background: #faad14; }
.bar-fill.danger { background: #f5222d; }
.bar-fill.unknown { background: #909399; }
.bar-labels { margin-top: 1px; font-size: 10px; color: #bbb; }
</style>