<template>
  <el-card class="device-card" shadow="hover">
    <div class="device-header">
      <div class="device-title">
        <span class="device-icon">⚙️</span>
        <span class="device-name">{{ deviceName || `设备 ${deviceId}` }}</span>
      </div>
      <el-tag :type="statusTagType" size="small">{{ statusLabel }}</el-tag>
    </div>

    <div class="device-body">
      <ParamGauge
        v-for="metric in metrics"
        :key="metric.key"
        :name="metric.name"
        :value="metric.value"
        :unit="metric.unit"
        :level="metric.level || 'unknown'"
        :min="metric.normal_range?.[0]"
        :max="metric.normal_range?.[1]"
      />
      <el-empty v-if="metrics.length === 0" :image-size="54" :description="emptyDescription" />
    </div>

    <div class="device-footer">
      <span>ID: {{ deviceId }}</span>
      <span>{{ updateTime || '--' }}</span>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import ParamGauge from './ParamGauge.vue'

const props = defineProps({
  deviceId: { type: String, required: true },
  deviceName: { type: String, default: '' },
  deviceStatus: { type: String, default: 'unknown' },
  metrics: { type: Array, default: () => [] },
  updateTime: { type: String, default: '' }
})

const normalizedStatus = computed(() => props.deviceStatus?.toLowerCase() || 'unknown')

const statusTagType = computed(() => ({
  running: 'success',
  warning: 'warning',
  warn: 'warning',
  stopped: 'danger',
  error: 'danger',
  unknown: 'info'
}[normalizedStatus.value] || 'info'))

const statusLabel = computed(() => ({
  running: '运行中',
  warning: '预警',
  warn: '预警',
  stopped: '已停止',
  error: '连接失败',
  unknown: '未知设备'
}[normalizedStatus.value] || '未知状态'))

const emptyDescription = computed(() => (
  normalizedStatus.value === 'error' ? '无法获取设备遥测数据' : '暂无遥测数据'
))
</script>

<style scoped>
.device-card { height: 100%; border-radius: 12px; }
.device-card :deep(.el-card__body) { display: flex; flex-direction: column; height: 100%; padding: 16px 20px; }
.device-header, .device-title, .device-footer { display: flex; align-items: center; }
.device-header { justify-content: space-between; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 2px solid #f5f5f5; }
.device-title { gap: 8px; }
.device-icon { font-size: 20px; }
.device-name { color: #333; font-size: 16px; font-weight: 600; }
.device-body { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.device-footer { justify-content: space-between; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f0f0f0; color: #bbb; font-size: 11px; }
</style>