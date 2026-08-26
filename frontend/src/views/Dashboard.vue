<template>
  <div class="dashboard-view">
    <div class="page-header">
      <div class="header-left">
        <h2>📊 设备实时监控面板</h2>
        <el-tag :type="isConnected ? 'success' : 'danger'" size="small">
          {{ isConnected ? '已连接' : '离线' }}
        </el-tag>
      </div>
      <div class="header-right">
        <span>⏱ 上次刷新：{{ lastUpdateTime || '--' }} <span class="refresh-interval">｜每 3 秒自动刷新</span></span>
        <el-button size="small" :loading="isLoading" @click="refreshData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div v-if="isLoading && devices.length === 0" class="loading-skeleton">
      <el-skeleton :rows="6" animated />
    </div>

    <el-alert
      v-else-if="!isConnected"
      title="⚠️ 未能获取任何设备遥测数据，请检查后端服务是否正常运行"
      type="error"
      show-icon
      :closable="false"
      class="offline-alert"
    />

    <el-row v-else :gutter="20" class="device-grid">
      <el-col v-for="device in devices" :key="device.deviceId" :xs="24" :sm="12" :lg="8">
        <DeviceCard
          :device-id="device.deviceId"
          :device-name="device.deviceName"
          :device-status="device.deviceStatus"
          :metrics="device.metrics"
          :update-time="lastUpdateTime"
        />
      </el-col>
    </el-row>

    <el-empty v-if="!isLoading && isConnected && devices.length === 0" description="暂无设备数据" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import DeviceCard from '@/components/DeviceCard.vue'
import { getMultipleDevicesTelemetry } from '@/api/telemetry'

const DEVICE_CONFIG = [
  { id: 'boiler_002', name: '2号锅炉' },
  { id: 'turbine_003', name: '3号汽轮机' },
  { id: 'generator_004', name: '4号发电机' }
]

const devices = ref([])
const isLoading = ref(false)
const isConnected = ref(false)
const lastUpdateTime = ref('')
let refreshTimer = null

const processDeviceData = (config, response) => {
  const data = response?.data || {}
  return {
    deviceId: config.id,
    deviceName: config.name,
    deviceStatus: data.device_status?.status || (response?.success ? 'unknown' : 'error'),
    metrics: (data.metrics || []).map(metric => ({ ...metric, level: metric.level || 'unknown' }))
  }
}

const isValidDeviceResponse = response => {
  const status = response?.data?.device_status?.status
  return response?.success === true && !['error', 'unknown'].includes(status)
}

const fetchAllDevices = async () => {
  if (isLoading.value) return
  isLoading.value = true

  try {
    const results = await getMultipleDevicesTelemetry(DEVICE_CONFIG.map(device => device.id))
    devices.value = results.map((response, index) => processDeviceData(DEVICE_CONFIG[index], response))
    // allSettled 会把单设备请求失败包装为结果，因此不能仅以 await 成功判断连接状态。
    isConnected.value = results.some(isValidDeviceResponse)
    if (isConnected.value) {
      lastUpdateTime.value = new Date().toLocaleTimeString()
    }
  } catch (error) {
    console.error('获取监控数据失败:', error)
    isConnected.value = false
    devices.value = []
  } finally {
    isLoading.value = false
  }
}

const refreshData = () => fetchAllDevices()

const startPolling = () => {
  refreshTimer = window.setInterval(fetchAllDevices, 3000)
}

onMounted(async () => {
  await fetchAllDevices()
  startPolling()
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.dashboard-view { max-width: 1400px; margin: 0 auto; padding: 20px; }
.page-header, .header-left, .header-right { display: flex; align-items: center; }
.page-header { justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 24px; }
.header-left { gap: 12px; }
.header-left h2 { margin: 0; color: #333; font-size: 20px; font-weight: 600; }
.header-right { gap: 16px; color: #999; font-size: 13px; }
.refresh-interval { color: #bfbfbf; }
.loading-skeleton { padding: 20px; border-radius: 8px; background: #fff; }
.offline-alert { margin-bottom: 20px; }
.device-grid { margin-top: 8px; }
</style>