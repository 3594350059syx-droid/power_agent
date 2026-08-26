<template>
  <span class="status-indicator" :class="normalizedLevel">
    <span class="dot"></span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: {
    type: String,
    default: 'unknown'
  }
})

const normalizedLevel = computed(() => {
  const aliases = {
    warning: 'warn',
    error: 'danger',
    stopped: 'danger'
  }
  const level = props.level?.toLowerCase()
  return aliases[level] || (['normal', 'warn', 'danger', 'unknown'].includes(level) ? level : 'unknown')
})

const label = computed(() => ({
  normal: '正常',
  warn: '预警',
  danger: '异常',
  unknown: '未知'
}[normalizedLevel.value]))
</script>

<style scoped>
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.normal { color: #52c41a; }
.normal .dot { background: #52c41a; }
.warn { color: #faad14; }
.warn .dot { background: #faad14; }
.danger { color: #f5222d; }
.danger .dot { background: #f5222d; }
.unknown { color: #909399; }
.unknown .dot { background: #909399; }
</style>