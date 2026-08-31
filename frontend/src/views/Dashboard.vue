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
        <span>⏱ 上次刷新：{{ lastUpdateTime || '--' }} <span class="refresh-interval">｜WebSocket 实时推送，断线自动轮询</span></span>
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
let heartbeatTimer = null
const reconnectTimers = new Map()
const sockets = new Map()
const activeSocketCount = ref(0)
const isUnmounted = ref(false)
const useMock = import.meta.env.VITE_USE_MOCK === 'true'

const websocketBaseUrl = () => {
  const configured = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  if (/^https?:\/\//i.test(configured)) {
    const url = new URL(configured)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return url.toString().replace(/\/$/, '')
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${configured.replace(/\/$/, '')}`
}

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

const processSnapshot = (event, config) => {
  const response = { success: true, data: event?.data || {} }
  const nextDevice = processDeviceData(config, response)
  const index = devices.value.findIndex(device => device.deviceId === config.id)
  if (index === -1) {
    devices.value = [...devices.value, nextDevice]
  } else {
    devices.value[index] = nextDevice
  }
  isConnected.value = devices.value.some(device => !['error', 'unknown'].includes(device.deviceStatus))
  lastUpdateTime.value = new Date().toLocaleTimeString()
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
  if (refreshTimer || isUnmounted.value) return
  refreshTimer = window.setInterval(fetchAllDevices, 3000)
}

const stopPolling = () => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const scheduleReconnect = config => {
  if (isUnmounted.value || reconnectTimers.has(config.id)) return
  reconnectTimers.set(config.id, window.setTimeout(() => {
    reconnectTimers.delete(config.id)
    connectDevice(config)
  }, 5000))
}

const connectDevice = config => {
  if (isUnmounted.value || useMock || sockets.has(config.id)) return

  let socket
  try {
    const url = `${websocketBaseUrl()}/ws/telemetry/${encodeURIComponent(config.id)}`
    socket = new WebSocket(url)
  } catch (error) {
    console.warn('创建遥测 WebSocket 失败，降级为轮询:', error)
    startPolling()
    scheduleReconnect(config)
    return
  }
  let countedAsOpen = false
  sockets.set(config.id, socket)

  socket.onopen = () => {
    countedAsOpen = true
    activeSocketCount.value += 1
    if (activeSocketCount.value === DEVICE_CONFIG.length) stopPolling()
  }

  socket.onmessage = message => {
    try {
      const event = JSON.parse(message.data)
      if (event.type === 'pong' || event.event === 'heartbeat') return
      if (event.type === 'telemetry' && event.event === 'telemetry_snapshot') {
        processSnapshot(event, config)
      }
    } catch (error) {
      console.warn('解析遥测 WebSocket 消息失败:', error)
    }
  }

  socket.onerror = () => {
    // onclose 负责清理和进入轮询降级，避免同一断线重复处理。
    socket.close()
  }

  socket.onclose = () => {
    if (sockets.get(config.id) === socket) sockets.delete(config.id)
    if (countedAsOpen && activeSocketCount.value > 0) {
      activeSocketCount.value -= 1
    }
    startPolling()
    scheduleReconnect(config)
  }
}

const startRealtime = () => {
  if (useMock) {
    startPolling()
    return
  }

  DEVICE_CONFIG.forEach(connectDevice)
  heartbeatTimer = window.setInterval(() => {
    sockets.forEach(socket => {
      if (socket.readyState === WebSocket.OPEN) socket.send('ping')
    })
  }, 10000)
}

onMounted(async () => {
  await fetchAllDevices()
  startRealtime()
})

onBeforeUnmount(() => {
  isUnmounted.value = true
  if (heartbeatTimer) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
  reconnectTimers.forEach(timer => window.clearTimeout(timer))
  reconnectTimers.clear()
  sockets.forEach(socket => socket.close())
  sockets.clear()
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