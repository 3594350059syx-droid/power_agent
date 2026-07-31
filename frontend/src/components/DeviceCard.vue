<template>
  <el-card class="device-card" shadow="hover">
    <div class="device-header">
      <div class="device-title">
        <span class="device-icon">⚙️</span>
        <span class="device-name">{{ deviceName || `设备 ${deviceId}` }}</span>
      </div>
      <el-tag :type="statusTagType" size="small">
        {{ deviceStatus || '运行中' }}
      </el-tag>
    </div>

    <div class="device-body">
      <ParamGauge
        v-for="metric in metrics"
        :key="metric.key"
        :name="metric.name"
        :value="metric.value"
        :unit="metric.unit"
        :level="metric.level || 'normal'"
        :min="metric.normal_range ? metric.normal_range[0] : undefined"
        :max="metric.normal_range ? metric.normal_range[1] : undefined"
      />
    </div>

    <div class="device-footer">
      <span class="device-id">ID: {{ deviceId }}</span>
      <span class="update-time">{{ updateTime }}</span>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import ParamGauge from './ParamGauge.vue'

const props = defineProps({
  deviceId: { type: String, required: true },
  deviceName: { type: String, default: '' },
  deviceStatus: { type: String, default: '运行中' },
  metrics: {
    type: Array,
    default: () => []
  },
  updateTime: { type: String, default: '' }
})

const statusTagType = computed(() => {
  const map = {
    running: 'success',
    stopped: 'danger',
    warning: 'warning'
  }
  return map[props.deviceStatus?.toLowerCase()] || 'success'
})
</script>

<style scoped>
.device-card {
  height: 100%;
  border-radius: 12px;
}

.device-card :deep(.el-card__body) {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f5f5f5;
}

.device-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-icon {
  font-size: 20px;
}

.device-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.device-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  font-size: 11px;
  color: #bbb;
}
</style>