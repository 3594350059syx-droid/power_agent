<template>
  <div class="param-gauge">
    <div class="param-header">
      <span class="param-name">{{ name }}</span>
      <StatusIndicator :level="level" />
    </div>
    <div class="param-value">
      <span class="value">{{ value !== undefined ? value : '--' }}</span>
      <span class="unit">{{ unit }}</span>
    </div>
    <div class="param-bar">
      <div class="bar-track">
        <div
          class="bar-fill"
          :class="level"
          :style="{ width: barWidth }"
        ></div>
      </div>
      <div class="bar-labels">
        <span class="bar-min">{{ min !== undefined ? min : '--' }}</span>
        <span class="bar-max">{{ max !== undefined ? max : '--' }}</span>
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
  level: { type: String, default: 'normal' },
  min: { type: Number, default: undefined },
  max: { type: Number, default: undefined }
})

const barWidth = computed(() => {
  if (props.value === undefined || props.min === undefined || props.max === undefined) {
    return '0%'
  }
  const range = props.max - props.min
  if (range === 0) return '50%'
  const pct = ((props.value - props.min) / range) * 100
  return `${Math.min(Math.max(pct, 0), 100)}%`
})
</script>

<style scoped>
.param-gauge {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.param-gauge:last-child {
  border-bottom: none;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.param-name {
  font-size: 13px;
  color: #666;
}

.param-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}

.param-value .value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.param-value .unit {
  font-size: 13px;
  color: #999;
}

/* 进度条 */
.param-bar {
  margin-top: 2px;
}

.bar-track {
  width: 100%;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}

.bar-fill.normal {
  background: #52c41a;
}

.bar-fill.warn {
  background: #faad14;
}

.bar-fill.danger {
  background: #f5222d;
}

.bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #bbb;
  margin-top: 1px;
}
</style>