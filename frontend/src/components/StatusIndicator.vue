<template>
  <span class="status-indicator" :class="level">
    <span class="dot"></span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: {
    type: String,
    default: 'normal',
    validator: (val) => ['normal', 'warn', 'danger'].includes(val)
  }
})

const label = computed(() => {
  const map = {
    normal: '正常',
    warn: '预警',
    danger: '异常'
  }
  return map[props.level] || '正常'
})
</script>

<style scoped>
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 12px;
}

.status-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-indicator.normal {
  color: #52c41a;
}
.status-indicator.normal .dot {
  background: #52c41a;
}

.status-indicator.warn {
  color: #faad14;
}
.status-indicator.warn .dot {
  background: #faad14;
}

.status-indicator.danger {
  color: #f5222d;
}
.status-indicator.danger .dot {
  background: #f5222d;
}
</style>